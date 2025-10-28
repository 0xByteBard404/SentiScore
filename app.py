from flask import Flask, request, jsonify
# 标准库
import os
import time
import torch
import logging
import warnings
import gc
import threading
from flask import Flask

# 在导入任何其他模块之前设置环境变量
# 设置ModelScope环境变量（提前设置，确保在cemotion导入前生效）
MODELSCOPE_CACHE_DIR = os.getenv('MODELSCOPE_CACHE_DIR', '/app/.cache/modelscope')
os.environ['MODELSCOPE_CACHE_HOME'] = MODELSCOPE_CACHE_DIR
os.environ['MODELSCOPE_CACHE_DIR'] = MODELSCOPE_CACHE_DIR

# 本地配置导入
from config import config

# 工具函数
from src.utils.helpers import setup_logging, EmotionAnalysisError
from src.core.cemotion import Cemotion
from src.core.segmentor import TextSegmentor
from src.api.routes import register_routes

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

# 初始化情感分析器
try:
    analyzer = Cemotion(config)
    logger.info("情感分析器初始化成功")
    
    # 预热模型以减少首次请求延迟
    if config.WARMUP_ENABLED:
        logger.info("正在预热模型...")
        warmup_start = time.time()
        try:
            warmup_texts = config.WARMUP_TEXTS
            _ = analyzer.predict_batch(warmup_texts)
            warmup_time = time.time() - warmup_start
            logger.info(f"模型预热完成，耗时: {warmup_time:.2f}秒")
        except Exception as e:
            logger.warning(f"模型预热失败: {e}")
        
except Exception as e:
    logger.error(f"情感分析器初始化失败: {e}")
    raise

# 初始化分词器
try:
    segmentor = TextSegmentor(config)
    logger.info("文本分词器初始化成功")
except Exception as e:
    logger.error(f"文本分词器初始化失败: {e}")
    raise

# 注册路由
register_routes(app, analyzer, config)

# 启动定期清理线程
def start_cleanup_thread():
    """启动定期清理线程"""
    def cleanup_routine():
        while True:
            time.sleep(300)  # 每5分钟执行一次清理
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                gc.collect()
                logger.debug("定期清理完成")
            except Exception as e:
                logger.warning(f"定期清理出错: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_routine, daemon=True)
    cleanup_thread.start()
    logger.info("定期清理线程已启动")

start_cleanup_thread()

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        threaded=True  # 启用多线程
    )