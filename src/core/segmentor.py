import logging
import re
import os
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

from src.utils.helpers import APIError

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

        return True, None

    def segment_single(self, text: str) -> List[str]:
        """对单个文本进行分词"""
        try:
            # 使用pipeline进行分词
            result: Any = self.pipeline(input=text)
            # 只提取分词结果
            if isinstance(result, dict) and 'output' in result:
                words = [item.get('span', '') for item in result['output'] if isinstance(item, dict)]
                return words
            else:
                # 处理其他可能的返回格式
                return []
        except Exception as e:
            logger.error(f"文本分词过程中出错: {e}")
            raise

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

    def segment(self, text: Union[str, List[str]]) -> Union[List[str], List[List[str]]]:
        """通用分词接口，支持单个文本或文本列表"""
        if isinstance(text, str):
            return self.segment_single(text)
        elif isinstance(text, list):
            return self.segment_batch(text)
        else:
            raise ValueError(f"不支持的输入类型: {type(text)}")