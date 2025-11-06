import streamlit as st
import os
from src.database.mongodb import init_db
from src.web_utils.ui_elements import display_sidebar_user_info

# 初始化数据库
init_db()

# 检查用户是否已登录
if 'user_info' not in st.session_state or st.session_state.user_info is None:
    st.switch_page("pages/login.py")

# 1. 页面基础配置
st.set_page_config(
    page_title="Data Analysis Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 设置页面样式
st.markdown("""
    <style>
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
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .feature-box {
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #eee;
        background-color: white;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 侧边栏配置
with st.sidebar:
    # 显示用户信息
    display_sidebar_user_info(st.session_state.user_info)

# 4. 主页面内容
st.markdown(f'''
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 class="big-font">Welcome back, {st.session_state.user_info["username"]} 👋</h1>
    <p style="color: #666;">What would you like to analyze today?</p>
</div>
''', unsafe_allow_html=True)

# 5. 功能区展示
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h3>📊 Data Analysis</h3>
        <p>Upload your data file and get in-depth analysis</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Analysis", key="to_analysis"):
            st.switch_page("pages/data_analysis.py")

with col2:
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h3>📈 Visualization</h3>
        <p>Turn your data into intuitive charts</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Create Visualization", key="to_viz"):
            st.switch_page("pages/visualization.py")

with col3:
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h3>👤 Profile</h3>
        <p>Manage your personal info and preferences</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Profile", key="to_profile"):
            st.switch_page("pages/profile.py")

# 6. 快速开始指南
st.markdown("""
<div style="background: white; padding: 2rem; border-radius: 15px; margin-top: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    <h3 style="color: #333; margin-bottom: 1rem;">🚀 Quick Start</h3>
    <ol style="color: #666;">
        <li>Click the "Data Analysis" button above</li>
        <li>Upload your CSV/Excel file</li>
        <li>Choose the analysis you need</li>
        <li>View results and charts</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# 7. 页面底部信息
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #333;">📫 Contact</h3>
        <p style="color: #666;">Email: support@example.com</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #333;">🔗 Quick Links</h3>
        <p style="color: #666;"><a href="#">Docs</a></p>
        <p style="color: #666;"><a href="#">FAQ</a></p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #333;">📢 Announcements</h3>
        <p style="color: #666;">System maintenance scheduled for Saturday</p>
    </div>
    """, unsafe_allow_html=True) 