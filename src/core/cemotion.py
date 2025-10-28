import os
import re
import time
import logging
import torch
from typing import List, Tuple, Optional
from functools import lru_cache
from transformers import BertTokenizer
from urllib.parse import urlparse

from src.models.emotion_classifier import SentimentClassifier, load_model
from src.utils.helpers import get_model_path, EmotionResult, APIError, EmotionAnalysisError

logger = logging.getLogger('SentiScore')


class Cemotion:
    def __init__(self, config):
        self.config = config
        self.path = get_model_path(config)

        # 设备检测
        if torch.cuda.is_available():
            device = torch.device('cuda')
            logger.info("使用GPU进行推理")
        elif torch.backends.mps.is_available():
            device = torch.device('mps')
            logger.info("使用Apple Silicon MPS进行推理")
        else:
            device = torch.device('cpu')
            logger.info("使用CPU进行推理")

        # 初始化模型
        try:
            model = SentimentClassifier(num_classes=1)
            self.model = load_model(model, self.path, device)
            self.model.to(device)
            self.model.eval()
            self.device = device
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

        # 使用LRU缓存tokenizer以避免重复加载
        self._get_tokenizer = lru_cache(maxsize=config.LRU_CACHE_SIZE)(self._load_tokenizer)
        
        # 创建情感分析结果缓存
        self._analyze_cache = lru_cache(maxsize=config.LRU_CACHE_SIZE)(self._analyze_emotion_cached)

    @staticmethod
    def _load_tokenizer():
        """加载tokenizer，支持多源下载"""
        # 使用国内镜像下载，避免网络问题
        return BertTokenizer.from_pretrained(
            'bert-base-chinese'
        )

    def validate_input(self, text: str) -> Tuple[bool, Optional[APIError]]:
        """验证输入参数"""
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

        if len(text) > self.config.MAX_TEXT_LENGTH:
            return False, APIError(
                code="TEXT_TOO_LONG",
                message=f"文本长度超过限制，最大允许长度为{self.config.MAX_TEXT_LENGTH}个字符"
            )

        # 检查是否包含中文字符
        if not re.search(r'[\u4e00-\u9fff]', text):
            return False, APIError(
                code="NO_CHINESE_TEXT",
                message="输入文本必须包含中文字符"
            )

        return True, None

    def predict_single(self, text: str) -> float:
        """单文本情感预测"""
        try:
            tokenizer = self._get_tokenizer()
            inputs = tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )

            # 将张量移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs).squeeze(1)  # 模型直接返回logits
                prediction = torch.sigmoid(outputs).cpu().item()

            return round(prediction, 6)

        except Exception as e:
            logger.error(f"预测过程中出错: {e}")
            raise EmotionAnalysisError(f"预测失败: {str(e)}")

    def predict_batch(self, texts: List[str]) -> List[float]:
        """批量文本情感预测"""
        try:
            tokenizer = self._get_tokenizer()
            
            # 截断过长的文本以符合配置限制
            truncated_texts = [text[:self.config.BATCH_MAX_LENGTH] for text in texts]
            
            # 批量编码所有文本
            encoded_inputs = tokenizer(
                truncated_texts,
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            
            # 将张量移动到设备
            encoded_inputs = {k: v.to(self.device) for k, v in encoded_inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**encoded_inputs).squeeze(1)
                predictions = torch.sigmoid(outputs).cpu().tolist()
            
            # 确保返回正确的格式
            if isinstance(predictions, float):
                predictions = [predictions]
            
            return [round(pred, 6) for pred in predictions]
            
        except Exception as e:
            logger.error(f"批量预测过程中出错: {e}")
            raise EmotionAnalysisError(f"批量预测失败: {str(e)}")

    def analyze_emotion(self, text: str) -> EmotionResult:
        """执行情感分析并返回详细结果"""
        # 使用缓存的结果（如果存在）
        return self._analyze_cache(text)
    
    def _analyze_emotion_cached(self, text: str) -> EmotionResult:
        """实际执行情感分析的方法（被缓存包装）"""
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
        # 对于列表输入，保持原有逻辑，但添加改进
        elif isinstance(text, list) or (hasattr(text, 'tolist') and hasattr(text, 'shape')):
            if hasattr(text, 'tolist'):
                text = text.tolist()

            if len(text) > self.config.BATCH_SIZE:
                logger.warning(f"批量处理数量 {len(text)} 超过限制 {self.config.BATCH_SIZE}，将截断前 {self.config.BATCH_SIZE} 个")
                text = text[:self.config.BATCH_SIZE]

            predictions = []
            for t in text:
                if isinstance(t, str):
                    pred = self.predict_single(t)
                else:
                    logger.warning(f"跳过非字符串输入: {t}")
                    continue
                predictions.append(round(pred, 6))

            return [[sentence, pred] for sentence, pred in zip(text, predictions)]

        else:
            raise ValueError(f"不支持的输入类型: {type(text)}")

    def deal(self, list_text):
        """处理多文本输入（优化版本）"""
        if len(list_text) > self.config.BATCH_SIZE:
            logger.warning(f"批量处理数量 {len(list_text)} 超过限制 {self.config.BATCH_SIZE}")
            list_text = list_text[:self.config.BATCH_SIZE]

        predictions = []
        tokenizer = self._get_tokenizer()

        for sentence in list_text:
            if isinstance(sentence, str):
                prediction = self.predict_single(sentence)
                predictions.append(prediction)
            else:
                logger.warning(f"跳过非字符串输入: {type(sentence)}")
                predictions.append(0.5)  # 默认中性

        return predictions