# -*- coding: utf-8 -*-
"""
API路由模块
处理所有RESTful API请求
"""
import time
import logging
import gc
import json
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.auth.decorators import api_key_required
from src.auth.service import AuthService
from src.models.api import APICall
from src.models.user import APIKey  # 添加APIKey模型导入
from src.utils.helpers import EmotionAnalysisError
from src.api.auth_routes import auth_bp  # 添加认证路由导入

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/')

def validate_json(f):
    """
    验证JSON请求体的装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否为GET请求，GET请求通常不需要JSON body
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        # 检查是否为JSON格式
        if not request.is_json:
            return jsonify({
                'code': 'INVALID_CONTENT_TYPE',
                'message': 'Content-Type必须为application/json',
                'timestamp': int(time.time())
            }), 400
        
        # 检查JSON数据是否为空
        data = request.get_json()
        if data is None:
            return jsonify({
                'code': 'INVALID_JSON',
                'message': '无效的JSON数据',
                'timestamp': int(time.time())
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def api_response(data=None, code=200, message="请求成功", **kwargs):
    """
    统一API响应格式
    
    Args:
        data: 响应数据
        code: 状态码
        message: 响应消息
        **kwargs: 其他参数
    """
    response = {
        'code': code,
        'message': message,
        'timestamp': int(time.time())
    }
    
    if data is not None:
        response['data'] = data
    
    response.update(kwargs)
    
    # 使用Response和json.dumps确保中文字符正确显示
    return Response(
        json.dumps(response, ensure_ascii=False),
        mimetype='application/json'
    )

def register_routes(app, emotion_analyzer=None, text_segmentor=None):
    """注册所有API路由"""
    
    @app.route('/health')
    def health_check():
        """健康检查端点"""
        try:
            # 检查情感分析器
            model_ready = emotion_analyzer is not None
            
            # 检查数据库连接
            from src.database.manager import db
            db_status = 'healthy'
            try:
                db.session.execute(db.text('SELECT 1'))
            except Exception as e:
                db_status = f'error: {str(e)}'
            
            return {
                'status': 'healthy' if model_ready and db_status == 'healthy' else 'unhealthy',
                'timestamp': int(time.time()),
                'model_ready': model_ready,
                'database': db_status,
                'gpu_available': False,  # 简化实现，实际项目中可以检查GPU状态
                'version': '2.0.0'
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'status': 'error',
                'timestamp': int(time.time()),
                'error': str(e)
            }, 500
    
    @api_bp.route('/analyze', methods=['POST'])
    @validate_json
    @api_key_required
    def analyze_emotion(user):
        """
        单文本情感分析接口
        """
        try:
            # 记录请求开始时间
            start_time = time.time()
            
            # 获取请求数据
            data = request.get_json()
            text = data.get('text', '')
            
            # 验证输入
            if emotion_analyzer:
                is_valid, error_msg = emotion_analyzer.validate_input(text)
                if not is_valid:
                    return api_response(
                        code=400,
                        message=error_msg.message if hasattr(error_msg, 'message') else str(error_msg)
                    ), 400
            else:
                if not text:
                    return api_response(
                        code=400,
                        message="文本不能为空"
                    ), 400
            
            # 执行情感分析
            if emotion_analyzer:
                # 使用新的predict方法
                emotion_result = emotion_analyzer.predict(text)
                if isinstance(emotion_result, list):
                    # 批量结果处理
                    emotion_score = emotion_result[0][1] if emotion_result else 0.5
                else:
                    # 单个结果处理
                    emotion_score = emotion_result
            else:
                # 模拟分析结果（用于测试）
                emotion_score = 0.5
            
            # 确定情感极性
            if emotion_score >= 0.6:
                emotion = "正面"
                confidence = emotion_score
            elif emotion_score <= 0.4:
                emotion = "负面"
                confidence = 1 - emotion_score
            else:
                emotion = "中性"
                confidence = 1 - abs(0.5 - emotion_score) * 2
            
            # 计算响应时间
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # 记录API调用（如果用户已认证）
            user_id = user.id
            if user_id:
                # 检查并扣减配额
                auth_service = AuthService()
                quota_valid, quota_msg = auth_service.check_user_quota(user)
                if not quota_valid:
                    return api_response(
                        code=403,
                        message=quota_msg
                    ), 403
                
                # 扣减配额
                auth_service.deduct_user_quota(user, 1)
                
                # 如果是通过API密钥认证的，也扣减API密钥的配额
                # 检查请求中是否包含API密钥
                api_key_value = None
                specific_api_key = None  # 初始化变量
                if 'X-API-Key' in request.headers:
                    api_key_value = request.headers.get('X-API-Key')
                elif 'api_key' in request.args:
                    api_key_value = request.args.get('api_key')
                elif 'api_key' in request.form:
                    api_key_value = request.form.get('api_key')
                
                # 如果使用了API密钥，则也扣减API密钥的配额
                if api_key_value:
                    api_key_record = auth_service.verify_api_key(api_key_value)
                    if api_key_record and hasattr(api_key_record, 'api_keys'):
                        # 获取对应的API密钥对象
                        specific_api_key = APIKey.query.filter_by(key=api_key_value, user_id=user.id).first()
                        if specific_api_key:
                            # 检查API密钥配额
                            if specific_api_key.quota_used >= specific_api_key.quota_total:
                                return api_response(
                                    code=403,
                                    message="API密钥配额已用完，请升级套餐或购买更多配额"
                                ), 403
                            # 扣减API密钥配额
                            auth_service.deduct_api_key_quota(specific_api_key, 1)
                
                # 记录API调用
                api_call = APICall()
                api_call.user_id = user_id
                api_call.api_key_id = specific_api_key.id if specific_api_key else None  # 添加API密钥ID
                api_call.endpoint = '/analyze'
                api_call.method = 'POST'
                api_call.response_status = 200
                api_call.response_time_ms = response_time
                api_call.ip_address = request.remote_addr
                api_call.user_agent = request.headers.get('User-Agent', '')
                api_call.quota_deducted = True
                api_call.batch_size = 1
                from src.database.manager import db
                db.session.add(api_call)
                db.session.commit()
            
            # 构造响应数据
            result = {
                'emotion_score': round(emotion_score, 6),
                'emotion': emotion,
                'confidence': round(confidence, 4),
                'text_length': len(text)
            }
            
            logger.info(f"[{request.remote_addr}] 情感分析完成 - 文本长度: {len(text)}, 情感分数: {emotion_score}")
            return api_response(data=result)
            
        except EmotionAnalysisError as e:
            logger.error(f"情感分析错误: {e}")
            return api_response(
                code=422,
                message="文本分析失败，请检查输入内容"
            ), 422
        except Exception as e:
            logger.error(f"未预期的错误: {e}", exc_info=True)
            return api_response(
                code=500,
                message="服务暂时异常，请稍后重试"
            ), 500
        finally:
            # 定期执行垃圾回收
            if int(time.time()) % 10 == 0:  # 每10秒执行一次
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"垃圾回收完成，清理对象数: {collected}")
    
    @api_bp.route('/batch', methods=['POST'])
    @validate_json
    @api_key_required
    def batch_analyze(user):
        """
        批量情感分析接口
        """
        try:
            # 记录请求开始时间
            start_time = time.time()
            
            # 获取请求数据
            data = request.get_json()
            texts = data.get('texts', [])
            
            # 验证输入
            if not isinstance(texts, list):
                return api_response(
                    code=400,
                    message="texts必须是数组格式"
                ), 400
            
            if len(texts) == 0:
                return api_response(
                    code=400,
                    message="texts数组不能为空"
                ), 400
            
            # 检查批量大小限制
            batch_limit = current_app.config.get('BATCH_SIZE_LIMIT', 100)
            if len(texts) > batch_limit:
                return api_response(
                    code=400,
                    message=f"批量处理文本数量不能超过{batch_limit}条"
                ), 400
            
            # 验证每个文本
            if emotion_analyzer:
                for i, text in enumerate(texts):
                    is_valid, error_msg = emotion_analyzer.validate_input(text)
                    if not is_valid:
                        return api_response(
                            code=400,
                            message=f"第{i+1}条文本错误: {error_msg.message if hasattr(error_msg, 'message') else str(error_msg)}"
                        ), 400
            else:
                for i, text in enumerate(texts):
                    if not text:
                        return api_response(
                            code=400,
                            message=f"第{i+1}条文本不能为空"
                        ), 400
            
            # 执行批量情感分析
            if emotion_analyzer:
                emotion_scores = emotion_analyzer.predict(texts)
                # 处理返回结果格式
                if isinstance(emotion_scores, list) and len(emotion_scores) > 0:
                    if isinstance(emotion_scores[0], list) and len(emotion_scores[0]) == 2:
                        # 格式为 [[text, score], ...]
                        emotion_scores = [score for _, score in emotion_scores]
            else:
                # 模拟分析结果（用于测试）
                emotion_scores = [0.5] * len(texts)
            
            # 处理结果
            results = []
            for i, (text, score) in enumerate(zip(texts, emotion_scores)):
                # 确定情感极性
                if score >= 0.6:
                    emotion = "正面"
                    confidence = score
                elif score <= 0.4:
                    emotion = "负面"
                    confidence = 1 - score
                else:
                    emotion = "中性"
                    confidence = 1 - abs(0.5 - score) * 2
                
                results.append({
                    'text': text,
                    'emotion_score': round(score, 6),
                    'emotion': emotion,
                    'confidence': round(confidence, 4),
                    'text_length': len(text)
                })
            
            # 计算响应时间
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # 记录API调用（如果用户已认证）
            user_id = user.id
            if user_id:
                # 检查并扣减配额
                auth_service = AuthService()
                quota_valid, quota_msg = auth_service.check_user_quota(user)
                if not quota_valid:
                    return api_response(
                        code=403,
                        message=quota_msg
                    ), 403
                
                # 扣减配额（批量处理按文本数量扣减）
                auth_service.deduct_user_quota(user, len(texts))
                
                # 如果是通过API密钥认证的，也扣减API密钥的配额
                # 检查请求中是否包含API密钥
                api_key_value = None
                specific_api_key = None  # 初始化变量
                if 'X-API-Key' in request.headers:
                    api_key_value = request.headers.get('X-API-Key')
                elif 'api_key' in request.args:
                    api_key_value = request.args.get('api_key')
                elif 'api_key' in request.form:
                    api_key_value = request.form.get('api_key')
                
                # 如果使用了API密钥，则也扣减API密钥的配额
                if api_key_value:
                    api_key_record = auth_service.verify_api_key(api_key_value)
                    if api_key_record and hasattr(api_key_record, 'api_keys'):
                        # 获取对应的API密钥对象
                        specific_api_key = APIKey.query.filter_by(key=api_key_value, user_id=user.id).first()
                        if specific_api_key:
                            # 检查API密钥配额
                            if specific_api_key.quota_used >= specific_api_key.quota_total:
                                return api_response(
                                    code=403,
                                    message="API密钥配额已用完，请升级套餐或购买更多配额"
                                ), 403
                            # 扣减API密钥配额（批量处理按文本数量扣减）
                            auth_service.deduct_api_key_quota(specific_api_key, len(texts))
                
                # 记录API调用
                api_call = APICall()
                api_call.user_id = user_id
                api_call.api_key_id = specific_api_key.id if specific_api_key else None  # 添加API密钥ID
                api_call.endpoint = '/batch'
                api_call.method = 'POST'
                api_call.response_status = 200
                api_call.response_time_ms = response_time
                api_call.ip_address = request.remote_addr
                api_call.user_agent = request.headers.get('User-Agent', '')
                api_call.quota_deducted = True
                api_call.batch_size = len(texts)
                from src.database.manager import db
                db.session.add(api_call)
                db.session.commit()
            
            # 构造响应数据
            result = {
                'results': results,
                'total_count': len(results)
            }
            
            logger.info(f"[{request.remote_addr}] 批量情感分析完成 - 文本数量: {len(texts)}")
            return api_response(data=result)
            
        except EmotionAnalysisError as e:
            logger.error(f"批量情感分析错误: {e}")
            return api_response(
                code=422,
                message="文本分析失败，请检查输入内容"
            ), 422
        except Exception as e:
            logger.error(f"未预期的错误: {e}", exc_info=True)
            return api_response(
                code=500,
                message="服务暂时异常，请稍后重试"
            ), 500
        finally:
            # 定期执行垃圾回收
            if int(time.time()) % 10 == 0:  # 每10秒执行一次
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"垃圾回收完成，清理对象数: {collected}")
    
    @api_bp.route('/segment', methods=['POST'])
    @validate_json
    @api_key_required
    def segment_text(user):
        """
        单文本分词接口
        """
        try:
            # 记录请求开始时间
            start_time = time.time()
            
            # 获取请求数据
            data = request.get_json()
            text = data.get('text', '')
            
            # 验证输入
            if not text:
                return api_response(
                    code=400,
                    message="文本不能为空"
                ), 400
            
            if not isinstance(text, str):
                return api_response(
                    code=400,
                    message="文本必须是字符串类型"
                ), 400
            
            # 执行文本分词
            if text_segmentor:
                segments = text_segmentor.segment(text)
            else:
                # 模拟分词结果（用于测试）
                segments = list(text)
            
            # 计算响应时间
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # 记录API调用（如果用户已认证）
            user_id = user.id
            if user_id:
                # 检查并扣减配额
                auth_service = AuthService()
                quota_valid, quota_msg = auth_service.check_user_quota(user)
                if not quota_valid:
                    return api_response(
                        code=403,
                        message=quota_msg
                    ), 403
                
                # 扣减配额
                auth_service.deduct_user_quota(user, 1)
                
                # 记录API调用
                api_call = APICall()
                api_call.user_id = user_id
                api_call.api_key_id = None  # 单文本分词接口暂不支持API密钥
                api_call.endpoint = '/segment'
                api_call.method = 'POST'
                api_call.response_status = 200
                api_call.response_time_ms = response_time
                api_call.ip_address = request.remote_addr
                api_call.user_agent = request.headers.get('User-Agent', '')
                api_call.quota_deducted = True
                api_call.batch_size = 1
                from src.database.manager import db
                db.session.add(api_call)
                db.session.commit()
            
            # 构造响应数据
            result = {
                'segments': segments,
                'segment_count': len(segments),
                'text_length': len(text)
            }
            
            logger.info(f"[{request.remote_addr}] 文本分词完成 - 文本长度: {len(text)}, 分词数量: {len(segments)}")
            return api_response(data=result)
            
        except Exception as e:
            logger.error(f"文本分词错误: {e}", exc_info=True)
            return api_response(
                code=500,
                message="服务暂时异常，请稍后重试"
            ), 500
        finally:
            # 定期执行垃圾回收
            if int(time.time()) % 10 == 0:  # 每10秒执行一次
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"垃圾回收完成，清理对象数: {collected}")
    
    @api_bp.route('/segment/batch', methods=['POST'])
    @validate_json
    @api_key_required
    def batch_segment(user):
        """
        批量文本分词接口
        """
        try:
            # 记录请求开始时间
            start_time = time.time()
            
            # 获取请求数据
            data = request.get_json()
            texts = data.get('texts', [])
            
            # 验证输入
            if not isinstance(texts, list):
                return api_response(
                    code=400,
                    message="texts必须是数组格式"
                ), 400
            
            if len(texts) == 0:
                return api_response(
                    code=400,
                    message="texts数组不能为空"
                ), 400
            
            # 检查批量大小限制
            batch_limit = current_app.config.get('BATCH_SIZE_LIMIT', 100)
            if len(texts) > batch_limit:
                return api_response(
                    code=400,
                    message=f"批量处理文本数量不能超过{batch_limit}条"
                ), 400
            
            # 验证每个文本
            for i, text in enumerate(texts):
                if not text:
                    return api_response(
                        code=400,
                        message=f"第{i+1}条文本不能为空"
                    ), 400
                
                if not isinstance(text, str):
                    return api_response(
                        code=400,
                        message=f"第{i+1}条文本必须是字符串类型"
                    ), 400
            
            # 执行批量文本分词
            results = []
            if text_segmentor:
                for text in texts:
                    segments = text_segmentor.segment(text)
                    results.append({
                        'text': text,
                        'segments': segments,
                        'segment_count': len(segments)
                    })
            else:
                # 模拟分词结果（用于测试）
                for text in texts:
                    segments = list(text)
                    results.append({
                        'text': text,
                        'segments': segments,
                        'segment_count': len(segments)
                    })
            
            # 计算响应时间
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # 记录API调用（如果用户已认证）
            user_id = user.id
            if user_id:
                # 检查并扣减配额
                auth_service = AuthService()
                quota_valid, quota_msg = auth_service.check_user_quota(user)
                if not quota_valid:
                    return api_response(
                        code=403,
                        message=quota_msg
                    ), 403
                
                # 扣减配额（批量处理按文本数量扣减）
                auth_service.deduct_user_quota(user, len(texts))
                
                # 记录API调用
                api_call = APICall()
                api_call.user_id = user_id
                api_call.api_key_id = None  # 批量文本分词接口暂不支持API密钥
                api_call.endpoint = '/segment/batch'
                api_call.method = 'POST'
                api_call.response_status = 200
                api_call.response_time_ms = response_time
                api_call.ip_address = request.remote_addr
                api_call.user_agent = request.headers.get('User-Agent', '')
                api_call.quota_deducted = True
                api_call.batch_size = len(texts)
                from src.database.manager import db
                db.session.add(api_call)
                db.session.commit()
            
            # 构造响应数据
            result = {
                'results': results,
                'total_count': len(results)
            }
            
            logger.info(f"[{request.remote_addr}] 批量文本分词完成 - 文本数量: {len(texts)}")
            return api_response(data=result)
            
        except Exception as e:
            logger.error(f"批量文本分词错误: {e}", exc_info=True)
            return api_response(
                code=500,
                message="服务暂时异常，请稍后重试"
            ), 500
        finally:
            # 定期执行垃圾回收
            if int(time.time()) % 10 == 0:  # 每10秒执行一次
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"垃圾回收完成，清理对象数: {collected}")
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)  # 确保认证路由正确注册
