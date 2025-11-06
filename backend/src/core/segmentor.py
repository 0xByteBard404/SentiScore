import logging
import re
import os
from typing import List, Union, Tuple, Optional, Any

# 修复容器中的导入问题
try:
    # 在容器环境中，模块路径是 src.utils.helpers
    from src.utils.helpers import APIError
except ImportError:
    # 在开发环境中，模块路径是 backend.src.utils.helpers
    from backend.src.utils.helpers import APIError

# 设置HanLP模型目录，确保模型下载到指定的持久化目录
# 必须在导入hanlp之前设置HANLP_HOME环境变量
from config import config
if hasattr(config, 'HANLP_MODEL_DIR') and config.HANLP_MODEL_DIR:
    # 设置HanLP根目录环境变量
    os.environ['HANLP_HOME'] = config.HANLP_MODEL_DIR
    # 确保目录存在
    if not os.path.exists(config.HANLP_MODEL_DIR):
        os.makedirs(config.HANLP_MODEL_DIR, exist_ok=True)

# 移除LTP导入，替换为HanLP
import hanlp

logger = logging.getLogger('SentiScore')


class TextSegmentor:
    """文本分词器类，基于HanLP的实现"""
    
    def __init__(self, config=None):
        """初始化HanLP分词器"""
        try:
            # 为避免静态类型检查工具报错，使用字符串方式加载模型
            # COARSE_ELECTRA_SMALL_ZH 是 hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH 的字符串标识符
            self.hanlp: Any = hanlp.load('COARSE_ELECTRA_SMALL_ZH')
            logger.info("HanLP分词器初始化成功")
        except Exception as e:
            logger.error(f"HanLP分词器初始化失败: {e}", exc_info=True)
            raise
    
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

        # 检查是否包含中文字符
        if not re.search(r'[\u4e00-\u9fff]', text):
            return False, APIError(
                code="NO_CHINESE_TEXT",
                message="输入文本必须包含中文字符"
            )

        # 检查文本长度限制
        from config import config
        max_length = getattr(config, 'MAX_TEXT_LENGTH', 512)
        if len(text) > max_length:
            return False, APIError(
                code="TEXT_TOO_LONG",
                message=f"输入文本长度不能超过{max_length}个字符"
            )

        return True, None

    def validate_input_without_length_check(self, text: str) -> Tuple[bool, Optional[APIError]]:
        """验证输入参数（不检查长度限制）"""
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
            # 空文本处理
            if not text.strip():
                return []
            
            # 使用HanLP进行分词
            result = self.hanlp(text)
            if result is not None:
                return result
            else:
                return []
        except Exception as e:
            logger.error(f"文本分词过程中出错: {e}", exc_info=True)
            # 降级方案：使用简单分词
            return self._fallback_segment(text)
    
    def segment_batch(self, texts: List[str]) -> List[List[str]]:
        """对多个文本进行批量分词"""
        try:
            results = []
            for text in texts:
                # 对每个文本执行分词
                result = self.segment_single(text)
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"批量文本分词过程中出错: {e}")
            raise

    def segment_long_text(self, text: str, max_len: int = 10000) -> List[str]:
        """对长文本进行智能分块分词处理"""
        try:
            # 智能分块策略（按句子边界切分）
            sentences = self._split_into_sentences(text)
            chunks = self._create_chunks(sentences, max_len)
            
            results = []
            for chunk in chunks:
                try:
                    # 使用HanLP进行分词
                    result = self.hanlp(chunk)
                    if result is not None:
                        results.extend(result)
                    else:
                        results.extend(self._fallback_segment(chunk))
                except Exception as e:
                    logger.error(f"分块处理失败: {e}")
                    results.extend(self._fallback_segment(chunk))
            
            return results
        except Exception as e:
            logger.error(f"长文本处理失败: {e}")
            return self._fallback_segment(text)
            
    def _split_into_sentences(self, text: str) -> List[str]:
        """按句子边界分割文本"""
        # 使用中文标点进行分句
        sentence_delimiters = re.compile(r'([。！？；\n])')
        sentences = []
        start = 0
        for match in sentence_delimiters.finditer(text):
            sentences.append(text[start:match.end()])
            start = match.end()
        if start < len(text):
            sentences.append(text[start:])
        return sentences
    
    def _create_chunks(self, sentences: List[str], max_len: int) -> List[str]:
        """将句子组合成合适大小的文本块"""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > max_len and current_chunk:
                # 当前块已满，保存并重置
                chunks.append(''.join(current_chunk))
                current_chunk = []
                current_length = 0
                
            current_chunk.append(sentence)
            current_length += len(sentence)
            
        if current_chunk:
            chunks.append(''.join(current_chunk))
            
        return chunks
    
    def _fallback_segment(self, text: str) -> List[str]:
        """三级降级策略"""
        try:
            # 1. 尝试减小分块尺寸
            if len(text) > 100:
                half = len(text) // 2
                # 递归调用时要确保不会无限递归
                if half > 50:  # 确保分块不会太小
                    try:
                        # 直接使用HanLP进行分词，避免递归调用segment_single
                        left_result = []
                        right_result = []
                        
                        # 处理左半部分
                        try:
                            result = self.hanlp(text[:half])
                            left_result = result if result is not None else list(text[:half])
                        except Exception as e:
                            logger.error(f"左半部分处理失败: {e}")
                            # 如果HanLP失败，使用规则分词
                            left_words = re.findall(r'[\u4e00-\u9fff]+|\w+', text[:half])
                            left_result = left_words if left_words else list(text[:half])
                        
                        # 处理右半部分
                        try:
                            result = self.hanlp(text[half:])
                            right_result = result if result is not None else list(text[half:])
                        except Exception as e:
                            logger.error(f"右半部分处理失败: {e}")
                            # 如果HanLP失败，使用规则分词
                            right_words = re.findall(r'[\u4e00-\u9fff]+|\w+', text[half:])
                            right_result = right_words if right_words else list(text[half:])
                        
                        # 确保返回的是List[str]类型
                        if isinstance(left_result, list) and isinstance(right_result, list):
                            return left_result + right_result
                        else:
                            # 如果不是列表，使用规则分词
                            words = re.findall(r'[\u4e00-\u9fff]+|\w+', text)  # 改进中文匹配
                            return words if words else list(text)
                    except Exception as e:
                        logger.error(f"分块处理失败: {e}")
                        # 如果分块处理失败，使用规则分词
                        words = re.findall(r'[\u4e00-\u9fff]+|\w+', text)  # 改进中文匹配
                        return words if words else list(text)
                
            # 2. 使用规则分词
            words = re.findall(r'[\u4e00-\u9fff]+|\w+', text)  # 改进中文匹配
            if words:
                return words
                
            # 3. 字符级回退
            return list(text)
        except Exception as e:
            logger.error(f"降级策略执行失败: {e}")
            # 最后的后备方案：确保返回List[str]
            words = re.findall(r'[\u4e00-\u9fff]+|\w+', text)  # 改进中文匹配
            return words if words else list(text)
    
    def segment(self, text: Union[str, List[str]]) -> Union[List[str], List[List[str]]]:
        """通用分词接口，支持单个文本或文本列表"""
        if isinstance(text, str):
            return self.segment_single(text)
        elif isinstance(text, list):
            return self.segment_batch(text)
        else:
            raise ValueError(f"不支持的输入类型: {type(text)}")