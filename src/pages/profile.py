import streamlit as st
from src.auth.auth import is_logged_in
from src.auth.profile import display_user_profile, handle_avatar_upload, display_user_settings
from src.web_utils.ui_elements import display_sidebar_user_info

st.set_page_config(
    page_title="Profile | Data Analysis Assistant",
    page_icon="👤",
    layout="wide"
)

# 检查用户是否登录
if not is_logged_in():
    st.warning("Please log in first")
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

# Page title
st.title("Profile")

user_info = st.session_state.user_info

# Profile section
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("Personal Info")
display_user_profile(user_info)
st.markdown("</div>", unsafe_allow_html=True)

# Avatar
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("Avatar")
handle_avatar_upload(user_info)
st.markdown("</div>", unsafe_allow_html=True)

# Settings
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
display_user_settings(user_info)
st.markdown("</div>", unsafe_allow_html=True)

# Security
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("Account Security")
with st.expander("Change Password"):
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    if st.button("Update Password"):
        if new_password != confirm_password:
            st.error("New password and confirmation do not match")
        else:
            # TODO: implement password update
            st.info("Password update is under development")
st.markdown("</div>", unsafe_allow_html=True)

# Usage
st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
st.subheader("Usage Statistics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Usage", user_info['usage_count'])
with col2:
    st.metric("Account Level", user_info['level'])
with col3:
    st.metric("Registered At", user_info['created_at'].strftime('%Y-%m-%d'))
st.markdown("</div>", unsafe_allow_html=True) 