from pymongo import MongoClient
from datetime import datetime

# MongoDB连接
try:
    client = MongoClient('mongodb://localhost:27017/')
    # 测试连接
    client.server_info()
    print("MongoDB连接成功")
except Exception as e:
    print(f"MongoDB连接失败: {e}")
    raise

db = client['data_analysis_web']  # 数据库名称

# 集合（相当于表）
users = db['users']

# 创建索引
users.create_index('username', unique=True)
users.create_index('email', unique=True)

def init_db():
    """初始化数据库，创建必要的索引"""
    if 'users' not in db.list_collection_names():
        users.create_index('username', unique=True)
        users.create_index('email', unique=True)

def create_user(username, password_hash, email):
    """创建新用户"""
    try:
        user = {
            'username': username,
            'password': password_hash,
            'email': email,
            'level': '普通用户',
            'usage_count': 0,
            'settings': {
                'notifications': True,
                'dark_mode': False,
                'theme': '默认'
            },
            'created_at': datetime.now(),
            'last_login': datetime.now()
        }
        result = users.insert_one(user)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, str(e)

def get_user(username):
    """获取用户信息"""
    return users.find_one({'username': username}, {'password': 0})

def verify_user(username, password_hash):
    """验证用户密码"""
    user = users.find_one({
        'username': username,
        'password': password_hash
    })
    return user is not None

def update_user_settings(username, settings):
    """更新用户设置"""
    try:
        result = users.update_one(
            {'username': username},
            {'$set': {'settings': settings}}
        )
        return True, '设置已更新'
    except Exception as e:
        return False, str(e)

def update_last_login(username):
    """更新最后登录时间"""
    users.update_one(
        {'username': username},
        {'$set': {'last_login': datetime.now()}}
    )

def increment_usage_count(username):
    """增加使用次数"""
    users.update_one(
        {'username': username},
        {'$inc': {'usage_count': 1}}
    ) 