"""
cemotion API 配置文件

注意：这个文件将在所有其他依赖导入之前被加载，以确保Hugging Face环境变量正确设置。
"""
import os
from typing import List

# 立即设置Hugging Face环境变量，必须在任何transformers导入之前
HF_MIRROR_DEFAULT = 'https://hf-mirror.com'
HF_ENDPOINT_VALUE = os.getenv('HF_ENDPOINT', HF_MIRROR_DEFAULT)
HF_CACHE_DIR_DEFAULT = os.getenv('HF_HOME', os.path.join(os.path.expanduser("~"), '.cache', 'huggingface'))

# 全局设置Hugging Face Hub配置
os.environ.setdefault('HF_ENDPOINT', HF_ENDPOINT_VALUE)
os.environ.setdefault('HF_HOME', HF_CACHE_DIR_DEFAULT)
os.environ.setdefault('HF_HUB_DISABLE_PROGRESS_BARS', 'true')
os.environ.setdefault('HF_HUB_ETAG_TIMEOUT', '10')

# 设置ModelScope缓存目录 - 使用与Docker卷挂载一致的路径
# 这需要在任何modelscope相关模块导入之前设置
MODELSCOPE_CACHE_DIR = os.getenv('MODELSCOPE_CACHE_DIR', '/app/.cache/modelscope')
os.environ.setdefault('MODELSCOPE_CACHE_HOME', MODELSCOPE_CACHE_DIR)
os.environ['MODELSCOPE_CACHE_HOME'] = MODELSCOPE_CACHE_DIR

class Config:
    """应用配置类"""

    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'development')

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # 模型配置
    MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', '/app/.cemotion_cache')

    # cemotion多源下载配置 (国内外镜像)
    MODEL_SOURCES = {
        'github': os.getenv('MODEL_URL_GITHUB', 'https://github.com/Cyberbolt/Cemotion/releases/download/2.0/cemotion_2.0.pt'),
        'gitee': os.getenv('MODEL_URL_GITEE', 'https://gitee.com/mirrors/cemotion/releases/download/2.0/cemotion_2.0.pt'),
        'coding': os.getenv('MODEL_URL_CODING', 'https://cemotion-static-1253868755.cos.ap-guangzhou.myqcloud.com/models/cemotion_2.0.pt'),
        # 如果以上都不可用，可以添加本地或其他云存储
    }

    # 下载策略配置
    MODEL_DOWNLOAD_STRATEGY = os.getenv('MODEL_DOWNLOAD_STRATEGY', 'auto')  # 'auto', 'cn_priority', 'global_priority'
    MODEL_DOWNLOAD_TIMEOUT = int(os.getenv('MODEL_DOWNLOAD_TIMEOUT', '60'))  # 下载超时时间(秒)

    # Hugging Face配置
    HF_CACHE_DIR = os.getenv('HF_HOME', '/app/.cache/huggingface')
    HF_ENDPOINT = os.getenv('HF_ENDPOINT', 'https://huggingface.co')
    # 使用国内镜像加速Hugging Face下载
    HF_MIRROR = os.getenv('HF_MIRROR', 'https://hf-mirror.com')  # 或使用 'https://huggingface.co' (官方)

    # ModelScope配置
    MODELSCOPE_CACHE_DIR = os.getenv('MODELSCOPE_CACHE_DIR', '/app/.cache/modelscope')

    # API配置
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '512'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '16'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

    # 性能配置
    LRU_CACHE_SIZE = int(os.getenv('LRU_CACHE_SIZE', '1000'))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    BATCH_MAX_LENGTH = int(os.getenv('BATCH_MAX_LENGTH', '128'))  # 批处理时单个文本最大长度
    WARMUP_ENABLED = os.getenv('WARMUP_ENABLED', 'true').lower() == 'true'  # 是否启用模型预热
    
    # 预热配置
    WARMUP_TEXTS = [
        "这个产品非常好，我很喜欢",
        "服务态度很差，非常失望", 
        "今天天气不错",
        "一般般吧，没什么特别的"
    ]

    # 语言配置
    SUPPORTED_LANGUAGES: List[str] = ['zh', 'zh-cn', 'zh-tw']

    # 服务信息
    SERVICE_NAME = 'cemotion-api'
    VERSION = '1.0.0'
    DESCRIPTION = '中文情感分析API服务'

# 创建全局配置实例
config = Config()

# 导出配置验证函数
def validate_config():
    """验证配置的合理性"""
    assert config.MAX_TEXT_LENGTH > 0, "MAX_TEXT_LENGTH必须大于0"
    assert config.BATCH_SIZE > 0, "BATCH_SIZE必须大于0"
    assert config.REQUEST_TIMEOUT > 0, "REQUEST_TIMEOUT必须大于0"
    assert config.LRU_CACHE_SIZE > 0, "LRU_CACHE_SIZE必须大于0"
    assert config.BATCH_MAX_LENGTH > 0, "BATCH_MAX_LENGTH必须大于0"

    # 创建缓存目录
    if not os.path.exists(config.MODEL_CACHE_DIR):
        os.makedirs(config.MODEL_CACHE_DIR)
    
    # 创建ModelScope缓存目录
    if not os.path.exists(config.MODELSCOPE_CACHE_DIR):
        os.makedirs(config.MODELSCOPE_CACHE_DIR)

# 运行配置验证
validate_config()

if __name__ == '__main__':
    # 打印当前配置
    print("=== cemotion API 配置信息 ===")
    for attr in dir(config):
        if not attr.startswith('_') and attr.isupper():
            value = getattr(config, attr)
            if isinstance(value, list):
                value = ', '.join(value)
            print(f"{attr}: {value}")