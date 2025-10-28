import os
import logging
import logging.handlers as handlers
import requests
import time
import gc
import traceback
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import torch
import warnings
from transformers import logging as transformers_logging

from config import config


# 情感分析结果类
@dataclass
class EmotionResult:
    emotion_score: float
    emotion: str
    confidence: float  # 置信度
    text_length: int

    def to_dict(self):
        return asdict(self)


# API错误类
@dataclass
class APIError:
    code: str
    message: str
    details: Optional[str] = None


class EmotionAnalysisError(ValueError):
    pass


class InvalidInputError(ValueError):
    pass


def setup_logging():
    """配置日志"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # 创建日志器
    logger = logging.getLogger('SentiScore')
    logger.setLevel(logging.DEBUG if log_level == 'DEBUG' else logging.INFO)

    # 防止重复添加handler
    if logger.handlers:
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if log_level == 'DEBUG' else logging.INFO)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)

    # 文件处理器（轮转日志）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = handlers.RotatingFileHandler(
        'logs/cemotion_api.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def determine_download_strategy(source_url: str) -> str:
    """根据URL判断下载区域 (国内/国外)"""
    try:
        domain = urlparse(source_url).netloc.lower()
        cn_domains = ['gitee.com', 'coding.net', 'myqcloud.com', 'aliyuncs.com']
        return 'cn' if any(domain.endswith(cn_domain) for cn_domain in cn_domains) else 'global'
    except Exception:
        return 'unknown'


def download_with_fallback(url: str, filepath: str, timeout: int = 30) -> bool:
    """带超时和错误处理的文件下载"""
    logger = logging.getLogger('SentiScore')
    try:
        logger.info(f"开始下载模型: {url}")
        response = requests.get(url, stream=True, timeout=timeout, verify=False)

        if response.status_code != 200:
            logger.warning(f"下载失败, 状态码: {response.status_code}")
            return False

        # 获取文件总大小（如果有的话）
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 简单的下载进度显示
                    if total_size > 0 and downloaded_size % (10*1024*1024) == 0:  # 每10MB显示一次进度
                        progress = (downloaded_size / total_size) * 100
                        logger.info(f"下载进度: {progress:.1f}%")
        return True

    except requests.exceptions.RequestException as e:
        logger.warning(f"下载失败: {e}")
        return False
    except Exception as e:
        logger.error(f"下载过程中发生未知错误: {e}")
        return False


def download_model_with_multiple_sources(cache_dir: str, sources: Dict[str, str],
                                       strategy: str = 'auto') -> Tuple[bool, str]:
    """
    多源下载模型文件，支持国内外镜像自动/手动切换

    Args:
        cache_dir: 缓存目录
        sources: 下载源字典
        strategy: 下载策略 ('auto', 'cn_priority', 'global_priority')

    Returns:
        (成功标志, 文件路径或错误信息)
    """
    logger = logging.getLogger('SentiScore')
    model_filename = 'cemotion_2.0.pt'
    filepath = os.path.join(cache_dir, model_filename)

    # 如果文件已存在，直接返回成功
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        logger.info("模型文件已存在，跳过下载")
        return True, filepath

    # 创建缓存目录
    os.makedirs(cache_dir, exist_ok=True)

    # 根据策略组织下载顺序
    if strategy == 'cn_priority':
        # 优先使用国内源
        source_order = [k for k in sources.keys() if determine_download_strategy(sources[k]) == 'cn'] + \
                      [k for k in sources.keys() if determine_download_strategy(sources[k]) == 'global']
    elif strategy == 'global_priority':
        # 优先使用国际源
        source_order = [k for k in sources.keys() if determine_download_strategy(sources[k]) == 'global'] + \
                      [k for k in sources.keys() if determine_download_strategy(sources[k]) == 'cn']
    else:  # auto - 自动选择（优先国内，失败后国际）
        source_order = list(sources.keys())

    logger.info(f"使用下载策略: {strategy}，尝试顺序: {source_order}")

    # 尝试每个下载源
    for source_name in source_order:
        source_url = sources[source_name]
        region = determine_download_strategy(source_url)

        logger.info(f"尝试从 {source_name} ({region}) 下载模型: {source_name}")

        # 临时文件名，避免下载中断导致的损坏文件
        temp_filepath = filepath + '.downloading'
        success = download_with_fallback(source_url, temp_filepath, config.MODEL_DOWNLOAD_TIMEOUT)

        if success:
            # 验证文件
            if os.path.getsize(temp_filepath) > 10*1024*1024:  # 至少10MB
                # 重命名临时文件为正式文件
                os.rename(temp_filepath, filepath)
                logger.info(f"模型下载成功! 来自: {source_name} ({region})")
                return True, filepath
            else:
                logger.warning(f"下载的文件太小，可能不完整: {os.path.getsize(temp_filepath)} bytes")
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
        else:
            logger.warning(f"从 {source_name} 下载失败，尝试下一个源")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

    return False, "所有下载源都失败了"


def get_model_path(config) -> str:
    """获取模型文件路径，支持多源下载"""
    cache_dir = config.MODEL_CACHE_DIR
    strategy = config.MODEL_DOWNLOAD_STRATEGY

    success, result = download_model_with_multiple_sources(
        cache_dir=cache_dir,
        sources=config.MODEL_SOURCES,
        strategy=strategy
    )

    if success:
        return result
    else:
        raise EmotionAnalysisError(f"模型下载失败: {result}")


def get_client_ip(request):
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def create_error_response(error_code: str, message: str, status_code: int = 400, details: Optional[str] = None):
    """创建统一的错误响应"""
    from flask import request
    error_obj = APIError(code=error_code, message=message, details=details)
    client_ip = get_client_ip(request)
    logging.getLogger('cemotion_api').warning(f"[{client_ip}] API错误 - {error_code}: {message}")
    from flask import jsonify
    return jsonify(asdict(error_obj)), status_code


def create_success_response(data: Any, client_ip: Optional[str] = None):
    """创建成功的响应"""
    from flask import request
    if client_ip is None:
        client_ip = get_client_ip(request)
    logging.getLogger('cemotion_api').info(f"[{client_ip}] 请求成功")
    from flask import jsonify
    return jsonify({"data": data, "timestamp": int(time.time())})