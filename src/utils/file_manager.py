import os
import shutil
import uuid
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List, Any, Union, Optional

def ensure_dir_exists(directory: str) -> None:
    """确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_user_data_dir(user_id: str) -> str:
    """获取用户数据目录
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: 用户数据目录路径
    """
    user_dir = f"data/users/{user_id}"
    ensure_dir_exists(user_dir)
    return user_dir

def get_conversation_dir(user_id: str, conversation_id: str) -> str:
    """获取对话目录
    
    Args:
        user_id: 用户ID
        conversation_id: 对话ID
        
    Returns:
        str: 对话目录路径
    """
    conv_dir = f"{get_user_data_dir(user_id)}/conversations/{conversation_id}"
    ensure_dir_exists(conv_dir)
    return conv_dir

def get_conversation_images_dir(user_id: str, conversation_id: str) -> str:
    """获取对话图片目录
    
    Args:
        user_id: 用户ID
        conversation_id: 对话ID
        
    Returns:
        str: 对话图片目录路径
    """
    images_dir = f"{get_conversation_dir(user_id, conversation_id)}/images"
    ensure_dir_exists(images_dir)
    return images_dir

def get_conversation_data_dir(user_id: str, conversation_id: str) -> str:
    """获取对话数据目录
    
    Args:
        user_id: 用户ID
        conversation_id: 对话ID
        
    Returns:
        str: 对话数据目录路径
    """
    data_dir = f"{get_conversation_dir(user_id, conversation_id)}/data"
    ensure_dir_exists(data_dir)
    return data_dir

def save_dataframe(df: pd.DataFrame, user_id: str, conversation_id: str, file_name: Optional[str] = None) -> str:
    """保存DataFrame到对话数据目录
    
    Args:
        df: 要保存的DataFrame
        user_id: 用户ID
        conversation_id: 对话ID
        file_name: 文件名，如果不指定则自动生成
        
    Returns:
        str: 保存的文件路径
    """
    data_dir = get_conversation_data_dir(user_id, conversation_id)
    
    if file_name is None:
        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"data_{timestamp}.csv"
    
    file_path = f"{data_dir}/{file_name}"
    df.to_csv(file_path, index=False)
    return file_path

def save_user_uploaded_file(uploaded_file, user_id: str, conversation_id: str) -> str:
    """保存用户上传的文件到对话数据目录
    
    Args:
        uploaded_file: Streamlit上传的文件对象
        user_id: 用户ID
        conversation_id: 对话ID
        
    Returns:
        str: 保存的文件路径
    """
    data_dir = get_conversation_data_dir(user_id, conversation_id)
    
    # 获取原始文件扩展名
    file_name = uploaded_file.name
    file_ext = os.path.splitext(file_name)[1].lower()
    
    # 生成新文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_file_name = f"uploaded_{timestamp}{file_ext}"
    file_path = f"{data_dir}/{new_file_name}"
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def save_image(image_path: str, user_id: str, conversation_id: str, image_name: Optional[str] = None) -> str:
    """保存图片到对话图片目录
    
    Args:
        image_path: 源图片路径
        user_id: 用户ID
        conversation_id: 对话ID
        image_name: 图片名称，如果不指定则自动生成
        
    Returns:
        str: 保存的图片路径
    """
    images_dir = get_conversation_images_dir(user_id, conversation_id)
    
    if image_name is None:
        # 获取图片扩展名
        file_ext = os.path.splitext(image_path)[1].lower()
        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = f"chart_{timestamp}{file_ext}"
    
    new_image_path = f"{images_dir}/{image_name}"
    
    # 复制图片文件
    shutil.copy2(image_path, new_image_path)
    
    return new_image_path

def get_mysql_connection_info_path(user_id: str, conversation_id: str) -> str:
    """获取MySQL连接信息文件路径
    
    Args:
        user_id: 用户ID
        conversation_id: 对话ID
        
    Returns:
        str: MySQL连接信息文件路径
    """
    data_dir = get_conversation_data_dir(user_id, conversation_id)
    return f"{data_dir}/mysql_connection.json"

def create_data_source_info(file_type: str, file_path: str, user_id: str, conversation_id: str) -> Dict[str, Any]:
    """创建数据源信息
    
    Args:
        file_type: 文件类型 (CSV/Excel/MySQL)
        file_path: 文件路径
        user_id: 用户ID
        conversation_id: 对话ID
        
    Returns:
        Dict: 数据源信息字典
    """
    data_dir = get_conversation_data_dir(user_id, conversation_id)
    
    if file_type == "MySQL":
        return {
            "type": "MySQL",
            "connection_info_path": get_mysql_connection_info_path(user_id, conversation_id),
            "table_name": os.path.basename(file_path) if file_path else None
        }
    else:
        # 复制文件到对话数据目录
        file_name = os.path.basename(file_path)
        new_file_path = f"{data_dir}/{file_name}"
        
        if new_file_path != file_path:  # 避免复制到自身
            shutil.copy2(file_path, new_file_path)
        
        return {
            "type": file_type,
            "file_path": new_file_path,
            "original_file_name": file_name
        }

def cleanup_temp_files(max_age_days: int = 7) -> None:
    """清理临时文件
    
    Args:
        max_age_days: 文件最大保留天数
    """
    # 清理codeexe目录中的临时文件
    codeexe_dir = "codeexe"
    if os.path.exists(codeexe_dir):
        now = datetime.now()
        for file_name in os.listdir(codeexe_dir):
            file_path = os.path.join(codeexe_dir, file_name)
            if os.path.isfile(file_path):
                # 获取文件修改时间
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                # 计算文件年龄（天）
                age_days = (now - file_mod_time).days
                # 如果文件年龄超过最大保留天数，删除文件
                if age_days > max_age_days:
                    try:
                        os.remove(file_path)
                        print(f"已删除临时文件: {file_path}")
                    except Exception as e:
                        print(f"删除文件 {file_path} 失败: {str(e)}") 