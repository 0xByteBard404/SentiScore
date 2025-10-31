# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""
import os
import sys
from datetime import datetime, timezone

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.manager import db
from src.models.user import User, Admin, APIKey
from src.models.quota import SystemConfig, JWTToken
from src.models.api import Plan, Order, APICall

def init_database():
    """初始化数据库"""
    try:
        # 创建所有表
        db.create_all()
        print("✅ 数据表创建成功")
        
        # 初始化系统配置
        config = SystemConfig.query.first()
        if not config:
            config = SystemConfig()
            db.session.add(config)
            db.session.commit()
            print("✅ 系统配置初始化成功")
        else:
            print("ℹ️  系统配置已存在")
        
        # 初始化默认套餐
        free_plan = Plan.query.filter_by(name='Free').first()
        if not free_plan:
            free_plan = Plan(
                name='Free',
                description='免费套餐，适合个人开发者和小规模测试',
                quota_total=1000,
                price=0,
                duration_days=30,
                max_requests_per_minute=10,
                features=['基础情感分析', 'API访问', '社区支持'],
                sort_order=0
            )
            db.session.add(free_plan)
            db.session.commit()
            print("✅ 默认套餐初始化成功")
        else:
            print("ℹ️  默认套餐已存在")
        
        # 创建默认管理员账户
        admin = Admin.query.first()
        if not admin:
            # 检查是否有同名用户
            existing_user = User.query.filter_by(username='admin').first()
            if existing_user:
                # 将现有用户升级为管理员
                admin = Admin(user_id=existing_user.id, role='super_admin')
                db.session.add(admin)
            else:
                # 创建新管理员用户
                user = User(
                    username='admin',
                    email='admin@sentiscore.com',
                    password='admin123456'
                )
                db.session.add(user)
                db.session.flush()  # 获取user.id
                
                # 创建管理员记录
                admin = Admin(user_id=user.id, role='super_admin')
                db.session.add(admin)
                
                # 为管理员创建API密钥记录
                api_key_record = APIKey(
                    user_id=user.id,
                    name='管理员默认密钥'
                )
                db.session.add(api_key_record)
            
            db.session.commit()
            print("✅ 管理员账户初始化成功")
        else:
            print("ℹ️  管理员账户已存在")
        
        print("✅ 数据库初始化成功")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        db.session.rollback()
        raise e

if __name__ == '__main__':
    init_database()
