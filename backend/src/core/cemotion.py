# -*- coding: utf-8 -*-
"""
情感分析核心模块
基于cemotion库的情感分析实现
"""
import os
import logging
from typing import Union, List, Tuple
from cemotion import Cemotion as CemotionBase
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger('SentiScore')

class EmotionResult:
    """情感分析结果类"""
    def __init__(self, emotion_score: float, emotion: str, confidence: float, text_length: int):
        self.emotion_score = emotion_score
        self.emotion = emotion
        self.confidence = confidence
        self.text_length = text_length

class APIError(Exception):
    """API错误类"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class EmotionAnalysisError(Exception):
    """情感分析错误类"""
    pass

class Cemotion:
    """
    情感分析器封装类
    """
    
    def __init__(self, config=None):
        """
        初始化情感分析器
        
        Args:
            config: 配置对象，包含模型相关配置
        """
        self.model = None
        self.config = config
        
        try:
            # 在初始化模型之前设置环境变量
            # 设置Hugging Face离线模式
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # 应用镜像配置 - 确保使用HF_ENDPOINT而不是HF_MIRROR
            if self.config and hasattr(self.config, 'HF_ENDPOINT'):
                os.environ['HF_ENDPOINT'] = self.config.HF_ENDPOINT
            if self.config and hasattr(self.config, 'HF_MIRROR'):
                # 为了兼容性也设置HF_MIRROR
                os.environ['HF_MIRROR'] = self.config.HF_MIRROR
            
            # 配置下载超时和重试机制
            if self.config and hasattr(self.config, 'MODEL_DOWNLOAD_TIMEOUT'):
                os.environ['HF_HUB_ETAG_TIMEOUT'] = str(self.config.MODEL_DOWNLOAD_TIMEOUT)
                os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = str(self.config.MODEL_DOWNLOAD_TIMEOUT)
            
            # 设置HF_HOME环境变量
            if self.config and hasattr(self.config, 'HF_CACHE_DIR'):
                os.environ['HF_HOME'] = self.config.HF_CACHE_DIR
            
            # 初始化Cemotion模型
            if self.config and hasattr(self.config, 'MODEL_CACHE_DIR') and self.config.MODEL_CACHE_DIR:
                model_cache_dir = self.config.MODEL_CACHE_DIR
                # 确保目录存在
                if not os.path.exists(model_cache_dir):
                    os.makedirs(model_cache_dir, exist_ok=True)
                
                # 保存当前工作目录
                original_cwd = os.getcwd()
                
                # 切换到模型缓存目录
                os.chdir(model_cache_dir)
                
                # 在指定目录初始化模型
                self.model = CemotionBase()
                logger.info(f"情感分析模型加载成功，使用缓存目录: {model_cache_dir}")
                
                # 切换回原来的工作目录
                os.chdir(original_cwd)
            else:
                # 使用默认路径
                self.model = CemotionBase()
                logger.info("情感分析模型加载成功（使用默认模型）")
        except Exception as e:
            logger.error(f"情感分析模型加载失败: {e}")
            raise
    
    def validate_input(self, text: str) -> Tuple[bool, Union[APIError, None]]:
        """
        验证输入参数
        
        Args:
            text: 待分析的文本
            
        Returns:
            tuple[bool, Optional[APIError]]: (是否有效, 错误信息)
        """
        if not isinstance(text, str):
            return False, APIError(
                code="INVALID_TYPE",
                message="输入的text必须是字符串类型"
            )

        if not text.strip():
            return False, APIError(
                code="EMPTY_TEXT",
                message="输入的文本不能为空"
            )

        # 这里可以添加其他验证逻辑
        return True, None

    def predict_single(self, text: str) -> float:
        """
        分析单个文本的情感分数
        
        Args:
            text: 待分析的文本
            
        Returns:
            float: 情感分数，范围0-1，越接近1表示越积极
        """
        if not self.model:
            raise Exception("情感分析模型未初始化")
        
        # 保存当前工作目录
        original_cwd = os.getcwd()
        
        try:
            # 如果有配置模型缓存目录，切换到该目录
            if self.config and hasattr(self.config, 'MODEL_CACHE_DIR') and self.config.MODEL_CACHE_DIR:
                model_cache_dir = self.config.MODEL_CACHE_DIR
                if os.path.exists(model_cache_dir):
                    os.chdir(model_cache_dir)
            
            result = self.model.predict(text)
            
            # 切换回原来的工作目录
            os.chdir(original_cwd)
            
            # 确保返回值在合理范围内
            score = 0.5
            if isinstance(result, list) and len(result) > 0:
                # 如果返回的是列表，取第一个元素
                first_element = result[0]
                if first_element is not None:
                    if isinstance(first_element, (int, float)):
                        score = float(first_element)
                    else:
                        try:
                            score = float(str(first_element))
                        except:
                            score = 0.5
            elif result is not None:
                if isinstance(result, (int, float)):
                    score = float(result)
                else:
                    try:
                        score = float(str(result))
                    except:
                        score = 0.5
            return max(0.0, min(1.0, score))
        except Exception as e:
            # 确保切换回原来的工作目录
            try:
                os.chdir(original_cwd)
            except:
                pass
            logger.error(f"情感分析失败: {e}")
            raise

    def predict_batch(self, texts: List[str]) -> List[float]:
        """
        批量分析文本情感分数
        
        Args:
            texts: 待分析的文本列表
            
        Returns:
            List[float]: 情感分数列表
        """
        if not self.model:
            raise Exception("情感分析模型未初始化")
        
        # 保存当前工作目录
        original_cwd = os.getcwd()
        
        try:
            # 如果有配置模型缓存目录，切换到该目录
            if self.config and hasattr(self.config, 'MODEL_CACHE_DIR') and self.config.MODEL_CACHE_DIR:
                model_cache_dir = self.config.MODEL_CACHE_DIR
                if os.path.exists(model_cache_dir):
                    os.chdir(model_cache_dir)
            
            results = []
            for text in texts:
                result = self.model.predict(text)
                # 确保返回值在合理范围内
                score = 0.5
                if isinstance(result, list) and len(result) > 0:
                    # 如果返回的是列表，取第一个元素
                    first_element = result[0]
                    if first_element is not None:
                        if isinstance(first_element, (int, float)):
                            score = float(first_element)
                        else:
                            try:
                                score = float(str(first_element))
                            except:
                                score = 0.5
                elif result is not None:
                    if isinstance(result, (int, float)):
                        score = float(result)
                    else:
                        try:
                            score = float(str(result))
                        except:
                            score = 0.5
                results.append(max(0.0, min(1.0, score)))
            
            # 切换回原来的工作目录
            os.chdir(original_cwd)
            
            return results
        except Exception as e:
            # 确保切换回原来的工作目录
            try:
                os.chdir(original_cwd)
            except:
                pass
            logger.error(f"批量情感分析失败: {e}")
            raise
    
    def analyze_emotion(self, text: str) -> EmotionResult:
        """执行情感分析并返回详细结果"""
        start_time = time.time()
        try:
            score = self.predict_single(text)

            # 计算置信度（距离0.5的程度）
            confidence = abs(score - 0.5) * 2
            emotion = "正面" if score >= 0.5 else "负面"

            result = EmotionResult(
                emotion_score=score,
                emotion=emotion,
                confidence=round(confidence, 4),
                text_length=len(text)
            )

            processing_time = time.time() - start_time
            logger.info(f"分析成功 - 文本长度: {len(text)} 字符，耗时: {processing_time:.4f}秒")

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"情感分析失败 - 文本长度: {len(text)} 字符，耗时: {processing_time:.4f}秒, 错误: {str(e)}")
            raise

    # 保持向后兼容性
    def predict(self, text):
        """保持与原接口的兼容性"""
        if isinstance(text, str):
            return self.predict_single(text)
        elif isinstance(text, list):
            return self.predict_batch(text)
        elif hasattr(text, 'tolist') and hasattr(text, 'shape'):
            try:
                text_list = text.tolist()
                return self.predict_batch(text_list)
            except:
                raise ValueError(f"不支持的输入类型: {type(text)}")
        else:
            raise ValueError(f"不支持的输入类型: {type(text)}")

    def deal(self, list_text):
        """处理多文本输入"""
        return self.predict_batch(list_text)