import streamlit as st
from src.auth.auth import login_user, register_user
from src.web_utils.ui_elements import display_error, display_success, create_text_input, create_button

st.set_page_config(
    page_title="Login | Data Analysis Assistant",
    page_icon="🔐",
    layout="centered"
)

# 设置页面样式
st.markdown("""
<style>
    .main {
        padding: 2rem;
        max-width: 800px;
        margin: 0 auto;
    }
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        margin-top: 1em;
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-bottom: 2px solid #FF6B6B;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1>Data Analysis Assistant</h1>
    <p>Your intelligent data analysis companion</p>
</div>
""", unsafe_allow_html=True)

# Tabs: Login / Register
login_tab, register_tab = st.tabs(["Log In", "Sign Up"])

# 登录标签页
with login_tab:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/user-male-circle--v1.png", width=80)
    with col2:
        st.markdown("""
        <h2 style="margin-bottom: 5px;">Welcome back</h2>
        <p style="color: #666; margin-top: 0;">Please sign in to your account</p>
        """, unsafe_allow_html=True)
    
    username = create_text_input("Username", key="login_username")
    password = create_text_input("Password", key="login_password", type="password")
    
    remember_me = st.checkbox("Remember me", value=True)
    
    if create_button("Log In", key="login_button"):
        if not username or not password:
            display_error("Please enter username and password")
        else:
            success, message, user_info = login_user(username, password)
            if success:
                st.session_state.user_info = user_info
                display_success(message)
                st.switch_page("app.py")
            else:
                display_error(message)
    
    st.markdown("<div style='text-align: center; margin-top: 1rem;'><a href='#'>Forgot password?</a></div>", unsafe_allow_html=True)

# 注册标签页
with register_tab:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/add-user-male--v1.png", width=80)
    with col2:
        st.markdown("""
        <h2 style="margin-bottom: 5px;">Create account</h2>
        <p style="color: #666; margin-top: 0;">Start your data analysis journey</p>
        """, unsafe_allow_html=True)
    
    username = create_text_input("Username", key="register_username")
    email = create_text_input("Email", key="register_email")
    password = create_text_input("Password", key="register_password", type="password")
    confirm_password = create_text_input("Confirm Password", key="register_confirm_password", type="password")
    
    agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", value=False)
    
    if create_button("Sign Up", key="register_button"):
        if not username or not email or not password or not confirm_password:
            display_error("Please fill in all required fields")
        elif password != confirm_password:
            display_error("Passwords do not match")
        elif not agree_terms:
            display_error("Please accept the Terms and Privacy Policy")
        else:
            success, message = register_user(username, password, email)
            if success:
                display_success("Registration successful. Please log in.")
                # 自动切换到登录标签
                st.experimental_set_query_params(view="login")
                st.rerun()
            else:
                display_error(message)

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.8rem;">
    © 2023 Data Analysis Assistant | <a href="#">Privacy Policy</a> | <a href="#">Terms of Service</a>
</div>
""", unsafe_allow_html=True)