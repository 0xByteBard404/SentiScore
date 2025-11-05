# -*- coding: utf-8 -*-
"""
鉴权服务类
"""
import re
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
import jwt
from sqlalchemy import or_
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.expression import ColumnElement
from src.database.manager import db
from src.models.user import User, Admin, UserPlan, APIKey
from src.models.quota import JWTToken, SystemConfig
from src.models.api import Plan, Order
from src.utils.helpers import validate_email, validate_password, create_success_response, create_error_response
from flask import Response


class AuthService:
    """鉴权服务类"""
    
    def __init__(self):
        self.access_token_expires = timedelta(minutes=30)
        self.refresh_token_expires = timedelta(days=30)
    
    def validate_username(self, username: str) -> bool:
        """验证用户名格式"""
        if not username:
            return False
        
        if len(username) < 3 or len(username) > 50:
            return False
        
        # 用户名只能包含字母、数字、下划线和连字符
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, username) is not None
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        return validate_email(email)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        return validate_password(password)
    
    def register_user(self, username: str, email: str, password: str, confirm_password: str) -> Response:
        """用户注册"""
        try:
            # 输入验证
            if not username or not email or not password or not confirm_password:
                return create_error_response("MISSING_FIELDS", "请填写所有必填字段")
            
            # 验证用户名
            if not self.validate_username(username):
                return create_error_response("INVALID_USERNAME", "用户名格式不正确，应为3-50位字母、数字、下划线或连字符")
            
            # 验证邮箱
            if not self.validate_email(email):
                return create_error_response("INVALID_EMAIL", "邮箱格式不正确")
            
            # 验证密码
            is_valid, message = self.validate_password_strength(password)
            if not is_valid:
                return create_error_response("WEAK_PASSWORD", message)
            
            # 确认密码
            if password != confirm_password:
                return create_error_response("PASSWORD_MISMATCH", "两次输入的密码不一致")
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                return create_error_response("USERNAME_EXISTS", "用户名已存在")
            
            # 检查邮箱是否已存在
            if User.query.filter_by(email=email).first():
                return create_error_response("EMAIL_EXISTS", "邮箱已被注册")
            
            # 创建用户
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.flush()  # 获取user.id但不提交事务
            
            # 为新用户创建默认API密钥
            api_key = APIKey(user_id=user.id, name='默认密钥')
            db.session.add(api_key)
            
            # 分配默认套餐
            free_plan = Plan.query.filter_by(name='Free').first()
            if free_plan:
                user_plan = UserPlan()
                user_plan.user_id = user.id
                user_plan.plan_id = free_plan.id  # 添加这行来设置plan_id
                user_plan.plan_name = free_plan.name
                user_plan.quota_total = free_plan.quota_total
                user_plan.quota_used = 0
                db.session.add(user_plan)
            
            db.session.commit()
            
            # 创建JWT令牌
            access_token = self.create_access_token(user)
            refresh_token = self.create_refresh_token(user)
            
            # 保存令牌到数据库
            self.save_token_to_db(user, access_token, 'access')
            self.save_token_to_db(user, refresh_token, 'refresh')
            
            return create_success_response({
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "message": "注册成功"
            })
            
        except Exception as e:
            db.session.rollback()
            return create_error_response("REGISTER_ERROR", f"注册失败: {str(e)}")
    
    def login_user(self, username: str, password: str, remember_me: bool = False) -> Response:
        """用户登录"""
        try:
            # 查找用户
            user = User.query.filter(
                or_(
                    User.username == username,  # type: ignore
                    User.email == username      # type: ignore
                )
            ).first()
            
            if not user:
                return create_error_response("INVALID_CREDENTIALS", "用户名或密码错误", 401)
            
            # 检查账户状态
            if user.status == 'disabled':
                return create_error_response("ACCOUNT_DISABLED", "账户已被禁用，请联系管理员", 403)
            
            if user.status == 'banned':
                return create_error_response("ACCOUNT_BANNED", "账户已被封禁", 403)
            
            # 检查账户锁定
            if user.is_locked():
                return create_error_response("ACCOUNT_LOCKED", "账户已被锁定，请稍后再试", 423)
            
            # 验证密码
            if not user.check_password(password):
                user.increment_login_attempts()
                db.session.commit()
                return create_error_response("INVALID_CREDENTIALS", "用户名或密码错误", 401)
            
            # 登录成功，重置失败次数
            user.reset_login_attempts()
            
            # 获取用户当前套餐
            current_plan = UserPlan.query.filter_by(user_id=user.id, is_active=True).first()
            
            # 生成JWT令牌
            access_token = self.create_access_token(user)
            refresh_token = self.create_refresh_token(user)
            
            # 保存令牌到数据库
            self.save_token_to_db(user, access_token, 'access')
            self.save_token_to_db(user, refresh_token, 'refresh')
            
            # 记录登录日志
            self.log_user_activity(user.id, 'login', request.remote_addr or '', str(request.user_agent))
            
            db.session.commit()
            
            return create_success_response({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(self.access_token_expires.total_seconds()),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "plan_name": current_plan.plan_name if current_plan else "Free",
                    "quota_remaining": current_plan.quota_remaining if current_plan else 0
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return create_error_response("LOGIN_ERROR", f"登录失败: {str(e)}", 500)
    
    def logout_user(self) -> Response:
        """用户登出"""
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return create_error_response("NOT_AUTHENTICATED", "用户未登录", 401)
            
            # 获取JWT标识符
            jti = get_jwt()["jti"]
            
            # 标记令牌为已撤销
            token = JWTToken.query.filter_by(jti=jti).first()
            if token:
                token.revoked = True
            
            # 记录登出日志
            self.log_user_activity(
                int(current_user_id), 
                'logout', 
                request.remote_addr or '', 
                str(request.user_agent) if request.user_agent else ''
            )
            
            db.session.commit()
            
            return create_success_response({"message": "登出成功"})
            
        except Exception as e:
            db.session.rollback()
            return create_error_response("LOGOUT_ERROR", f"登出失败: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> Response:
        """刷新访问令牌"""
        try:
            # 验证Refresh Token
            payload = jwt.decode(
                refresh_token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            user_id = payload.get('sub')
            token_type = payload.get('type')
            
            if token_type != 'refresh':
                return create_error_response("INVALID_TOKEN_TYPE", "无效的令牌类型", 401)
            
            user = User.query.get(user_id)
            if not user or user.status != 'active':
                return create_error_response("USER_NOT_FOUND", "用户不存在或已禁用", 401)
            
            # 检查令牌是否在数据库中且未撤销
            jti = payload.get('jti')
            token_hash = hashlib.sha256(jti.encode()).hexdigest()
            db_token = JWTToken.query.filter_by(
                token_hash=token_hash,
                token_type='refresh',
                revoked=False
            ).first()
            
            if not db_token:
                return create_error_response("TOKEN_REVOKED", "令牌已被撤销", 401)
            
            # 生成新的访问令牌
            access_token = self.create_access_token(user)
            self.save_token_to_db(user, access_token, 'access')
            
            db.session.commit()
            
            return create_success_response({
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": int(self.access_token_expires.total_seconds())
            })
            
        except jwt.ExpiredSignatureError:
            return create_error_response("TOKEN_EXPIRED", "令牌已过期", 401)
        except jwt.InvalidTokenError:
            return create_error_response("INVALID_TOKEN", "无效的令牌", 401)
        except Exception as e:
            db.session.rollback()
            return create_error_response("REFRESH_ERROR", f"刷新令牌失败: {str(e)}", 500)
    
    def change_password(self, current_password: str, new_password: str, confirm_password: str) -> Response:
        """修改密码"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在", 404)
            
            # 验证当前密码
            if not user.check_password(current_password):
                return create_error_response("INVALID_PASSWORD", "当前密码错误", 400)
            
            # 验证新密码
            valid_password, password_error = self.validate_password_strength(new_password)
            if not valid_password:
                return create_error_response("INVALID_PASSWORD", password_error, 400)
            
            if new_password != confirm_password:
                return create_error_response("PASSWORD_MISMATCH", "两次输入的新密码不一致", 400)
            
            # 设置新密码
            user.set_password(new_password)
            
            # 撤销所有现有令牌，强制重新登录
            JWTToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
            
            # 记录操作日志
            self.log_user_activity(
                user.id, 
                'change_password', 
                request.remote_addr or '', 
                str(request.user_agent) if request.user_agent else ''
            )
            
            db.session.commit()
            
            return create_success_response({"message": "密码修改成功，请重新登录"})
            
        except Exception as e:
            db.session.rollback()
            return create_error_response("CHANGE_PASSWORD_ERROR", f"修改密码失败: {str(e)}", 500)
    
    def verify_api_key(self, api_key: str) -> Optional[User]:
        """验证API Key"""
        try:
            if not api_key:
                return None
            
            # 首先检查用户表中的主API密钥
            user = User.query.filter_by(api_key=api_key, status='active').first()
            if user:
                return user
            
            # 然后检查API密钥表
            api_key_record = APIKey.query.filter_by(key=api_key, is_active=True).first()
            if api_key_record:
                return api_key_record.user
            
            return None
        except Exception:
            return None
    
    def get_api_key_info(self, user: User) -> Response:
        """获取API密钥信息"""
        try:
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在")
            
            # 获取用户当前套餐
            current_plan = UserPlan.query.filter_by(user_id=user.id, is_active=True).first()
            
            result = {
                "api_key": user.api_key,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            
            if current_plan:
                result['plan'] = {
                    'name': current_plan.plan_name,
                    'quota_total': current_plan.quota_total,
                    'quota_used': current_plan.quota_used,
                    'quota_remaining': current_plan.quota_remaining
                }
            else:
                result['plan'] = {
                    'name': 'Free',
                    'quota_total': 1000,
                    'quota_used': 0,
                    'quota_remaining': 1000
                }
            
            return create_success_response(result)
        except Exception as e:
            return create_error_response("GET_API_KEY_ERROR", f"获取API密钥信息失败: {str(e)}")

    def get_api_key(self, user_id: int, key_id: int) -> Response:
        """获取单个API密钥详情"""
        try:
            user = User.query.get(user_id)
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在")
            
            # 获取指定的API密钥（包含实际密钥值）
            api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
            if not api_key:
                return create_error_response("API_KEY_NOT_FOUND", "API密钥不存在")
            
            # 返回包含实际密钥的详细信息
            return create_success_response(api_key.to_detail_dict())
        except Exception as e:
            return create_error_response("GET_API_KEY_ERROR", f"获取API密钥详情失败: {str(e)}")

    def get_api_keys(self, user_id: int) -> Response:
        """获取用户的所有API密钥"""
        try:
            user = User.query.get(user_id)
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在")
            
            # 获取用户的所有API密钥（不包含实际密钥值）
            api_keys = APIKey.query.filter_by(user_id=user_id).all()
            api_keys_data = [key.to_dict() for key in api_keys]
            
            return create_success_response(api_keys_data)
        except Exception as e:
            return create_error_response("GET_API_KEYS_ERROR", f"获取API密钥列表失败: {str(e)}")

    def create_api_key(self, user_id: int, name: str, permissions: str = 'read,write', quota_total: Optional[int] = None) -> Response:
        """创建新的API密钥"""
        try:
            user = User.query.get(user_id)
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在")
            
            # 创建新的API密钥
            api_key = APIKey(user_id=user_id, name=name)
            api_key.permissions = permissions
            
            # 如果指定了配额总额，则设置配额
            if quota_total is not None:
                api_key.quota_total = quota_total
            
            db.session.add(api_key)
            db.session.commit()
            
            # 返回包含实际密钥的详细信息
            return create_success_response(api_key.to_detail_dict())
        except Exception as e:
            db.session.rollback()
            return create_error_response("CREATE_API_KEY_ERROR", f"创建API密钥失败: {str(e)}")
    
    def update_api_key(self, user_id: int, key_id: int, name: Optional[str] = None, 
                      permissions: Optional[str] = None, is_active: Optional[bool] = None,
                      quota_total: Optional[int] = None) -> Response:
        """更新API密钥"""
        try:
            # 获取API密钥
            api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
            if not api_key:
                return create_error_response("API_KEY_NOT_FOUND", "API密钥不存在")
            
            # 更新字段
            if name is not None:
                api_key.name = name
            if permissions is not None:
                api_key.permissions = permissions
            if is_active is not None:
                api_key.is_active = is_active
            if quota_total is not None:
                api_key.quota_total = quota_total
            
            api_key.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return create_success_response(api_key.to_dict())
        except Exception as e:
            db.session.rollback()
            return create_error_response("UPDATE_API_KEY_ERROR", f"更新API密钥失败: {str(e)}")
    
    def delete_api_key(self, user_id: int, key_id: int) -> Response:
        """删除API密钥"""
        try:
            # 检查是否是默认密钥
            api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
            if not api_key:
                return create_error_response("API_KEY_NOT_FOUND", "API密钥不存在")
            
            # 不允许删除用户主API密钥（与user.api_key关联的）
            user = User.query.get(user_id)
            if user and api_key.key == user.api_key:
                return create_error_response("DELETE_DEFAULT_KEY_ERROR", "不能删除默认API密钥")
            
            # 删除API密钥
            db.session.delete(api_key)
            db.session.commit()
            
            return create_success_response({"message": "API密钥删除成功"})
        except Exception as e:
            db.session.rollback()
            return create_error_response("DELETE_API_KEY_ERROR", f"删除API密钥失败: {str(e)}")

    def reset_api_key(self) -> Response:
        """重置API Key"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(int(current_user_id))
            
            if not user:
                return create_error_response("USER_NOT_FOUND", "用户不存在", 404)
            
            old_api_key = user.api_key
            user.api_key = user.generate_api_key()
            
            # 同时更新用户的默认API密钥记录
            default_api_key = APIKey.query.filter_by(user_id=user.id, name='默认密钥').first()
            if default_api_key:
                default_api_key.key = user.api_key
            else:
                # 如果不存在默认密钥记录，则创建一个
                default_api_key = APIKey(user_id=user.id, name='默认密钥')
                default_api_key.key = user.api_key
                db.session.add(default_api_key)
            
            # 记录操作日志
            self.log_user_activity(
                user.id, 
                'reset_api_key', 
                request.remote_addr or '', 
                str(request.user_agent) if request.user_agent else '',
                {
                    'old_api_key': old_api_key[:8] + '...',
                    'new_api_key': user.api_key[:8] + '...'
                }
            )
            
            db.session.commit()
            
            return create_success_response({
                "api_key": user.api_key,
                "message": "API Key重置成功，请妥善保管新的API Key"
            })
            
        except Exception as e:
            db.session.rollback()
            return create_error_response("RESET_API_KEY_ERROR", f"重置API Key失败: {str(e)}", 500)
    
    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        return create_access_token(
            identity=str(user.id),
            expires_delta=self.access_token_expires,
            additional_claims={
                'type': 'access',
                'username': user.username,
                'role': 'user'
            }
        )
    
    def create_refresh_token(self, user: User) -> str:
        """创建刷新令牌"""
        return create_refresh_token(
            identity=str(user.id),
            expires_delta=self.refresh_token_expires,
            additional_claims={
                'type': 'refresh',
                'username': user.username,
                'role': 'user'
            }
        )
    
    def save_token_to_db(self, user: User, token: str, token_type: str):
        """保存令牌到数据库"""
        try:
            # 解码JWT获取jti
            decoded_token = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            jti = decoded_token['jti']
            exp = datetime.fromtimestamp(decoded_token['exp'], tz=timezone.utc)
            
            # 创建令牌记录
            token_record = JWTToken()
            token_record.user_id = user.id
            token_record.jti = jti
            token_record.token_type = token_type
            token_record.expires_at = exp
            
            db.session.add(token_record)
            
        except Exception as e:
            print(f"保存令牌到数据库失败: {e}")

    def get_current_user(self) -> Optional[User]:
        """获取当前用户"""
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return None
            
            user = User.query.get(current_user_id)
            return user if user and user.status == 'active' else None
            
        except Exception:
            return None
    
    def is_admin(self, user: User) -> bool:
        """检查是否为管理员"""
        return Admin.query.filter_by(user_id=user.id, status='active').first() is not None
    
    def get_user_plan(self, user: User) -> Optional[UserPlan]:
        """获取用户当前套餐"""
        return UserPlan.query.filter_by(user_id=user.id, is_active=True).first()
    
    def check_user_quota(self, user: User) -> Tuple[bool, str]:
        """检查用户配额"""
        user_plan = self.get_user_plan(user)
        if not user_plan:
            return False, "用户没有有效的套餐"
        
        if user_plan.quota_remaining <= 0:
            return False, "配额已用完，请升级套餐"
        
        return True, ""
    
    def deduct_user_quota(self, user: User, amount: int = 1) -> bool:
        """扣减用户配额"""
        try:
            user_plan = self.get_user_plan(user)
            if user_plan:
                if user_plan.quota_total - user_plan.quota_used >= amount:
                    user_plan.quota_used += amount
                    success = True
                else:
                    success = False
            else:
                success = False

            if success:
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            print(f"扣减用户配额失败: {e}")
            db.session.rollback()
            return False
    
    def deduct_api_key_quota(self, api_key: APIKey, amount: int = 1) -> bool:
        """扣减API密钥配额"""
        try:
            if not api_key.is_active:
                return False

            # 扣减配额
            if hasattr(api_key, 'deduct_quota') and callable(api_key.deduct_quota):
                success = api_key.deduct_quota(amount)
            else:
                # 回退逻辑
                if api_key.quota_total - api_key.quota_used >= amount:
                    api_key.quota_used += amount
                    success = True
                else:
                    success = False

            if success:
                api_key.last_used_at = datetime.now(timezone.utc)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            print(f"扣减API密钥配额失败: {e}")
            db.session.rollback()
            return False
    
    def log_user_activity(self, user_id: int, action: str, ip_address: str = '', user_agent: str = '', details: Optional[Dict] = None):
        """记录用户活动"""
        try:
            from src.models.quota import OperationLog
            log_entry = OperationLog()
            log_entry.user_id = user_id
            log_entry.action = action
            log_entry.ip_address = ip_address
            log_entry.user_agent = user_agent[:255] if user_agent else None
            log_entry.details = details
            db.session.add(log_entry)
            # 注意：这里不提交事务，由调用者决定何时提交
        except Exception as e:
            print(f"记录用户活动失败: {e}")