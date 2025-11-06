import os
import uuid
import streamlit as st
from datetime import datetime
from src.auth.auth import update_avatar, update_settings

def display_user_profile(user_info):
    """显示用户个人资料
    
    Args:
        user_info (dict): 用户信息
    """
    col1, col2 = st.columns([1, 2])
    with col1:
        # 显示当前头像
        avatar_url = user_info.get('avatar_url', 'https://ui-avatars.com/api/?name=' + user_info.get('username', 'User') + '&background=random')
        
        # 检查头像路径是否存在（使用基于 src 的绝对路径）
        if avatar_url.startswith('data/avatars/'):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            src_root = os.path.join(project_root, "src")
            abs_path = os.path.join(src_root, avatar_url.replace("/", os.sep))
            if os.path.exists(abs_path):
                st.image(abs_path, caption="当前头像", width=150)
            else:
                default_avatar = 'https://ui-avatars.com/api/?name=' + user_info.get('username', 'User') + '&background=random'
                st.image(default_avatar, caption="当前头像", width=150)
        else:
            st.image(avatar_url, caption="当前头像", width=150)
    
    with col2:
        st.write(f"用户名：{user_info.get('username', '未设置')}")
        st.write(f"账号等级：{user_info.get('level', '普通用户')}")
        st.write(f"邮箱：{user_info.get('email', '未设置')}")
        st.write(f"使用次数：{user_info.get('usage_count', 0)}")
        if 'created_at' in user_info:
            st.write(f"注册时间：{user_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        if 'last_login' in user_info:
            st.write(f"最后登录：{user_info['last_login'].strftime('%Y-%m-%d %H:%M:%S')}")

def handle_avatar_upload(user_info):
    """处理头像上传
    
    Args:
        user_info (dict): 用户信息
        
    Returns:
        bool: 是否成功上传
    """
    # 确定数据目录路径（固定到 src/data/avatars）
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    src_root = os.path.join(project_root, "src")
    data_dir = os.path.join(src_root, "data", "avatars")
    os.makedirs(data_dir, exist_ok=True)
    
    st.write("更新头像")
    
    # 使用唯一的key确保不会与其他组件冲突
    upload_key = "avatar_uploader_" + user_info["username"]
    uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"], key=upload_key)
    
    # 使用按钮触发上传，而不是自动触发
    if uploaded_file is not None and st.button("确认上传", key="confirm_avatar_upload"):
        # 删除用户之前的头像文件（如果有）
        old_avatar_url = user_info.get('avatar_url', '')
        if old_avatar_url.startswith('data/avatars/'):
            abs_old = os.path.join(src_root, old_avatar_url.replace("/", os.sep))
            if os.path.exists(abs_old):
                try:
                    os.remove(abs_old)
                except Exception as e:
                    st.warning(f"无法删除旧头像文件: {e}")
        
        # 使用用户名作为文件名基础，避免生成过多文件
        file_extension = os.path.splitext(uploaded_file.name)[1]
        file_name = f"{user_info['username']}_{int(datetime.now().timestamp())}{file_extension}"
        file_path = os.path.join(data_dir, file_name)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 确保数据库中存储的路径是相对于项目根目录的路径
        db_path = "data/avatars/" + file_name
        
        # 更新用户头像
        success, message = update_avatar(user_info['username'], db_path)
        if success:
            st.success("头像已更新")
            # 不要直接修改session_state中的widget状态
            # 而是使用标志来表示上传成功
            if "upload_success" not in st.session_state:
                st.session_state.upload_success = True
            # 刷新页面以显示新头像
            st.rerun()
        else:
            st.error(f"头像更新失败: {message}")
            return False
    
    return True

def display_user_settings(user_info):
    """显示用户设置界面
    
    Args:
        user_info (dict): 用户信息
    """
    st.subheader("个人设置")
    settings = st.container()
    with settings:
        user_settings = user_info.get('settings', {})
        notifications = st.toggle("开启通知", value=user_settings.get('notifications', False))
        dark_mode = st.toggle("深色模式", value=user_settings.get('dark_mode', False))
        theme = st.selectbox("界面主题", ["默认", "暗黑", "明亮"], 
                           index=["默认", "暗黑", "明亮"].index(user_settings.get('theme', '默认')))
        
        if st.button("保存设置"):
            new_settings = {
                "notifications": notifications,
                "dark_mode": dark_mode,
                "theme": theme
            }
            success, message = update_settings(user_info['username'], new_settings)
            if success:
                st.success("设置已更新")
                user_info['settings'] = new_settings
            else:
                st.error(message) 