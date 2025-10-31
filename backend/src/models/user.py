# -*- coding: utf-8 -*-
"""
用户模型
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from src.database.manager import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(64), unique=True, index=True)  # 主API密钥
    status = db.Column(db.String(20), default='active', index=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(255))
    
    # 约束
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled', 'banned')", name='check_user_status'),
    )
    
    def __init__(self, username: str, email: str, password: str):
        """初始化用户"""
        self.username = username
        self.email = email.lower()
        self.set_password(password)
        self.api_key = self.generate_api_key()
    
    def generate_api_key(self) -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(32)
    
    def get_primary_api_key(self):
        """获取用户的主API密钥（第一个有效密钥）"""
        return self.api_keys.filter_by(is_active=True).first()
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if not self.locked_until:
            return False
        return self.locked_until > datetime.now(timezone.utc)
    
    def increment_login_attempts(self):
        """增加登录失败次数"""
        self.login_attempts += 1
        if self.login_attempts >= 5:  # 5次失败后锁定
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def reset_login_attempts(self):
        """重置登录失败次数"""
        self.login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'status': self.status,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_attempts': self.login_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'two_factor_enabled': self.two_factor_enabled
        }
    
    def to_public_dict(self):
        """转换为公共信息字典（不包含敏感信息）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'status': self.status,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class APIKey(db.Model):
    """API密钥模型"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default='默认密钥')
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    permissions = db.Column(db.String(200), default='read,write')  # 权限列表
    is_active = db.Column(db.Boolean, default=True)
    quota_total = db.Column(db.Integer, default=1000)  # 总配额
    quota_used = db.Column(db.Integer, default=0)  # 已使用配额
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 添加约束：配额范围检查
    __table_args__ = (
        CheckConstraint('quota_total >= 1 AND quota_total <= 10000000000', name='check_quota_total_range'),
        CheckConstraint('quota_used >= 0', name='check_quota_used_non_negative'),
    )
    
    user = db.relationship('User', backref=db.backref('api_keys', lazy='dynamic'))
    
    def __init__(self, user_id: int, name: str = '默认密钥'):
        """初始化API密钥"""
        self.user_id = user_id
        self.name = name
        self.key = self.generate_key()
    
    def generate_key(self) -> str:
        """生成API密钥"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def to_dict(self):
        """转换为字典格式（不包含实际密钥）"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'quota_total': self.quota_total,
            'quota_used': self.quota_used,
            'quota_remaining': self.quota_total - self.quota_used,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_detail_dict(self):
        """转换为详细字典格式（包含实际密钥）"""
        result = self.to_dict()
        result['key'] = self.key
        return result
    
    def deduct_quota(self, amount: int = 1):
        """扣减密钥配额"""
        if self.quota_total - self.quota_used >= amount:
            self.quota_used += amount
            return True
        return False
    
    def reset_quota(self):
        """重置密钥配额"""
        self.quota_used = 0
    
    def __repr__(self):
        return f'<APIKey {self.name}:{self.user_id}>'


class Admin(db.Model):
    """管理员模型"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), default='admin', index=True)
    permissions = db.Column(db.JSON, default={})
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    
    # 约束
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'super_admin')", name='check_admin_role'),
        CheckConstraint("status IN ('active', 'disabled')", name='check_admin_status'),
    )
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('admin', uselist=False))
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'permissions': self.permissions,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def __repr__(self):
        return f'<Admin {self.user_id}:{self.role}>'


class UserPlan(db.Model):
    """用户套餐模型"""
    __tablename__ = 'user_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_name = db.Column(db.String(50), nullable=False, index=True)
    plan_type = db.Column(db.String(20), default='subscription')
    quota_total = db.Column(db.Integer, nullable=False, default=1000)
    quota_used = db.Column(db.Integer, default=0)
    reset_period = db.Column(db.String(20), default='monthly')
    reset_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    auto_renew = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 计算字段：剩余额度
    quota_remaining = db.Column(db.Integer, default=1000)
    
    # 约束
    __table_args__ = (
        CheckConstraint("plan_type IN ('free', 'subscription', 'pay_per_use')", name='check_plan_type'),
        CheckConstraint("reset_period IN ('daily', 'weekly', 'monthly', 'yearly')", name='check_reset_period'),
    )
    
    user = db.relationship('User', backref=db.backref('plans', lazy='dynamic'))
    
    def deduct_quota(self, amount: int = 1, reason: str = "API调用扣减"):
        """扣减用户配额"""
        if self.quota_remaining >= amount:
            self.quota_used += amount
            self.quota_remaining -= amount
            
            # 记录配额扣减日志
            from src.models.quota import QuotaHistory
            quota_log = QuotaHistory(
                user_id=self.user_id,
                operation="deduct",
                amount=-amount,
                balance_before=self.quota_used - amount,
                balance_after=self.quota_used,
                description=reason
            )
            from src.database.manager import db
            db.session.add(quota_log)
            return True
        return False
    
    def reset_quota(self):
        """重置配额"""
        old_quota_used = self.quota_used
        self.quota_used = 0
        self.quota_remaining = self.quota_total
        
        # 记录配额重置日志
        from src.models.quota import QuotaHistory
        quota_log = QuotaHistory(
            user_id=self.user_id,
            operation="reset",
            amount=self.quota_total,
            balance_before=old_quota_used,
            balance_after=0,
            description="配额周期重置"
        )
        from src.database.manager import db
        db.session.add(quota_log)