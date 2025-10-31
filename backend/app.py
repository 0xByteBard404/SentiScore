# -*- coding: utf-8 -*-
"""
主应用文件
"""
# 标准库
import time
import os
import warnings
import torch
import gc
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# 在导入任何其他模块之前设置环境变量
# 设置ModelScope环境变量（提前设置，确保在cemotion导入前生效）
# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
models_path = os.path.join(project_root, '..', 'models')
MODELSCOPE_CACHE_DIR = os.getenv('MODELSCOPE_CACHE_DIR', os.path.join(models_path, 'modelscope_cache'))
os.environ['MODELSCOPE_CACHE_HOME'] = MODELSCOPE_CACHE_DIR
os.environ['MODELSCOPE_CACHE_DIR'] = MODELSCOPE_CACHE_DIR

# 本地配置导入
from config import config

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
os.environ['HF_ENDPOINT'] = config.HF_MIRROR  # 使用国内镜像
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'  # 禁用进度条，避免影响日志

# 创建Hugging Face缓存目录
if not os.path.exists(config.HF_CACHE_DIR):
    os.makedirs(config.HF_CACHE_DIR, exist_ok=True)

# 验证配置完整性
logger.info("配置验证完成")
logger.info(f"ModelScope缓存目录: {MODELSCOPE_CACHE_DIR}")

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
database_manager.create_tables()
database_manager.update_table_structure()  # 更新表结构
database_manager.init_database()
database_manager.create_default_admin()

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
    logger.error(f"文本分词器初始化失败: {e}")
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