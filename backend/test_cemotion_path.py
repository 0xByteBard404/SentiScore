#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试cemotion模型路径配置
"""
import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config import config
from src.core.cemotion import Cemotion

def test_cemotion_path():
    """测试cemotion模型路径配置"""
    print("=== cemotion模型路径测试 ===")
    
    # 打印配置信息
    print(f"MODEL_CACHE_DIR: {config.MODEL_CACHE_DIR}")
    
    # 检查目录是否存在
    if not os.path.exists(config.MODEL_CACHE_DIR):
        print(f"创建目录: {config.MODEL_CACHE_DIR}")
        os.makedirs(config.MODEL_CACHE_DIR, exist_ok=True)
    
    # 测试cemotion初始化
    try:
        print("初始化Cemotion模型...")
        emotion_analyzer = Cemotion(config=config)
        print("Cemotion模型初始化成功")
        
        # 测试预测
        print("测试情感分析...")
        result = emotion_analyzer.predict("这个产品非常好用")
        print(f"分析结果: {result}")
        
    except Exception as e:
        print(f"Cemotion测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cemotion_path()