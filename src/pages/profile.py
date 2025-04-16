import streamlit as st
from src.auth.auth import is_logged_in
from src.auth.profile import display_user_profile, handle_avatar_upload, display_user_settings
from src.web_utils.ui_elements import display_sidebar_user_info

st.set_page_config(
    page_title="个人中心 | 数据分析助手",
    page_icon="👤",
    layout="wide"
)

# 检查用户是否登录
if not is_logged_in():
    st.warning("请先登录")
    st.switch_page("login.py")

# 设置页面样式
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stButton>button {
        border-radius: 20px;
        height: 3em;
        background: linear-gradient(90deg, #FF6B6B 0%, #FF8E53 100%);
        border: none;
        color: white;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
    }
    .profile-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 显示侧边栏
with st.sidebar:
    display_sidebar_user_info(st.session_state.user_info)

# 页面标题
st.title("个人中心")

user_info = st.session_state.user_info

# 个人信息展示
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("个人资料")
display_user_profile(user_info)
st.markdown("</div>", unsafe_allow_html=True)

# 头像管理
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("头像管理")
handle_avatar_upload(user_info)
st.markdown("</div>", unsafe_allow_html=True)

# 个人设置
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
display_user_settings(user_info)
st.markdown("</div>", unsafe_allow_html=True)

# 账号安全
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

# 使用统计
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("使用统计")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("总使用次数", user_info['usage_count'])
with col2:
    st.metric("账号等级", user_info['level'])
with col3:
    st.metric("注册时间", user_info['created_at'].strftime('%Y-%m-%d'))
st.markdown("</div>", unsafe_allow_html=True) 