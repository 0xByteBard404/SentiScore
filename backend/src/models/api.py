# -*- coding: utf-8 -*-
"""
API相关模型
"""
from datetime import datetime, timezone
from sqlalchemy import func, CheckConstraint
from src.database.manager import db

class APICall(db.Model):
    """API调用记录模型"""
    __tablename__ = 'api_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id', ondelete='SET NULL'), nullable=True)  # 关联的API密钥ID
    endpoint = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    request_data = db.Column(db.JSON)
    response_data = db.Column(db.JSON)
    response_status = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Integer)  # 响应时间（毫秒）
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    batch_size = db.Column(db.Integer, default=1)  # 批量处理大小
    quota_deducted = db.Column(db.Boolean, default=False)  # 是否扣减配额
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    
    user = db.relationship('User', backref=db.backref('api_calls', lazy='dynamic'))
    api_key = db.relationship('APIKey', backref=db.backref('api_calls', lazy='dynamic'))  # API密钥关系
    
    def __repr__(self):
        return f'<APICall {self.user_id}:{self.endpoint}:{self.response_status}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'api_key_id': self.api_key_id,
            'api_key_name': self.api_key.name if self.api_key else None,
            'endpoint': self.endpoint,
            'method': self.method,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'batch_size': self.batch_size,
            'quota_deducted': self.quota_deducted,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Plan(db.Model):
    """套餐模型"""
    __tablename__ = 'plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(500))
    quota_total = db.Column(db.Integer, nullable=False)  # 总配额
    price = db.Column(db.Numeric(10, 2), nullable=False)  # 价格
    duration_days = db.Column(db.Integer)  # 有效期（天）
    max_requests_per_minute = db.Column(db.Integer, default=100)  # 每分钟最大请求数
    features = db.Column(db.JSON, default=[])  # 功能列表
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'quota_total': self.quota_total,
            'price': float(self.price),
            'duration_days': self.duration_days,
            'max_requests_per_minute': self.max_requests_per_minute,
            'features': self.features,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Plan {self.name}:{self.price}>'


class Order(db.Model):
    """订单模型"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    order_no = db.Column(db.String(32), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, cancelled, refunded
    payment_method = db.Column(db.String(20))  # alipay, wechat, stripe, etc.
    payment_id = db.Column(db.String(100))  # 第三方支付ID
    paid_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    refunded_at = db.Column(db.DateTime)
    refund_amount = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('orders', lazy='dynamic'))
    plan = db.relationship('Plan')
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'paid', 'cancelled', 'refunded')", name='check_order_status'),
    )
    
    def generate_order_no(self):
        """生成订单号"""
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.order_no = f"ORD{timestamp}{random_str}"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_no': self.order_no,
            'plan_id': self.plan_id,
            'amount': float(self.amount),
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_id': self.payment_id,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Order {self.order_no}:{self.status}>'


# 初始化默认套餐数据
def init_default_plans():
    """初始化默认套餐"""
    default_plans = [
        {
            'name': 'Free',
            'description': '免费套餐，适合个人开发者和小规模测试',
            'quota_total': 1000,
            'price': 0,
            'duration_days': 30,
            'max_requests_per_minute': 10,
            'features': ['基础情感分析', 'API访问', '社区支持'],
            'sort_order': 0
        },
        {
            'name': 'Basic',
            'description': '基础套餐，适合小型项目和初创企业',
            'quota_total': 10000,
            'price': 29.99,
            'duration_days': 30,
            'max_requests_per_minute': 100,
            'features': ['基础情感分析', '批量处理(10条)', 'API访问', '邮箱支持'],
            'sort_order': 1
        },
        {
            'name': 'Professional',
            'description': '专业套餐，适合中型企业项目',
            'quota_total': 100000,
            'price': 99.99,
            'duration_days': 30,
            'max_requests_per_minute': 500,
            'features': ['基础情感分析', '批量处理(100条)', 'API访问', '优先支持', '自定义模型'],
            'sort_order': 2
        },
        {
            'name': 'Enterprise',
            'description': '企业套餐，适合大型企业和高并发场景',
            'quota_total': 1000000,
            'price': 299.99,
            'duration_days': 30,
            'max_requests_per_minute': 2000,
            'features': ['基础情感分析', '批量处理(1000条)', 'API访问', '7x24小时支持', '自定义模型', 'SLA保障'],
            'sort_order': 3
        }
    ]
    
    for plan_data in default_plans:
        existing = Plan.query.filter_by(name=plan_data['name']).first()
        if not existing:
            plan = Plan(**plan_data)
            db.session.add(plan)
    
    try:
        db.session.commit()
        print("✅ 默认套餐初始化成功")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 默认套餐初始化失败: {e}")