import logging
import re
import os
import sys
from typing import List, Union, Optional, Tuple, Any

# 在导入任何相关模块之前设置环境变量，确保ModelScope使用正确的缓存路径
modelscope_cache_dir: str = '/app/.cache/modelscope'
env_cache_dir = os.getenv('MODELSCOPE_CACHE_DIR')
if env_cache_dir:
    modelscope_cache_dir = env_cache_dir
    
os.environ['MODELSCOPE_CACHE_HOME'] = modelscope_cache_dir
os.environ['MODELSCOPE_CACHE_DIR'] = modelscope_cache_dir

# 确保缓存目录存在
if not os.path.exists(modelscope_cache_dir):
    os.makedirs(modelscope_cache_dir, exist_ok=True)

# 导入ModelScope相关类
from modelscope.models import Model
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.preprocessors import TokenClassificationTransformersPreprocessor
from modelscope.hub.snapshot_download import snapshot_download

# 定义APIError类，避免导入问题
class APIError:
    """API错误类"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

logger = logging.getLogger('SentiScore')


class TextSegmentor:
    """文本分词器类，基于ModelScope的实现"""
    
    def __init__(self, config=None):
        """初始化分词器"""
        try:
            # 获取配置中的缓存目录
            self.modelscope_cache_dir: str = '/app/.cache/modelscope'
            if config and hasattr(config, 'MODELSCOPE_CACHE_DIR') and config.MODELSCOPE_CACHE_DIR:
                self.modelscope_cache_dir = config.MODELSCOPE_CACHE_DIR
                
            # 确保环境变量已经正确设置
            os.environ['MODELSCOPE_CACHE_HOME'] = self.modelscope_cache_dir
            os.environ['MODELSCOPE_CACHE_DIR'] = self.modelscope_cache_dir
            
            # 确保缓存目录存在
            if not os.path.exists(self.modelscope_cache_dir):
                os.makedirs(self.modelscope_cache_dir, exist_ok=True)
            
            # 先手动下载模型到指定目录
            model_id = 'damo/nlp_structbert_word-segmentation_chinese-base'
            logger.info(f"开始下载模型 {model_id} 到目录: {self.modelscope_cache_dir}")
            model_dir = snapshot_download(model_id, cache_dir=self.modelscope_cache_dir)
            
            # 然后从本地目录加载模型
            self.model = Model.from_pretrained(model_dir)
            # 忽略类型检查错误
            self.tokenizer = TokenClassificationTransformersPreprocessor(self.model.model_dir)  # type: ignore
            self.pipeline = pipeline(task=Tasks.token_classification, model=self.model, preprocessor=self.tokenizer)  # type: ignore
            
            logger.info(f"文本分词器初始化成功，使用缓存目录: {self.modelscope_cache_dir}")
        except Exception as e:
            logger.error(f"文本分词器初始化失败: {e}")
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
        max_length = 512  # 默认限制
        try:
            # 尝试导入配置获取最大长度限制
            # 添加项目根目录到Python路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            backend_path = os.path.join(project_root, 'backend')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            # 尝试导入配置
            from backend.config import config
            max_length = getattr(config, 'MAX_TEXT_LENGTH', 512)
        except:
            # 如果导入失败，使用默认值
            pass
            
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
            # 限制文本长度以避免模型张量维度错误
            # ModelScope的分词模型通常有最大序列长度限制（如512或1024）
            max_model_length = 512  # 根据模型实际情况调整
            if len(text) > max_model_length:
                logger.warning(f"文本长度({len(text)})超过模型最大限制({max_model_length})，将截断处理")
                text = text[:max_model_length]
            
            # 进一步确保文本长度安全，留一些余量
            safe_length = 510
            if len(text) > safe_length:
                text = text[:safe_length]
                logger.warning(f"进一步截断文本到安全长度: {safe_length}")
            
            # 如果文本为空，直接返回空列表
            if not text.strip():
                return []
            
            # 使用pipeline进行分词
            result: Any = self.pipeline(input=text)
            # 只提取分词结果
            if isinstance(result, dict) and 'output' in result:
                words = [item.get('span', '') for item in result['output'] if isinstance(item, dict)]
                # 如果分词结果为空或只有单字符，尝试不同的处理方式
                if not words or (len(words) == len(text) and all(len(w) <= 1 for w in words)):
                    logger.warning("分词结果可能不理想，尝试优化处理")
                    # 过滤掉空字符串和纯空格
                    words = [w for w in words if w.strip()]
                    # 如果处理后仍然不理想，返回字符列表作为后备
                    if not words:
                        logger.warning("分词结果为空，返回字符列表作为后备")
                        return list(text)
                return words
            elif isinstance(result, list):
                # 处理列表格式的返回结果
                words = []
                for item in result:
                    if isinstance(item, dict) and 'span' in item:
                        words.append(item['span'])
                    elif isinstance(item, str):
                        words.append(item)
                # 如果分词结果为空或只有单字符，返回字符列表作为后备
                if not words or (len(words) == len(text) and all(len(w) <= 1 for w in words)):
                    logger.warning("分词结果可能不理想，返回字符列表作为后备")
                    return list(text)
                return words
            else:
                # 处理其他可能的返回格式
                logger.warning("分词结果格式不符合预期，返回字符列表作为后备")
                return list(text)
        except Exception as e:
            logger.error(f"文本分词过程中出错: {e}", exc_info=True)
            # 返回字符列表而不是空列表，作为更合理的后备方案
            logger.warning("返回字符列表作为最终后备方案")
            return list(text)
    
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

    def segment_long_text(self, text: str, max_chunk_size: int = 512) -> List[str]:
        """对长文本进行分块分词处理"""
        try:
            logger.info(f"开始长文本分词处理，文本长度: {len(text)}, 分块大小: {max_chunk_size}")
            
            # 确保分块大小不超过模型限制
            max_model_length = 512
            safe_chunk_size = 510  # 留一些余量
            if max_chunk_size > safe_chunk_size:
                max_chunk_size = safe_chunk_size
                logger.info(f"调整分块大小为安全限制: {max_chunk_size}")
            
            if len(text) <= max_chunk_size:
                # 如果文本长度在限制内，直接分词
                logger.info("文本长度在限制内，直接分词")
                try:
                    result = self.segment_single(text)
                    # 如果结果为空，返回字符列表
                    if not result:
                        logger.warning("短文本分词结果为空，返回字符列表")
                        return list(text)
                    return result
                except Exception as e:
                    logger.error(f"短文本分词失败: {e}")
                    return list(text)  # 返回字符列表作为后备
            
            # 将长文本分块处理
            segments = []
            start = 0
            chunk_count = 0
            
            while start < len(text):
                # 获取一个文本块
                chunk = text[start:start + max_chunk_size]
                chunk_count += 1
                logger.debug(f"处理第{chunk_count}个文本块，长度: {len(chunk)}")
                
                # 对文本块进行分词
                try:
                    chunk_segments = self.segment_single(chunk)
                    segments.extend(chunk_segments)
                    logger.debug(f"第{chunk_count}个文本块分词结果数量: {len(chunk_segments)}")
                except Exception as e:
                    logger.error(f"第{chunk_count}个文本块分词失败: {e}")
                    # 如果分词失败，尝试更小的块
                    if len(chunk) > 100:
                        # 将块再分半处理
                        half_size = len(chunk) // 2
                        try:
                            chunk_segments1 = self.segment_single(chunk[:half_size])
                            chunk_segments2 = self.segment_single(chunk[half_size:])
                            segments.extend(chunk_segments1)
                            segments.extend(chunk_segments2)
                            logger.debug(f"第{chunk_count}个文本块分半处理成功")
                        except Exception as e2:
                            logger.error(f"第{chunk_count}个文本块分半处理也失败: {e2}")
                            # 如果还是失败，添加原始文本作为后备
                            segments.extend(list(chunk))
                    else:
                        # 对于很小的块，直接添加字符
                        segments.extend(list(chunk))
                
                # 移动到下一个块
                start += max_chunk_size
                
            # 如果最终结果为空，返回字符列表
            if not segments:
                logger.warning("长文本分词结果为空，返回字符列表作为最终后备方案")
                return list(text)
                
            logger.info(f"长文本分词完成，总块数: {chunk_count}, 总分词数量: {len(segments)}")
            return segments
        except Exception as e:
            logger.error(f"长文本分词过程中出错: {e}", exc_info=True)
            # 返回字符列表作为最终后备方案
            return list(text)
    
    def segment(self, text: Union[str, List[str]]) -> Union[List[str], List[List[str]]]:
        """通用分词接口，支持单个文本或文本列表"""
        if isinstance(text, str):
            return self.segment_single(text)
        elif isinstance(text, list):
            return self.segment_batch(text)
        else:
            raise ValueError(f"不支持的输入类型: {type(text)}")