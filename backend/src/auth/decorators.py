# -*- coding: utf-8 -*-
"""
鉴权装饰器
"""
from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.auth.service import AuthService
from src.models.user import User, Admin
from src.utils.helpers import create_error_response

auth_service = AuthService()

def token_required(f):
    """要求用户登录的装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return create_error_response("MISSING_USER_ID", "用户ID缺失", 401)
            
            # 确保用户ID是整数类型
            user = User.query.get(int(current_user_id))
            
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在", 404)
            
            if user.status != 'active':
                return create_error_response("ACCOUNT_INACTIVE", "账户已被禁用", 403)
            
            return f(user=user, *args, **kwargs)
        except ValueError as e:
            return create_error_response("INVALID_USER_ID", "无效的用户ID", 401)
        except Exception as e:
            return create_error_response("AUTH_ERROR", f"认证错误: {str(e)}", 500)
    
    return decorated_function

def admin_required(f):
    """要求管理员权限的装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return create_error_response("USER_NOT_FOUND", "用户不存在", 404)
        
        if user.status != 'active':
            return create_error_response("ACCOUNT_INACTIVE", "账户已被禁用", 403)
        
        # 检查管理员权限
        admin = Admin.query.filter_by(user_id=user.id, status='active').first()
        if not admin:
            return create_error_response("ADMIN_REQUIRED", "需要管理员权限", 403)
        
        return f(user=user, admin=admin, *args, **kwargs)
    
    return decorated_function

def api_key_required(f):
    """要求API Key的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取API Key
        api_key = None
        
        # 优先级：Header > Query Parameter > Form Data
        if 'X-API-Key' in request.headers:
            api_key = request.headers.get('X-API-Key')
        elif 'api_key' in request.args:
            api_key = request.args.get('api_key')
        elif 'api_key' in request.form:
            api_key = request.form.get('api_key')
        
        if not api_key:
            return create_error_response("API_KEY_REQUIRED", "缺少API Key", 401)
        
        # 验证API Key
        user = auth_service.verify_api_key(api_key)
        if not user:
            return create_error_response("INVALID_API_KEY", "无效的API Key", 401)
        
        # 如果使用的是API密钥表中的密钥，则更新最后使用时间
        from src.models.user import APIKey
        api_key_record = APIKey.query.filter_by(key=api_key, is_active=True).first()
        if api_key_record:
            from datetime import datetime, timezone
            api_key_record.last_used_at = datetime.now(timezone.utc)
            from src.database.manager import db
            db.session.commit()
        
        return f(user=user, *args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """可选认证装饰器（有token则验证，无token则跳过）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = None
        
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                current_user = User.query.get(int(current_user_id))
        except:
            # 未提供token或token无效，跳过认证
            pass
        
        return f(user=current_user, *args, **kwargs)
    
    return decorated_function

def rate_limit_by_user(f):
    """基于用户的频率限制装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从装饰器参数中获取用户
        user = None
        if 'user' in kwargs:
            user = kwargs['user']
        
        if not user:
            return create_error_response("USER_REQUIRED", "需要用户信息进行频率限制", 400)
        
        # 检查用户配额
        can_proceed, error_message = auth_service.check_user_quota(user)
        if not can_proceed:
            return create_error_response("QUOTA_EXCEEDED", error_message, 429)
        
        # 检查频率限制
        from flask_limiter import RateLimit
        from flask import current_app
        
        rate_limit = auth_service.get_rate_limit(user)
        limit_key = f"user_{user.id}"
        
        # 这里可以实现更细粒度的频率限制逻辑
        # 例如基于IP、端点等的组合限制
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_plan(plan_name):
    """要求特定套餐的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = kwargs.get('user')
            if not user:
                return create_error_response("USER_REQUIRED", "需要用户信息", 400)
            
            user_plan = auth_service.get_user_plan(user)
            if not user_plan or user_plan.plan_name != plan_name:
                return create_error_response("PLAN_REQUIRED", f"需要{plan_name}套餐", 403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_min_plan(min_plan_name):
    """要求最小套餐等级的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = kwargs.get('user')
            if not user:
                return create_error_response("USER_REQUIRED", "需要用户信息", 400)
            
            user_plan = auth_service.get_user_plan(user)
            if not user_plan:
                return create_error_response("NO_PLAN", "用户没有套餐", 403)
            
            # 套餐等级映射
            plan_levels = {
                'Free': 0,
                'Basic': 1,
                'Professional': 2,
                'Pro': 2,
                'Enterprise': 3
            }
            
            user_level = plan_levels.get(user_plan.plan_name, 0)
            required_level = plan_levels.get(min_plan_name, 0)
            
            if user_level < required_level:
                return create_error_response("PLAN_LEVEL_INSUFFICIENT", 
                                          f"需要{min_plan_name}或更高套餐", 403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_user_activity(action):
    """记录用户活动的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = kwargs.get('user')
            if user:
                auth_service.log_user_activity(
                    user.id, 
                    action, 
                    request.remote_addr, 
                    request.user_agent
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_json(required_fields=None):
    """验证JSON请求体的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 对于GET请求，不需要验证JSON
            if request.method == 'GET':
                return f(*args, **kwargs)
            
            if not request.is_json:
                return create_error_response("INVALID_CONTENT_TYPE", "请求必须是JSON格式", 400)
            
            data = request.get_json()
            if data is None:
                return create_error_response("INVALID_JSON", "无效的JSON格式", 400)
            
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    return create_error_response("MISSING_FIELDS", 
                                              f"缺少必填字段: {', '.join(missing_fields)}", 400)
            
            kwargs['request_data'] = data
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def cache_control(max_age=3600, public=True):
    """控制缓存的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # 如果返回的是字典，转换为JSON响应
            if isinstance(response, dict):
                from flask import jsonify
                response = jsonify(response)
            
            # 设置缓存头
            cache_directive = f"public, max-age={max_age}" if public else "private, no-cache"
            response.headers['Cache-Control'] = cache_directive
            
            return response
        
        return decorated_function
    return decorator

def cors_origins(origins=None):
    """CORS支持的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # 如果没有指定来源，使用请求的Origin
            if not origins:
                origins = [request.headers.get('Origin', '*')]
            
            from flask import make_response
            if isinstance(response, dict):
                from flask import jsonify
                response = jsonify(response)
            
            response.headers['Access-Control-Allow-Origin'] = ', '.join(origins)
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response
        
        return decorated_function
    return decorator

# 预定义的装饰器组合
api_required = [api_key_required, rate_limit_by_user, log_user_activity('api_call')]
user_required = [token_required, log_user_activity('user_action')]
admin_required_decorators = [admin_required, log_user_activity('admin_action')]
