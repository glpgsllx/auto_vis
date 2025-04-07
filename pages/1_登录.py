import streamlit as st
from utils.auth import login_user, register_user

# 页面配置
st.set_page_config(
    page_title="登录 - 数据分析助手",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"  # 强制隐藏侧边栏
)

# 设置页面样式
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}  /* 隐藏主菜单 */
    footer {visibility: hidden;}     /* 隐藏页脚 */
    .main {
        padding: 0rem 1rem;
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
    .auth-box {
        background: white;
        padding: 2.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        width: 100%;
        max-width: 360px;
        margin: 0 auto;
    }
    .auth-title {
        text-align: center;
        color: #333;
        margin-bottom: 1rem;
        font-size: 28px;
        font-weight: 600;
    }
    .auth-subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 14px;
    }
    .auth-switch {
        text-align: center;
        margin-top: 1.5rem;
        color: #666;
        font-size: 14px;
    }
    .auth-switch a {
        color: #FF6B6B;
        text-decoration: none;
        font-weight: 500;
    }
    .auth-switch a:hover {
        text-decoration: underline;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border: 1px solid #e0e0e0;
        font-size: 14px;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: #FF6B6B;
        box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.1);
    }
    .stTextInput>div>div>input:hover {
        border-color: #FF8E53;
    }
    .stTextInput>label {
        font-size: 14px;
        color: #666;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化session state
if 'show_login' not in st.session_state:
    st.session_state.show_login = True

# 页面标题
st.markdown('<p style="font-size: 40px; font-weight: bold; text-align: center; margin-bottom: 2rem;">数据分析助手</p>', unsafe_allow_html=True)

# 登录/注册表单
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.session_state.show_login:
        st.markdown("""
        <div class="auth-box">
            <h2 class="auth-title">欢迎回来</h2>
            <p class="auth-subtitle">请登录您的账号以继续使用</p>
        </div>
        """, unsafe_allow_html=True)
        username = st.text_input("用户名", key="login_username", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", key="login_password", placeholder="请输入密码")
        if st.button("登录", key="login_button"):
            success, message, user_info = login_user(username, password)
            if success:
                st.success(message)
                st.session_state.user_info = user_info
                st.switch_page("Home.py")  # 登录成功后跳转到主页
            else:
                st.error(message)
        st.markdown('<p class="auth-switch">还没有账号？ <a href="#" onclick="document.querySelector(\'[data-testid=\'stButton\'] button\').click()">立即注册</a></p>', unsafe_allow_html=True)
        if st.button("没有账号？去注册", key="to_register", help="点击切换到注册页面"):
            st.session_state.show_login = False
    else:
        st.markdown("""
        <div class="auth-box">
            <h2 class="auth-title">创建账号</h2>
            <p class="auth-subtitle">开启您的数据分析之旅</p>
        </div>
        """, unsafe_allow_html=True)
        username = st.text_input("用户名", key="register_username", placeholder="请设置用户名")
        password = st.text_input("密码", type="password", key="register_password", placeholder="请设置密码")
        email = st.text_input("邮箱", key="register_email", placeholder="请输入邮箱")
        if st.button("注册", key="register_button"):
            success, message = register_user(username, password, email)
            if success:
                st.success("注册成功！请使用新账号登录")
                st.session_state.show_login = True
            else:
                st.error(message)
        st.markdown('<p class="auth-switch">已有账号？ <a href="#" onclick="document.querySelector(\'[data-testid=\'stButton\'] button\').click()">立即登录</a></p>', unsafe_allow_html=True)
        if st.button("已有账号？去登录", key="to_login", help="点击切换到登录页面"):
            st.session_state.show_login = True 