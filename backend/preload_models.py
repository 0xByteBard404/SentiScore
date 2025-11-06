#!/usr/bin/env python3
"""
预加载所有必要的模型脚本
用于在首次运行时下载并缓存所有需要的模型
"""

import os
import sys
import logging
import time  # 新增time模块用于重试等待
from config import config

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ModelPreloader')

def preload_huggingface_models():
    """预加载Hugging Face模型"""
    logger.info("开始预加载Hugging Face模型...")
    
    try:
        # 设置Hugging Face环境变量
        os.environ['HF_HOME'] = config.HF_CACHE_DIR
        os.environ['HF_ENDPOINT'] = config.HF_ENDPOINT
        
        # 确保缓存目录存在
        if not os.path.exists(config.HF_CACHE_DIR):
            os.makedirs(config.HF_CACHE_DIR, exist_ok=True)
            logger.info(f"创建Hugging Face缓存目录: {config.HF_CACHE_DIR}")
        
        # 导入并加载BERT tokenizer和模型
        from transformers import BertTokenizer, BertForSequenceClassification
        
        logger.info("正在下载/加载 bert-base-chinese tokenizer...")
        tokenizer = BertTokenizer.from_pretrained(
            'bert-base-chinese',
            timeout=600  # 增加超时时间
        )
        logger.info("bert-base-chinese tokenizer 加载完成")
        
        logger.info("正在下载/加载 bert-base-chinese 模型...")
        model = BertForSequenceClassification.from_pretrained(
            'bert-base-chinese', 
            num_labels=1,
            timeout=600  # 增加超时时间
        )
        logger.info("bert-base-chinese 模型加载完成")
        
        logger.info("Hugging Face模型预加载完成")
        return True
    except Exception as e:
        logger.error(f"Hugging Face模型预加载失败: {e}")
        return False

def preload_cemotion_model():
    """预加载cemotion模型"""
    logger.info("开始预加载cemotion模型...")
    
    # 初始化original_cwd变量
    original_cwd = os.getcwd()
    
    try:
        # 确保cemotion缓存目录存在
        if not os.path.exists(config.MODEL_CACHE_DIR):
            os.makedirs(config.MODEL_CACHE_DIR, exist_ok=True)
            logger.info(f"创建cemotion缓存目录: {config.MODEL_CACHE_DIR}")
        
        # 切换到模型缓存目录
        os.chdir(config.MODEL_CACHE_DIR)
        
        # 导入并初始化cemotion
        from cemotion import Cemotion
        logger.info("正在下载/加载 cemotion 模型...")
        cemotion = Cemotion()
        logger.info("cemotion 模型加载完成")
        
        # 切换回原来的工作目录
        os.chdir(original_cwd)
        
        logger.info("cemotion模型预加载完成")
        return True
    except Exception as e:
        logger.error(f"cemotion模型预加载失败: {e}")
        # 切换回原来的工作目录（确保不会影响其他操作）
        try:
            os.chdir(original_cwd)
        except:
            pass
        return False

def main():
    """主函数"""
    logger.info("=== 模型预加载脚本开始 ===")
    
    # 预加载Hugging Face模型（带重试机制）
    max_retries = 3
    hf_success = False
    for attempt in range(max_retries):
        logger.info(f"尝试预加载Hugging Face模型 (第{attempt+1}次)")
        hf_success = preload_huggingface_models()
        if hf_success:
            break
        logger.warning(f"Hugging Face模型预加载失败，将在5秒后重试...")
        time.sleep(5)
    
    # 预加载cemotion模型（带重试机制）
    cemotion_success = False
    for attempt in range(max_retries):
        logger.info(f"尝试预加载cemotion模型 (第{attempt+1}次)")
        cemotion_success = preload_cemotion_model()
        if cemotion_success:
            break
        logger.warning(f"cemotion模型预加载失败，将在5秒后重试...")
        time.sleep(5)
    
    if hf_success and cemotion_success:
        logger.info("=== 所有模型预加载完成 ===")
        return 0
    else:
        logger.error("=== 模型预加载失败 ===")
        return 1

if __name__ == '__main__':
    sys.exit(main())
