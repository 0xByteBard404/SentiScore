#!/usr/bin/env python3
"""
SentiScore 后端服务主入口
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import sqlite3

# 在导入任何其他模块之前设置HF_HOME环境变量
from config import config
os.environ['HF_HOME'] = config.HF_CACHE_DIR
os.environ['HF_ENDPOINT'] = config.HF_ENDPOINT

# 标准库
import os
import sys
import time
import torch
import logging
import warnings
import threading
import gc
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
models_path = os.path.join(project_root, '..', 'models')
# 规范化路径，移除 .. 部分
models_path = os.path.normpath(models_path)

# 设置ModelScope缓存目录
MODELSCOPE_CACHE_DIR = os.getenv('MODELSCOPE_CACHE_DIR', os.path.join(models_path, 'modelscope_cache'))
# 规范化ModelScope缓存目录路径
MODELSCOPE_CACHE_DIR = os.path.normpath(MODELSCOPE_CACHE_DIR)
os.environ['MODELSCOPE_CACHE_HOME'] = MODELSCOPE_CACHE_DIR
os.environ['MODELSCOPE_CACHE_DIR'] = MODELSCOPE_CACHE_DIR

# 设置HanLP环境变量（提前设置，确保在hanlp导入前生效）
HANLP_MODEL_DIR = os.getenv('HANLP_MODEL_DIR', os.path.join(models_path, 'hanlp_models'))
os.environ['HANLP_HOME'] = HANLP_MODEL_DIR

# 本地配置导入
from config import config

# 设置HanLP环境变量（在导入任何使用HanLP的模块之前）
if hasattr(config, 'HANLP_MODEL_DIR') and config.HANLP_MODEL_DIR:
    os.environ['HANLP_HOME'] = config.HANLP_MODEL_DIR

# 工具函数
from src.utils.helpers import setup_logging, EmotionAnalysisError
from src.core.cemotion import Cemotion
from src.core.segmentor import TextSegmentor
from src.api.routes import register_routes
from src.api.auth_routes import auth_bp
from src.database.manager import DatabaseManager

# 配置日志
logger = setup_logging()

# 全局忽略警告
warnings.simplefilter(action='ignore', category=UserWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)

# 设置transformers的日志级别
try:
    from transformers import logging as transformers_logging
    transformers_logging.set_verbosity_error()
except ImportError:
    pass

# 配置Hugging Face环境
os.environ['HF_HOME'] = config.HF_CACHE_DIR
os.environ['HF_ENDPOINT'] = config.HF_ENDPOINT  # 使用国内镜像
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'  # 禁用进度条，避免影响日志

# 创建Hugging Face缓存目录
if not os.path.exists(config.HF_CACHE_DIR):
    os.makedirs(config.HF_CACHE_DIR, exist_ok=True)

# 创建HanLP模型目录
if not os.path.exists(config.HANLP_MODEL_DIR):
    os.makedirs(config.HANLP_MODEL_DIR, exist_ok=True)

# 设置HanLP模型目录的权限，确保appuser可以写入
try:
    import stat
    os.chmod(config.HANLP_MODEL_DIR, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
except Exception as e:
    logger.warning(f"设置HanLP模型目录权限失败: {e}")

# 创建ModelScope缓存目录
if not os.path.exists(MODELSCOPE_CACHE_DIR):
    os.makedirs(MODELSCOPE_CACHE_DIR, exist_ok=True)

# 验证配置完整性
logger.info("配置验证完成")
logger.info(f"ModelScope缓存目录: {MODELSCOPE_CACHE_DIR}")
logger.info(f"HanLP模型目录: {config.HANLP_MODEL_DIR}")
logger.info(f"cemotion模型缓存目录: {config.MODEL_CACHE_DIR}")
logger.info(f"Hugging Face缓存目录: {config.HF_CACHE_DIR}")

# 检查并预加载模型
def preload_models_if_needed():
    """检查并预加载模型（如果需要）"""
    try:
        # 检查Hugging Face模型是否存在
        hf_tokenizer_path = os.path.join(config.HF_CACHE_DIR, 'hub', 'models--bert-base-chinese')
        cemotion_model_path = os.path.join(config.MODEL_CACHE_DIR, '.cemotion_cache', 'cemotion_2.0.pt')
        
        need_preload = False
        
        # 检查BERT tokenizer是否存在
        if not os.path.exists(hf_tokenizer_path):
            logger.info("BERT tokenizer未找到，需要预加载")
            need_preload = True
        else:
            logger.info("BERT tokenizer已存在")
        
        # 检查cemotion模型是否存在
        if not os.path.exists(cemotion_model_path):
            logger.info("cemotion模型未找到，需要预加载")
            need_preload = True
        else:
            logger.info("cemotion模型已存在")
        
        if need_preload:
            logger.info("开始预加载模型...")
            # 导入预加载脚本并执行
            import subprocess
            result = subprocess.run([sys.executable, 'preload_models.py'], 
                                  cwd=project_root,
                                  capture_output=True, 
                                  text=True,
                                  env={**os.environ, 'HF_HOME': config.HF_CACHE_DIR})  # 确保HF_HOME环境变量正确传递
            if result.returncode == 0:
                logger.info("模型预加载完成")
            else:
                logger.error(f"模型预加载失败: {result.stderr}")
                return False
        else:
            logger.info("所有模型已存在，跳过预加载")
        
        return True
    except Exception as e:
        logger.error(f"模型检查和预加载过程中出错: {e}")
        return False

# 预加载模型
preload_models_if_needed()

app = Flask(__name__)
# 配置JSON编码器，确保中文字符不会被转义
app.config['JSON_AS_ASCII'] = False

# JWT配置
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sentiscore-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1800  # 30分钟
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30天

# 初始化JWT管理器
jwt = JWTManager(app)

# JWT错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'code': 'TOKEN_EXPIRED',
        'message': '登录已过期，请重新登录',
        'timestamp': int(time.time())
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'code': 'INVALID_TOKEN',
        'message': '无效的访问令牌',
        'timestamp': int(time.time())
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'code': 'MISSING_TOKEN',
        'message': '缺少访问令牌',
        'timestamp': int(time.time())
    }), 401

# 初始化数据库 - 统一使用sentiscore.db数据库文件
database_manager = DatabaseManager(app)

# 在应用上下文中初始化数据库
with app.app_context():
    # 确保instance目录存在并设置正确的权限
    instance_dir = 'instance'
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir, exist_ok=True)
        print(f"✅ 创建instance目录: {instance_dir}")
    else:
        print(f"ℹ️  instance目录已存在: {instance_dir}")
    
    # 设置目录权限（确保appuser可以写入）
    try:
        import stat
        os.chmod(instance_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"✅ 设置instance目录权限")
    except Exception as e:
        print(f"⚠️  设置instance目录权限失败: {e}")
    
    # 确保数据库文件存在并设置正确的权限
    db_file = os.path.join(instance_dir, 'sentiscore.db')
    if not os.path.exists(db_file):
        try:
            with open(db_file, 'w') as f:
                pass  # 创建空文件
            print(f"✅ 创建数据库文件: {db_file}")
        except Exception as e:
            print(f"⚠️  创建数据库文件失败: {e}")
    
    # 设置数据库文件权限
    try:
        import stat
        os.chmod(db_file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"✅ 设置数据库文件权限")
    except Exception as e:
        print(f"⚠️  设置数据库文件权限失败: {e}")
    
    # 初始化数据库表和数据
    try:
        database_manager.create_tables()
        database_manager.update_table_structure()  # 更新表结构
        database_manager.init_database()
        database_manager.create_default_admin()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()

# 添加CORS支持
CORS(app, resources={
    r"/auth/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    },
    r"/analyze": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    },
    r"/batch": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    },
    r"/health": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    }
})

# 初始化情感分析器
try:
    emotion_analyzer = Cemotion(config=config)
    logger.info("情感分析器初始化成功")
    
    # 预热模型
    logger.info("正在预热模型...")
    start_time = time.time()
    emotion_analyzer.predict("预热文本")
    logger.info(f"模型预热完成，耗时: {time.time() - start_time:.2f}秒")
    
except Exception as e:
    logger.error(f"情感分析器初始化失败: {e}")
    emotion_analyzer = None

# 初始化文本分词器
try:
    text_segmentor = TextSegmentor(config=config)
    logger.info("文本分词器初始化成功")
except Exception as e:
    logger.error(f"文本分词器初始化失败: {e}", exc_info=True)
    text_segmentor = None

# 注册路由
register_routes(app, emotion_analyzer, text_segmentor)

# 定期清理线程
def cleanup_thread():
    """定期清理缓存和内存"""
    while True:
        time.sleep(3600)  # 每小时执行一次
        try:
            # 清理PyTorch缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 强制垃圾回收
            gc.collect()
            
            logger.info("定期清理完成")
        except Exception as e:
            logger.error(f"定期清理失败: {e}")

# 启动定期清理线程
cleanup_worker = threading.Thread(target=cleanup_thread, daemon=True)
cleanup_worker.start()
logger.info("定期清理线程已启动")

@app.before_request
def before_request():
    """请求前处理"""
    # 可以在这里添加请求前的处理逻辑
    pass

if __name__ == '__main__':
    # 启动Flask应用
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )