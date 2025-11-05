# -*- coding: utf-8 -*-
"""
数据库管理器
"""
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, or_

# 创建全局db实例
db = SQLAlchemy()

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        # 确保instance目录存在
        instance_dir = 'instance'
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir, exist_ok=True)
            print(f"✅ 创建instance目录: {instance_dir}")
        else:
            print(f"ℹ️  instance目录已存在: {instance_dir}")
        
        # 确保数据库文件存在
        db_file = os.path.join(instance_dir, 'sentiscore.db')
        if not os.path.exists(db_file):
            try:
                with open(db_file, 'w') as f:
                    pass  # 创建空文件
                print(f"✅ 创建数据库文件: {db_file}")
            except Exception as e:
                print(f"⚠️  创建数据库文件失败: {e}")
        
        # 设置目录和文件权限
        try:
            import stat
            os.chmod(instance_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.chmod(db_file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            print(f"✅ 设置instance目录和数据库文件权限")
        except Exception as e:
            print(f"⚠️  设置权限失败: {e}")
        
        # 数据库配置 - 统一使用instance目录下的sentiscore.db
        database_url = os.getenv('DATABASE_URL', f'sqlite:///{db_file}')
        print(f"🔧 数据库URL: {database_url}")
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {"check_same_thread": False} if database_url.startswith('sqlite') else {}
        }
        
        # 初始化db
        db.init_app(app)
    
    def create_tables(self):
        """创建所有数据表"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            with self.app.app_context():
                db.create_all()
            print("✅ 数据表创建成功")
            return True
        except Exception as e:
            print(f"❌ 数据表创建失败: {e}")
            return False
    
    def drop_tables(self):
        """删除所有数据表"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            with self.app.app_context():
                db.drop_all()
            print("✅ 数据表删除成功")
            return True
        except Exception as e:
            print(f"❌ 数据表删除失败: {e}")
            return False
    
    def update_table_structure(self):
        """更新表结构"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            with self.app.app_context():
                # 检查并添加api_keys表缺失的列
                try:
                    # 使用正确的SQLAlchemy方法检查列是否存在
                    result = db.session.execute(text("""
                        PRAGMA table_info(api_keys)
                    """))
                    columns = [row[1] for row in result]
                    
                    if 'quota_total' not in columns:
                        db.session.execute(text("""
                            ALTER TABLE api_keys ADD COLUMN quota_total INTEGER DEFAULT 1000
                        """))
                        print("✅ 添加api_keys.quota_total列成功")
                    
                    if 'quota_used' not in columns:
                        db.session.execute(text("""
                            ALTER TABLE api_keys ADD COLUMN quota_used INTEGER DEFAULT 0
                        """))
                        print("✅ 添加api_keys.quota_used列成功")
                    
                    if 'last_used_at' not in columns:
                        db.session.execute(text("""
                            ALTER TABLE api_keys ADD COLUMN last_used_at DATETIME
                        """))
                        print("✅ 添加api_keys.last_used_at列成功")
                        
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"⚠️  更新api_keys表结构时出错: {e}")
                
                # 检查并添加api_calls表缺失的列
                try:
                    # 检查api_calls表的api_key_id列
                    result = db.session.execute(text("""
                        PRAGMA table_info(api_calls)
                    """))
                    columns = [row[1] for row in result]
                    
                    if 'api_key_id' not in columns:
                        db.session.execute(text("""
                            ALTER TABLE api_calls ADD COLUMN api_key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL
                        """))
                        print("✅ 添加api_calls.api_key_id列成功")
                        
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"⚠️  更新api_calls表结构时出错: {e}")
                
                # 检查并添加其他可能缺失的列
                try:
                    # 检查api_keys表的quota_remaining列（计算字段，不需要实际添加）
                    pass
                except Exception as e:
                    print(f"⚠️  检查api_keys表结构时出错: {e}")
            
            print("✅ 表结构更新完成")
            return True
        except Exception as e:
            print(f"❌ 表结构更新失败: {e}")
            return False
    
    def init_database(self):
        """初始化数据库"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            with self.app.app_context():
                # 初始化系统配置
                from src.models.quota import init_system_config
                init_system_config()
                
                # 初始化套餐数据
                from src.models.api import init_default_plans
                init_default_plans()
            print("✅ 数据库初始化成功")
            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
    
    def create_default_admin(self):
        """创建默认管理员账户"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            with self.app.app_context():
                from src.models.user import User, Admin, UserPlan
                from src.models.api import Plan
                
                # 检查是否已存在管理员（检查用户名或邮箱）
                existing_user = User.query.filter_by(username='admin').first()
                
                if not existing_user:
                    existing_user = User.query.filter_by(email='admin@sentiscore.com').first()
                
                if not existing_user:
                    # 创建管理员用户
                    admin_user = User('admin', 'admin@sentiscore.com', 'admin123456')
                    admin_user.email_verified = True
                    db.session.add(admin_user)
                    db.session.flush()  # 获取用户ID
                    
                    # 创建管理员角色
                    admin_role = Admin()
                    admin_role.user_id = admin_user.id
                    admin_role.role = 'super_admin'
                    admin_role.permissions = {
                        'users': ['create', 'read', 'update', 'delete'],
                        'orders': ['create', 'read', 'update', 'delete'],
                        'plans': ['create', 'read', 'update', 'delete'],
                        'config': ['read', 'update'],
                        'admin': ['create', 'read', 'update', 'delete']
                    }
                    db.session.add(admin_role)
                    
                    # 创建默认Free套餐
                    free_plan = Plan.query.filter_by(name='Free').first()
                    if free_plan:
                        user_plan = UserPlan()
                        user_plan.user_id = admin_user.id
                        user_plan.plan_name = 'Free'
                        user_plan.plan_type = 'free'
                        user_plan.quota_total = free_plan.quota_total
                        user_plan.quota_used = 0
                        user_plan.quota_remaining = free_plan.quota_total
                        user_plan.reset_period = 'monthly'
                        user_plan.is_active = True
                        db.session.add(user_plan)
                    
                    db.session.commit()
                    print("✅ 默认管理员账户创建成功")
                    print("   用户名: admin")
                    print("   邮箱: admin@sentiscore.com")
                    print("   密码: admin123456")
                    return True
                else:
                    print("ℹ️  管理员账户已存在")
                    return True
        except Exception as e:
            print(f"❌ 默认管理员账户创建失败: {e}")
            return False
    
    def reset_database(self):
        """重置数据库"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            self.drop_tables()
            self.create_tables()
            self.init_database()
            print("✅ 数据库重置成功")
            return True
        except Exception as e:
            print(f"❌ 数据库重置失败: {e}")
            return False
    
    def get_table_info(self):
        """获取数据表信息"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return []
                
            tables = []
            # 获取所有表名
            with self.app.app_context():
                result = db.session.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table'
                """))
                tables = [row[0] for row in result]
            return tables
        except Exception as e:
            print(f"❌ 获取表信息失败: {e}")
            return []
    
    def backup_database(self, backup_path=None):
        """备份数据库"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            if not backup_path:
                backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            with self.app.app_context():
                # SQLite备份
                from sqlalchemy import create_engine
                source_engine = db.engine
                dest_engine = create_engine(f'sqlite:///{backup_path}')
                
                # 复制数据
                source_conn = source_engine.raw_connection()
                dest_conn = dest_engine.raw_connection()
                
                source_conn.backup(dest_conn)
                
                source_conn.close()
                dest_conn.close()
            
            print(f"✅ 数据库备份完成: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ 数据库备份失败: {e}")
            return False
    
    def clean_expired_tokens(self):
        """清理过期的JWT令牌"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return False
                
            from src.models.quota import JWTToken
            from datetime import datetime, timezone
            
            # 删除已过期或已撤销的令牌（保留最近100条）
            expired_tokens = JWTToken.query.filter(
                (JWTToken.expires_at < datetime.now(timezone.utc)) |
                (JWTToken.revoked == True)
            ).all()
            
            for token in expired_tokens:
                db.session.delete(token)
            
            db.session.commit()
            print(f"✅ 清理了 {len(expired_tokens)} 个过期令牌")
            return True
        except Exception as e:
            print(f"❌ 清理令牌失败: {e}")
            return False
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return {}
                
            stats = {}
            
            # 用户统计
            from src.models.user import User
            stats['users'] = {
                'total': User.query.count(),
                'active': User.query.filter_by(status='active').count(),
                'verified': User.query.filter_by(email_verified=True).count()
            }
            
            # API调用统计
            from src.models.api import APICall
            stats['api_calls'] = {
                'total': APICall.query.count(),
                'today': APICall.query.filter(
                    APICall.created_at >= datetime.now().date()
                ).count()
            }
            
            # 订单统计
            from src.models.api import Order
            stats['orders'] = {
                'total': Order.query.count(),
                'paid': Order.query.filter_by(status='paid').count(),
                'pending': Order.query.filter_by(status='pending').count()
            }
            
            # 数据库大小
            if os.getenv('DATABASE_URL', 'sqlite:///sentiscore.db').startswith('sqlite'):
                db_path = os.getenv('DATABASE_URL', 'sqlite:///sentiscore.db').replace('sqlite:///', '')
                if os.path.exists(db_path):
                    stats['database_size'] = f"{os.path.getsize(db_path) / 1024 / 1024:.2f} MB"
            
            return stats
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def health_check(self):
        """数据库健康检查"""
        try:
            if self.app is None:
                print("❌ 应用实例未初始化")
                return {
                    'status': 'error',
                    'message': '应用实例未初始化',
                    'timestamp': datetime.now().isoformat()
                }
                
            # 测试连接
            db.session.execute(text('SELECT 1'))
            
            # 测试表是否存在
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)).scalar()
            
            if result is not None and result > 0:
                return {
                    'status': 'healthy',
                    'message': '数据库连接正常',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': '数据表不存在',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'数据库连接失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }