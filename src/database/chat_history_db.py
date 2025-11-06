from datetime import datetime
from bson import ObjectId  # 用于处理 MongoDB ObjectIDs
import os # 新增
import shutil # 新增
import traceback # For better error logging

# 从 mongodb.py 导入共享的数据库对象
# 注意：这假设 chat_history_db.py 与 mongodb.py 在同一目录下或 Python 路径可达
try:
    from .mongodb import db
except ImportError:
    # 如果直接运行此文件或导入方式不同，尝试另一种方式
    # 在实际应用中，确保导入路径正确
    from mongodb import db

# 获取或创建 chat_sessions 和 chat_messages 集合
chat_sessions = db['chat_sessions']
chat_messages = db['chat_messages']

# 可选：为常用查询字段创建索引以提高性能
chat_sessions.create_index('user_id')
chat_sessions.create_index([('user_id', 1), ('last_updated_at', -1)]) # 复合索引，用于按用户获取并排序
chat_messages.create_index('session_id')
chat_messages.create_index([('session_id', 1), ('timestamp', 1)]) # 复合索引，用于按会话获取并排序

def create_new_session(user_id: str, session_name: str = "未命名会话") -> str | None:
    """
    为指定用户创建一个新的聊天会话。

    Args:
        user_id: 用户的唯一标识符。
        session_name: 会话的初始名称。

    Returns:
        新创建会话的 ID (str)，如果创建失败则返回 None。
    """
    print(f"[create_new_session] 尝试为 user_id='{user_id}' 创建会话，名称='{session_name}'")
    if not user_id:
        print(f"错误：[create_new_session] 接收到无效的 user_id: {user_id}")
        return None
    
    try:
        now = datetime.now()
        new_object_id = ObjectId() # 手动生成 ObjectId
        session_doc = {
            '_id': new_object_id,           # 使用生成的 ObjectId
            'username': user_id,          # 使用 'username' 字段名
            'session_id': str(new_object_id), # 添加 'session_id' 字段 (字符串形式)
            'session_name': session_name,
            'created_at': now,
            'last_updated_at': now,
            'summary': None
        }
        result = chat_sessions.insert_one(session_doc)
        inserted_id = str(new_object_id) # 返回 string 形式的 ID
        print(f"[create_new_session] 成功创建会话，ID: {inserted_id} (Username: {user_id})")
        return inserted_id
    except Exception as e:
        print(f"创建新会话时出错: {e}")
        return None

def get_sessions_by_user(user_id: str) -> list:
    """
    获取指定用户的所有聊天会话，按最后更新时间降序排列。

    Args:
        user_id: 用户的唯一标识符。

    Returns:
        包含会话文档的列表 (每个文档是一个字典)。
    """
    try:
        sessions = list(chat_sessions.find(
            {'username': user_id},
            {'_id': 1, 'session_name': 1, 'last_updated_at': 1}
        ).sort('last_updated_at', -1))

        for session in sessions:
            session['_id'] = str(session['_id'])
        return sessions
    except Exception as e:
        print(f"获取用户 {user_id} 的会话列表时出错: {e}")
        return []

def add_message_to_session(session_id: str, username: str, role: str, content_type: str, content: any, metadata: dict | None = None) -> bool:
    """
    向指定的会话添加一条消息，并更新会话的最后更新时间。

    Args:
        session_id: 消息所属会话的 ID。
        username: 发送消息的用户名。
        role: 消息发送者 ('user' or 'assistant').
        content_type: 消息类型 ('text', 'image', 'code', 'file_upload', etc.).
        content: 消息内容 (可以是字符串、字典等)。
        metadata: 与消息相关的额外元数据 (可选)。

    Returns:
        如果添加成功返回 True，否则返回 False。
    """
    try:
        now = datetime.now()
        message_doc = {
            'session_id': ObjectId(session_id),
            'username': username,
            'role': role,
            'content_type': content_type,
            'content': content,
            'timestamp': now,
            'metadata': metadata if metadata else {}
        }
        chat_messages.insert_one(message_doc)

        chat_sessions.update_one(
            {'_id': ObjectId(session_id)},
            {'$set': {'last_updated_at': now}}
        )
        return True
    except Exception as e:
        print(f"向会话 {session_id} 添加消息时出错: {e}")
        return False

def get_messages_by_session(session_id: str) -> list:
    """
    获取指定会话的所有消息，按时间戳升序排列。

    Args:
        session_id: 会话的 ID。

    Returns:
        包含消息文档的列表 (每个文档是一个字典)。
    """
    try:
        messages = list(chat_messages.find(
            {'session_id': ObjectId(session_id)}
        ).sort('timestamp', 1)) # 1 表示升序

        for msg in messages:
            msg['_id'] = str(msg['_id'])
            if isinstance(msg.get('session_id'), ObjectId):
                msg['session_id'] = str(msg['session_id'])

        return messages
    except Exception as e:
        print(f"获取会话 {session_id} 的消息时出错: {e}")
        return []

# --- 可选功能 (后续可以添加) ---

def update_session_name(session_id: str, new_name: str) -> bool:
    try:
        result = chat_sessions.update_one(
            {'_id': ObjectId(session_id)},
            {'$set': {'session_name': new_name}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"更新会话 {session_id} 名称时出错: {e}")
        return False

def delete_session(session_id: str) -> bool:
    """删除会话及其所有消息和关联文件。"""
    try:
        session_oid = ObjectId(session_id)
        
        session_doc = chat_sessions.find_one({"_id": session_oid}, {"username": 1})
        if not session_doc:
            print(f"错误：未找到 session_id {session_id} 对应的会话文档。")
            return False
        username = session_doc.get("username")
        if not username:
             print(f"错误：会话 {session_id} 缺少 username，无法删除关联文件。")
             # 可以选择继续删除数据库记录，或者在这里返回 False
             # return False 

        delete_msg_result = chat_messages.delete_many({'session_id': session_oid})
        print(f"删除了 {delete_msg_result.deleted_count} 条消息。")
        
        delete_session_result = chat_sessions.delete_one({'_id': session_oid})
        
        if username and delete_session_result.deleted_count > 0:
            try:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                src_root = os.path.join(project_root, "src")
                
                asset_dir = os.path.join(src_root, "session_assets", str(username), str(session_id))
                upload_dir = os.path.join(src_root, "user_uploads", str(username), str(session_id))
                
                if os.path.exists(asset_dir):
                    shutil.rmtree(asset_dir, ignore_errors=True)
                    print(f"已尝试删除目录: {asset_dir}")
                else:
                    print(f"目录不存在，无需删除: {asset_dir}")
                    
                if os.path.exists(upload_dir):
                    shutil.rmtree(upload_dir, ignore_errors=True)
                    print(f"已尝试删除目录: {upload_dir}")
                else:
                    print(f"目录不存在，无需删除: {upload_dir}")
                    
            except Exception as file_e:
                # 文件删除失败不应阻止函数报告数据库删除成功，但应记录错误
                print(f"警告：删除会话 {session_id} 的关联文件时出错: {file_e}")
        
        return delete_session_result.deleted_count > 0
    except Exception as e:
        import traceback
        print(f"删除会话 {session_id} 时发生严重错误: {e}\n{traceback.format_exc()}")
        return False

def update_session_data_context(session_id: str, data_source_type: str, data_source_details: dict) -> bool:
    """
    更新指定会话的数据源上下文信息。

    Args:
        session_id: 会话的 ID。
        data_source_type: 数据源类型 ('file', 'mysql', etc.)。
        data_source_details: 包含数据源具体信息的字典。
                           对于 'file': {'stored_path': ..., 'column_descriptions': ...}
                           对于 'mysql': {'connection_info': ..., 'table_name': ..., 'column_descriptions': ...}

    Returns:
        如果更新成功返回 True，否则返回 False。
    """
    try:
        now = datetime.now()
        result = chat_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "data_source_type": data_source_type,
                    "data_source_details": data_source_details,
                    "last_updated_at": now # 同时更新最后活动时间
                }
            }
        )
        if result.matched_count == 0:
            print(f"警告：尝试更新不存在的会话 {session_id} 的数据上下文。")
            return False
        # modified_count 可能是 0 (如果设置的值相同)，所以主要检查 matched_count
        print(f"会话 {session_id} 数据上下文已更新。")
        return True
    except Exception as e:
        print(f"更新会话 {session_id} 数据上下文时出错: {e}\n{traceback.format_exc()}")
        return False

def get_session_details(session_id: str) -> dict | None:
    """
    获取指定会话的完整详细信息。

    Args:
        session_id: 会话的 ID。

    Returns:
        包含完整会话文档的字典，如果未找到则返回 None。
    """
    try:
        session_doc = chat_sessions.find_one({"_id": ObjectId(session_id)})
        if session_doc:
            # 将 ObjectId 转换为字符串以便序列化
            session_doc['_id'] = str(session_doc['_id'])
            # 如果存在 _id 以外的 ObjectId 字段，也需要转换
            # 例如，如果 user_id 是 ObjectId
            if 'username' in session_doc and isinstance(session_doc['username'], ObjectId):
                 session_doc['username'] = str(session_doc['username'])
            return session_doc
        else:
            print(f"未找到会话 {session_id} 的详细信息。")
            return None
    except Exception as e:
        print(f"获取会话 {session_id} 详细信息时出错: {e}\n{traceback.format_exc()}")
        return None

# --- 简单的测试 (如果直接运行此文件) ---
 