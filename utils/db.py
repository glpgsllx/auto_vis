from pymongo import MongoClient
from datetime import datetime
import mysql.connector
import pandas as pd

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

# MySQL连接和查询功能
def connect_mysql(host, port, user, password, database, charset='utf8mb4'):
    """连接到MySQL数据库
    
    Args:
        host (str): 数据库服务器地址
        port (int): 数据库端口
        user (str): 用户名
        password (str): 密码
        database (str): 数据库名
        charset (str, optional): 字符集，默认为utf8mb4
        
    Returns:
        tuple: (连接对象, 错误信息)
            - 如果成功连接，返回 (连接对象, None)
            - 如果连接失败，返回 (None, 错误信息字符串)
    """
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset
        )
        return connection, None
    except Exception as e:
        return None, f"MySQL连接失败: {str(e)}"

def get_mysql_tables(connection):
    """获取MySQL数据库中的所有表
    
    Args:
        connection: MySQL连接对象
        
    Returns:
        list: 表名列表
    """
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    return tables

def get_mysql_table_data(connection, table_name, limit=1000):
    """从MySQL表中获取数据
    
    Args:
        connection: MySQL连接对象
        table_name (str): 表名
        limit (int, optional): 最大返回行数，默认为1000
        
    Returns:
        tuple: (DataFrame, 错误信息)
            - 如果成功获取数据，返回 (DataFrame, None)
            - 如果获取失败，返回 (None, 错误信息字符串)
    """
    try:
        # 首先获取表的总行数
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        cursor.close()
        
        # 如果表太大，只获取前limit行
        if total_rows > limit:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql_query(query, connection)
            return df, f"表中共有{total_rows}行数据，已获取前{limit}行"
        else:
            # 如果表不大，获取所有数据
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, connection)
            return df, None
    except Exception as e:
        return None, f"获取表数据失败: {str(e)}"

def close_mysql_connection(connection):
    """关闭MySQL连接
    
    Args:
        connection: MySQL连接对象
    """
    if connection:
        connection.close() 