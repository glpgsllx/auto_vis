import pymysql
import pandas as pd
import traceback

def connect_mysql(host='localhost', port=3306, user='root', password='', database=''):
    """连接到MySQL数据库
    
    Args:
        host (str): 数据库主机
        port (int): 数据库端口
        user (str): 用户名
        password (str): 密码
        database (str): 数据库名
        
    Returns:
        tuple: (连接对象, 错误信息)
    """
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection, None
    except Exception as e:
        error_info = str(e)
        return None, error_info

def close_mysql_connection(connection):
    """关闭MySQL连接
    
    Args:
        connection: MySQL连接对象
    """
    if connection:
        connection.close()

def get_mysql_tables(connection):
    """获取数据库中的表列表
    
    Args:
        connection: MySQL连接对象
        
    Returns:
        list: 表名列表
    """
    tables = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            result = cursor.fetchall()
            for table in result:
                tables.append(list(table.values())[0])
        return tables
    except Exception as e:
        print(f"获取表列表时出错: {e}")
        return []

def get_mysql_table_data(connection, table_name, limit=10000):
    """获取表数据
    
    Args:
        connection: MySQL连接对象
        table_name (str): 表名
        limit (int): 最大行数限制
        
    Returns:
        tuple: (DataFrame, 消息)
    """
    try:
        # 检查行数
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
            count = cursor.fetchone()['count']
        
        # 提取数据
        query = f"SELECT * FROM `{table_name}`"
        if limit and count > limit:
            query += f" LIMIT {limit}"
            message = f"表中有 {count} 行数据，已限制加载前 {limit} 行"
        else:
            message = None
        
        df = pd.read_sql(query, connection)
        return df, message
    except Exception as e:
        error_info = f"获取表数据时出错: {str(e)}\n{traceback.format_exc()}"
        return None, error_info

def execute_query(connection, query):
    """执行SQL查询
    
    Args:
        connection: MySQL连接对象
        query (str): SQL查询语句
        
    Returns:
        tuple: (DataFrame/None, 错误信息/None)
    """
    try:
        # 检查是否是SELECT查询
        if query.strip().upper().startswith("SELECT"):
            df = pd.read_sql(query, connection)
            return df, None
        else:
            with connection.cursor() as cursor:
                cursor.execute(query)
                connection.commit()
            return None, "查询执行成功"
    except Exception as e:
        error_info = f"执行查询时出错: {str(e)}\n{traceback.format_exc()}"
        return None, error_info 