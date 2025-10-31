# -*- coding: utf-8 -*-
"""
配额和系统配置模型
"""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint
from src.database.manager import db

class QuotaHistory(db.Model):
    """配额使用历史模型"""
    __tablename__ = 'quota_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    operation = db.Column(db.String(50), nullable=False)  # deduct, add, reset
    amount = db.Column(db.Integer, nullable=False)
    balance_before = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    
    user = db.relationship('User', backref=db.backref('quota_histories', lazy='dynamic'))
    
    def __repr__(self):
        return f'<QuotaHistory {self.user_id}:{self.operation}:{self.amount}>'


class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'
    
    def __repr__(self):
        return f'<SystemConfig {self.key}:{self.value}>'


class OperationLog(db.Model):
    """操作日志模型"""
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    
    user = db.relationship('User', backref=db.backref('operation_logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<OperationLog {self.action}:{self.resource_type}:{self.resource_id}>'


class JWTToken(db.Model):
    """JWT令牌模型"""
    __tablename__ = 'jwt_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)  # JWT ID
    token_type = db.Column(db.String(20), nullable=False)  # access or refresh
    revoked = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('tokens', lazy='dynamic'))
    
    __table_args__ = (
        CheckConstraint("token_type IN ('access', 'refresh')", name='check_token_type'),
    )
    
    def is_expired(self):
        """检查令牌是否过期"""
        return self.expires_at <= datetime.now(timezone.utc)
    
    def revoke(self):
        """撤销令牌"""
        self.revoked = True
    
    def __repr__(self):
        return f'<JWTToken {self.user_id}:{self.token_type}>'


# 初始化系统配置数据
def init_system_config():
    """初始化系统配置"""
    # 默认配置项
    default_configs = [
        {'key': 'free_quota', 'value': '1000', 'description': '免费用户默认配额'},
        {'key': 'system_status', 'value': 'active', 'description': '系统状态'},
        {'key': 'maintenance_mode', 'value': 'false', 'description': '维护模式'},
    ]
    
    for config_item in default_configs:
        existing = SystemConfig.query.filter_by(key=config_item['key']).first()
        if not existing:
            new_config = SystemConfig(
                key=config_item['key'],
                value=config_item['value'],
                description=config_item['description']
            )
            db.session.add(new_config)
    
    try:
        db.session.commit()
        print("✅ 系统配置初始化成功")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 系统配置初始化失败: {e}")
