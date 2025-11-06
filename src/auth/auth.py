import hashlib
import streamlit as st
from src.database.mongodb import (
    create_user, verify_user, get_user, 
    update_user_settings, update_last_login, update_user_avatar
)

def hash_password(password):
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email):
    """注册新用户"""
    password_hash = hash_password(password)
    success, message = create_user(username, password_hash, email)
    return success, message

def login_user(username, password):
    """用户登录"""
    password_hash = hash_password(password)
    if verify_user(username, password_hash):
        user_info = get_user(username)
        if user_info:
            update_last_login(username)
            return True, "Login successful", user_info
    return False, "Incorrect username or password", None

def update_settings(username, settings):
    """更新用户设置"""
    success, message = update_user_settings(username, settings)
    if success:
        user_info = get_user(username)
        if user_info:
            st.session_state.user_info = user_info
    return success, message

def update_avatar(username, avatar_url):
    """更新用户头像
    
    Args:
        username (str): 用户名
        avatar_url (str): 头像URL
        
    Returns:
        tuple: (是否成功, 消息)
    """
    success, message = update_user_avatar(username, avatar_url)
    if success:
        user_info = get_user(username)
        if user_info:
            st.session_state.user_info = user_info
    return success, message

def is_logged_in():
    """检查用户是否已登录"""
    return 'user_info' in st.session_state and st.session_state.user_info is not None

def logout_user():
    """退出登录"""
    if 'user_info' in st.session_state:
        st.session_state.user_info = None
    return True 