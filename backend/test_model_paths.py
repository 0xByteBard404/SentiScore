#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模型路径配置
"""
import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config import config

def test_model_paths():
    """测试模型路径配置"""
    print("=== 模型路径配置测试 ===")
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(project_root, '..', 'models')
    
    print(f"项目根目录: {project_root}")
    print(f"模型存储路径: {models_path}")
    
    # 检查路径是否存在
    if not os.path.exists(models_path):
        print(f"创建模型存储目录: {models_path}")
        os.makedirs(models_path, exist_ok=True)
    
    # 检查各个子目录
    subdirs = ['cemotion_cache', 'modelscope_cache', 'huggingface_cache']
    for subdir in subdirs:
        full_path = os.path.join(models_path, subdir)
        if not os.path.exists(full_path):
            print(f"创建子目录: {full_path}")
            os.makedirs(full_path, exist_ok=True)
        else:
            print(f"子目录已存在: {full_path}")
    
    # 打印配置信息
    print("\n=== 配置信息 ===")
    print(f"MODEL_CACHE_DIR: {config.MODEL_CACHE_DIR}")
    print(f"MODELSCOPE_CACHE_DIR: {config.MODELSCOPE_CACHE_DIR}")
    print(f"HF_CACHE_DIR: {config.HF_CACHE_DIR}")
    
    # 检查环境变量
    print("\n=== 环境变量 ===")
    print(f"MODELSCOPE_CACHE_HOME: {os.environ.get('MODELSCOPE_CACHE_HOME', '未设置')}")
    print(f"MODELSCOPE_CACHE_DIR: {os.environ.get('MODELSCOPE_CACHE_DIR', '未设置')}")
    print(f"HF_HOME: {os.environ.get('HF_HOME', '未设置')}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_model_paths()