import streamlit as st
from utils.auth import update_settings
from datetime import datetime

st.title("个人中心")

# 检查用户是否登录
if 'user_info' not in st.session_state or st.session_state.user_info is None:
    st.warning("请先登录")
    st.stop()

user_info = st.session_state.user_info

# 个人信息展示
col1, col2 = st.columns([1, 2])
with col1:
    st.image("https://placeholder.com/150", caption="头像")
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