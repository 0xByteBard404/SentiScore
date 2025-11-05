# -*- coding: utf-8 -*-
"""
认证相关路由
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from src.auth.service import AuthService
from src.auth.decorators import token_required
from src.models.user import User, Admin, APIKey
from src.utils.helpers import validate_email, validate_password, create_error_response
from src.database.manager import db

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 获取日志记录器
logger = logging.getLogger('SentiScore')

# 初始化认证服务
auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # 验证必填字段
        if not all([username, email, password, confirm_password]):
            return jsonify({'error': '所有字段都是必填的'}), 400
        
        # 验证邮箱格式
        if not validate_email(email):
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        # 验证密码强度
        password_error = validate_password(password)
        if password_error:
            return jsonify({'error': password_error}), 400
        
        # 验证密码匹配
        if password != confirm_password:
            return jsonify({'error': '两次输入的密码不一致'}), 400
        
        # 注册用户
        result = auth_service.register_user(username, email, password, confirm_password)
        # 直接返回Response对象
        return result
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"注册错误: {e}")
        return jsonify({'error': '注册失败，请稍后重试'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        # 验证必填字段
        if not all([username_or_email, password]):
            return jsonify({'error': '用户名/邮箱和密码都是必填的'}), 400
        
        # 用户认证
        result = auth_service.login_user(username_or_email, password)
        # 直接返回Response对象
        return result
        
    except Exception as e:
        logger.error(f"登录错误: {e}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        # 在实际应用中，应将jti添加到黑名单中
        logger.info(f"用户登出成功")
        return jsonify({'message': '登出成功'}), 200
    except Exception as e:
        logger.error(f"登出错误: {e}")
        return jsonify({'error': '登出失败，请稍后重试'}), 500


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_user_profile(user):
    """获取用户信息"""
    try:
        return jsonify({
            'data': user.to_public_dict()
        }), 200
    except Exception as e:
        logger.error(f"获取用户信息错误: {e}")
        return jsonify({'error': '获取用户信息失败'}), 500


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_user_profile(user):
    """更新用户信息"""
    try:
        data = request.get_json()
        
        # 更新用户名
        if 'username' in data:
            username = data['username']
            # 验证用户名格式
            if len(username) < 3 or len(username) > 50:
                return jsonify({'error': '用户名长度应在3-50个字符之间'}), 400
            
            # 检查用户名是否已存在（排除当前用户）
            existing_user = User.query.filter(
                User.username == username,
                User.id != user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': '用户名已存在'}), 400
                
            user.username = username
        
        # 更新邮箱
        if 'email' in data:
            email = data['email']
            # 验证邮箱格式
            if not validate_email(email):
                return jsonify({'error': '邮箱格式不正确'}), 400
                
            # 检查邮箱是否已存在（排除当前用户）
            existing_user = User.query.filter(
                User.email == email,
                User.id != user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': '邮箱已被注册'}), 400
                
            user.email = email
        
        # 如果有密码字段，处理密码修改
        if 'old_password' in data and 'new_password' in data:
            old_password = data['old_password']
            new_password = data['new_password']
            confirm_password = data.get('confirm_password', new_password)
            
            # 验证当前密码
            if not user.check_password(old_password):
                return jsonify({'error': '当前密码错误'}), 400
            
            # 验证新密码
            password_valid, password_error = validate_password(new_password)
            if not password_valid:
                return jsonify({'error': password_error}), 400
            
            # 验证确认密码
            if new_password != confirm_password:
                return jsonify({'error': '两次输入的新密码不一致'}), 400
            
            # 设置新密码
            user.set_password(new_password)
            
            # 撤销所有现有令牌，强制重新登录
            from src.models.quota import JWTToken
            JWTToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
            
            # 记录操作日志
            auth_service.log_user_activity(
                user.id, 
                'change_password', 
                request.remote_addr or '', 
                str(request.user_agent) if request.user_agent else ''
            )
            
            db.session.commit()
            
            return jsonify({
                'message': '密码修改成功，请重新登录',
                'require_relogin': True
            }), 200
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'data': user.to_public_dict(),
            'message': '用户信息更新成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新用户信息错误: {e}")
        return jsonify({'error': '更新用户信息失败'}), 500


@auth_bp.route('/api-keys', methods=['GET'])
@token_required
def get_all_api_keys(user):
    """获取所有API密钥"""
    try:
        # 获取用户的所有API密钥
        result = auth_service.get_api_keys(user.id)
        # 直接返回Response对象
        return result
    except Exception as e:
        logger.error(f"获取API密钥列表失败: {e}")
        return jsonify({'error': '获取API密钥列表失败'}), 500


@auth_bp.route('/api-keys', methods=['POST'])
@token_required
def create_api_key(user):
    """创建新的API密钥"""
    try:
        data = request.get_json()
        name = data.get('name', '默认密钥')
        permissions = data.get('permissions', 'read,write')
        quota_total = data.get('quota_total')
        
        # 创建新的API密钥
        result = auth_service.create_api_key(user.id, name, permissions, quota_total)
        # 直接返回Response对象
        return result
    except Exception as e:
        logger.error(f"创建API密钥失败: {e}")
        return jsonify({'error': '创建API密钥失败'}), 500


@auth_bp.route('/api-keys/<int:key_id>', methods=['PUT'])
@token_required
def update_api_key(user, key_id):
    """更新API密钥"""
    try:
        data = request.get_json()
        name = data.get('name')
        permissions = data.get('permissions')
        is_active = data.get('is_active')
        quota_total = data.get('quota_total')
        
        # 更新API密钥
        result = auth_service.update_api_key(user.id, key_id, name, permissions, is_active, quota_total)
        # 直接返回Response对象
        return result
    except Exception as e:
        logger.error(f"更新API密钥失败: {e}")
        return jsonify({'error': '更新API密钥失败'}), 500


@auth_bp.route('/api-keys/<int:key_id>', methods=['GET'])
@token_required
def get_api_key(user, key_id):
    """获取单个API密钥详情"""
    try:
        # 获取指定的API密钥
        result = auth_service.get_api_key(user.id, key_id)
        # 直接返回Response对象
        return result
    except Exception as e:
        logger.error(f"获取API密钥详情失败: {e}")
        return jsonify({'error': '获取API密钥详情失败'}), 500


@auth_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@token_required
def delete_api_key(user, key_id):
    """删除API密钥"""
    try:
        # 删除API密钥
        result = auth_service.delete_api_key(user.id, key_id)
        # 直接返回Response对象
        return result
    except Exception as e:
        logger.error(f"删除API密钥失败: {e}")
        return jsonify({'error': '删除API密钥失败'}), 500


@auth_bp.route('/statistics', methods=['GET'])
@token_required
def get_user_statistics(user):
    """获取用户统计信息"""
    try:
        from src.models.api import APICall
        from src.models.user import UserPlan, User
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import func, and_
        
        # 获取查询参数
        period = request.args.get('period', 'week')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 设置北京时间时区
        beijing_tz = timezone(timedelta(hours=8))
        
        # 设置默认时间范围（使用北京时间）
        if not end_date:
            end_date = datetime.now(beijing_tz)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=beijing_tz)
            # 将结束日期设置为当天的结束时间（23:59:59）
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        if not start_date:
            if period == 'day':
                start_date = end_date - timedelta(days=1)
            elif period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(weeks=1)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=beijing_tz)
            # 将开始日期设置为当天的开始时间（00:00:00）
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 确保时间范围正确（start_date应该在end_date之前）
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        # 转换为UTC时间用于数据库查询
        start_date_utc = start_date.astimezone(timezone.utc)
        end_date_utc = end_date.astimezone(timezone.utc)
        
        # 检查是否为管理员
        from src.auth.service import AuthService
        auth_service = AuthService()
        is_admin_user = auth_service.is_admin(user)
        
        # 总API密钥数（默认为0，管理员时会更新）
        total_api_keys = 0
        
        if is_admin_user:
            # 管理员查询所有用户的统计信息
            calls_query = APICall.query.filter(
                and_(
                    APICall.created_at >= start_date_utc,
                    APICall.created_at <= end_date_utc,
                    APICall.quota_deducted == True  # 只统计成功扣减配额的调用
                )
            )
            
            # 总API密钥数
            total_api_keys = APIKey.query.count()
        else:
            # 普通用户只查询自己的统计信息
            calls_query = APICall.query.filter(
                and_(
                    APICall.user_id == user.id,
                    APICall.created_at >= start_date_utc,
                    APICall.created_at <= end_date_utc,
                    APICall.quota_deducted == True  # 只统计成功扣减配额的调用
                )
            )
        
        # 总调用次数（成功扣减配额的调用）
        total_calls = calls_query.count()
        
        # 成功调用次数
        successful_calls = calls_query.filter(APICall.response_status == 200).count()
        
        # 失败调用次数
        failed_calls = total_calls - successful_calls
        
        # 平均响应时间
        avg_response_time = calls_query.with_entities(
            func.avg(APICall.response_time_ms)
        ).scalar() or 0
        
        # 按日期统计调用次数（只统计成功扣减配额的调用）
        daily_calls = []
        
        # 生成完整日期范围（包含所有日期，使用北京时间）
        date_range = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        # 确保包含结束日期
        while current_date <= end_date_only:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # 查询数据库中的统计数据（使用UTC时间进行分组，但转换为北京时间显示）
        if period in ['day', 'week']:
            date_format = '%Y-%m-%d'
            # 使用UTC时间进行分组，但转换为北京时间
            date_group = func.date(func.datetime(APICall.created_at, '+8 hours'))
        else:
            date_format = '%Y-%m'
            # 使用UTC时间进行分组，但转换为北京时间
            date_group = func.strftime('%Y-%m', func.datetime(APICall.created_at, '+8 hours'))
            
        daily_stats = calls_query.with_entities(
            date_group.label('date'),
            func.count(APICall.id).label('count')
        ).group_by(date_group).all()
        
        # 创建日期统计数据字典
        stats_dict = {str(stat.date): stat.count for stat in daily_stats}
        
        # 填充完整日期范围的数据
        daily_calls = []
        for date_str in date_range:
            daily_calls.append({
                'date': date_str,
                'count': stats_dict.get(date_str, 0)
            })
        
        # 按端点统计使用情况（只统计成功扣减配额的调用）
        endpoint_usage = calls_query.with_entities(
            APICall.endpoint,
            func.count(APICall.id).label('count')
        ).group_by(APICall.endpoint).all()
        
        endpoint_usage = [{'endpoint': usage.endpoint, 'count': usage.count} for usage in endpoint_usage]
        
        # 获取用户当前套餐信息
        current_plan = UserPlan.query.filter_by(user_id=user.id, is_active=True).first()
        
        # 添加调试信息
        logger.info(f"用户 {user.id} 统计数据:")
        logger.info(f"  时间范围: {start_date} 到 {end_date}")
        logger.info(f"  UTC时间范围: {start_date_utc} 到 {end_date_utc}")
        logger.info(f"  总调用次数: {total_calls}")
        logger.info(f"  成功调用次数: {successful_calls}")
        logger.info(f"  失败调用次数: {failed_calls}")
        logger.info(f"  每日调用统计: {daily_calls}")
        logger.info(f"  端点使用情况: {endpoint_usage}")
        
        response_data = {
            'data': {
                'period': period,
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                },
                'summary': {
                    'total_calls': total_calls,
                    'successful_calls': successful_calls,
                    'failed_calls': failed_calls,
                    'avg_response_time': round(float(avg_response_time), 2)
                },
                'daily_calls': daily_calls,
                'endpoint_usage': endpoint_usage
            }
        }
        
        # 如果是管理员，添加额外信息
        if is_admin_user:
            response_data['data']['total_api_keys'] = total_api_keys
            response_data['data']['plan_info'] = {
                'name': 'Administrator',
                'quota_total': 0,
                'quota_used': 0,
                'quota_remaining': 0
            }
        elif current_plan:
            response_data['data']['plan_info'] = {
                'name': current_plan.plan_name if current_plan else 'Free',
                'quota_total': current_plan.quota_total if current_plan else 1000,
                'quota_used': current_plan.quota_used if current_plan else 0,
                'quota_remaining': current_plan.quota_remaining if current_plan else 1000
            }
        else:
            response_data['data']['plan_info'] = {
                'name': 'Free',
                'quota_total': 1000,
                'quota_used': 0,
                'quota_remaining': 1000
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"获取用户统计信息错误: {e}")
        return jsonify({'error': '获取用户统计信息失败'}), 500


@auth_bp.route('/calls/history', methods=['GET'])
@token_required
def get_api_call_history(user):
    """获取API调用历史记录"""
    try:
        from src.models.api import APICall
        from flask import request
        from sqlalchemy import desc
        from src.utils.helpers import format_datetime_for_api
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        # 获取过滤参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        endpoint = request.args.get('endpoint')
        
        # 构建查询
        query = APICall.query.filter(APICall.user_id == user.id)
        
        # 添加日期过滤
        if start_date:
            from datetime import datetime, timezone
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            query = query.filter(APICall.created_at >= start_dt)
            
        if end_date:
            from datetime import datetime, timezone
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            query = query.filter(APICall.created_at <= end_dt)
            
        if endpoint:
            query = query.filter(APICall.endpoint == endpoint)
        
        # 执行分页查询
        pagination = query.order_by(desc(APICall.created_at)).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        calls = pagination.items
        total = pagination.total
        total_pages = pagination.pages
        
        # 转换为字典格式
        calls_data = []
        for call in calls:
            call_dict = call.to_dict() if hasattr(call, 'to_dict') else {
                'id': call.id,
                'user_id': call.user_id,
                'endpoint': call.endpoint,
                'method': call.method,
                'response_status': call.response_status,
                'response_time_ms': call.response_time_ms,
                'ip_address': call.ip_address,
                'user_agent': call.user_agent,
                'created_at': format_datetime_for_api(call.created_at)
            }
            calls_data.append(call_dict)
        
        return jsonify({
            'data': {
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'calls': calls_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取API调用历史记录错误: {e}")
        return jsonify({'error': '获取API调用历史记录失败'}), 500


@auth_bp.route('/orders', methods=['GET'])
@token_required
def get_order_history(user):
    """获取订单历史记录"""
    try:
        # 修复导入错误，从正确的模块导入Order
        from src.models.api import Order
        from flask import request
        from sqlalchemy import desc
        from src.utils.helpers import format_datetime_for_api
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        # 获取过滤参数
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = Order.query.filter(Order.user_id == user.id)
        
        # 添加状态过滤
        if status:
            query = query.filter(Order.status == status)
            
        # 添加日期过滤
        if start_date:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_dt)
            
        if end_date:
            from datetime import datetime
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Order.created_at <= end_dt)
        
        # 执行分页查询
        pagination = query.order_by(desc(Order.created_at)).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        orders = pagination.items
        total = pagination.total
        total_pages = pagination.pages
        
        # 转换为字典格式
        orders_data = []
        for order in orders:
            order_dict = order.to_dict() if hasattr(order, 'to_dict') else {
                'id': order.id,
                'order_no': order.order_no,
                'user_id': order.user_id,
                'plan_id': order.plan_id,
                'plan_name': order.plan_name,
                'amount': float(order.amount),
                'status': order.status,
                'created_at': format_datetime_for_api(order.created_at),
                'paid_at': format_datetime_for_api(order.paid_at) if order.paid_at else None,
                'refunded_at': format_datetime_for_api(order.refunded_at) if order.refunded_at else None
            }
            orders_data.append(order_dict)
        
        return jsonify({
            'data': {
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'orders': orders_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取订单历史记录错误: {e}")
        return jsonify({'error': '获取订单历史记录失败'}), 500

# 错误处理
@auth_bp.errorhandler(400)
def bad_request(error):
    return create_error_response("BAD_REQUEST", "请求格式错误", 400)

@auth_bp.errorhandler(401)
def unauthorized(error):
    return create_error_response("UNAUTHORIZED", "未授权访问", 401)

@auth_bp.errorhandler(403)
def forbidden(error):
    return create_error_response("FORBIDDEN", "访问被禁止", 403)

@auth_bp.errorhandler(404)
def not_found(error):
    return create_error_response("NOT_FOUND", "资源不存在", 404)

@auth_bp.errorhandler(500)
def internal_error(error):
    return create_error_response("INTERNAL_ERROR", "服务器内部错误", 500)