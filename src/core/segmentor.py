import logging
import re
from typing import List, Union
from cemotion import Cegmentor

from src.utils.helpers import APIError

logger = logging.getLogger('SentiScore')


class TextSegmentor:
    """文本分词器类，基于cemotion的Cegmentor实现"""
    
    def __init__(self, config=None):
        """初始化分词器"""
        try:
            self.segmentor = Cegmentor()
            logger.info("文本分词器初始化成功")
        except Exception as e:
            logger.error(f"文本分词器初始化失败: {e}")
            raise
    
    def validate_input(self, text: str) -> tuple[bool, APIError or None]:
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

        # 检查是否包含中文字符
        if not re.search(r'[\u4e00-\u9fff]', text):
            return False, APIError(
                code="NO_CHINESE_TEXT",
                message="输入文本必须包含中文字符"
            )

        return True, None

    def segment_single(self, text: str) -> List[str]:
        """对单个文本进行分词"""
        try:
            result = self.segmentor.segment(text)
            return result
        except Exception as e:
            logger.error(f"文本分词过程中出错: {e}")
            raise

    def segment_batch(self, texts: List[str]) -> List[List[str]]:
        """对多个文本进行批量分词"""
        try:
            results = self.segmentor.segment(texts)
            return results
        except Exception as e:
            logger.error(f"批量文本分词过程中出错: {e}")
            raise

    def segment(self, text: Union[str, List[str]]) -> Union[List[str], List[List[str]]]:
        """通用分词接口，支持单个文本或文本列表"""
        if isinstance(text, str):
            return self.segment_single(text)
        elif isinstance(text, list):
            return self.segment_batch(text)
        else:
            raise ValueError(f"不支持的输入类型: {type(text)}")