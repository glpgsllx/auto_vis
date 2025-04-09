import streamlit as st
from utils.auth import update_settings, update_avatar
from datetime import datetime
import base64
import os
import uuid

st.title("个人中心")

# 检查用户是否登录
if 'user_info' not in st.session_state or st.session_state.user_info is None:
    st.warning("请先登录")
    st.stop()

user_info = st.session_state.user_info

# 创建头像存储目录
if not os.path.exists("data/avatars"):
    os.makedirs("data/avatars")

# 个人信息展示
col1, col2 = st.columns([1, 2])
with col1:
    # 显示当前头像
    avatar_url = user_info.get('avatar_url', 'https://ui-avatars.com/api/?name=' + user_info.get('username', 'User') + '&background=random')
    
    # 检查头像路径是否存在
    if avatar_url.startswith('data/avatars/'):
        if os.path.exists(avatar_url):
            st.image(avatar_url, caption="当前头像", width=150)
        else:
            # 如果头像文件不存在，使用默认头像
            default_avatar = 'https://ui-avatars.com/api/?name=' + user_info.get('username', 'User') + '&background=random'
            st.image(default_avatar, caption="当前头像", width=150)
    else:
        st.image(avatar_url, caption="当前头像", width=150)
    
    # 头像上传
    st.write("更新头像")
    uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"], key="avatar_uploader")
    
    # 使用按钮触发上传，而不是自动触发
    if uploaded_file is not None and st.button("确认上传"):
        # 删除用户之前的头像文件（如果有）
        old_avatar_url = user_info.get('avatar_url', '')
        if old_avatar_url.startswith('data/avatars/') and os.path.exists(old_avatar_url):
            try:
                os.remove(old_avatar_url)
            except Exception as e:
                st.warning(f"无法删除旧头像文件: {e}")
        
        # 使用用户名作为文件名基础，避免生成过多文件
        file_extension = os.path.splitext(uploaded_file.name)[1]
        file_name = f"{user_info['username']}_{int(datetime.now().timestamp())}{file_extension}"
        file_path = f"data/avatars/{file_name}"
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 更新用户头像
        success, message = update_avatar(user_info['username'], file_path)
        if success:
            st.success("头像已更新")
            # 使用session_state清除上传的文件
            st.session_state.avatar_uploader = None
            # 刷新页面以显示新头像
            st.rerun()
        else:
            st.error(f"头像更新失败: {message}")

with col2:
    st.write(f"用户名：{user_info.get('username', '未设置')}")
    st.write(f"账号等级：{user_info.get('level', '普通用户')}")
    st.write(f"邮箱：{user_info.get('email', '未设置')}")
    st.write(f"使用次数：{user_info.get('usage_count', 0)}")
    if 'created_at' in user_info:
        st.write(f"注册时间：{user_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    if 'last_login' in user_info:
        st.write(f"最后登录：{user_info['last_login'].strftime('%Y-%m-%d %H:%M:%S')}")

# 个人设置
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

# 账号安全
st.subheader("账号安全")
with st.expander("修改密码"):
    current_password = st.text_input("当前密码", type="password")
    new_password = st.text_input("新密码", type="password")
    confirm_password = st.text_input("确认新密码", type="password")
    if st.button("更新密码"):
        if new_password != confirm_password:
            st.error("新密码与确认密码不匹配")
        else:
            # TODO: 实现密码更新功能
            st.info("密码更新功能开发中")

# 使用统计
st.subheader("使用统计")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("总使用次数", user_info['usage_count'])
with col2:
    st.metric("账号等级", user_info['level'])
with col3:
    st.metric("注册时间", user_info['created_at'].strftime('%Y-%m-%d'))