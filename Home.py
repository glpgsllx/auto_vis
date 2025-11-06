import streamlit as st
import os
from utils.db import init_db

# 初始化数据库
init_db()

# 检查用户是否已登录
if 'user_info' not in st.session_state or st.session_state.user_info is None:
    st.switch_page("pages/1_登录.py")

# 1. 页面基础配置
st.set_page_config(
    page_title="数据分析助手",
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
    if 'user_info' in st.session_state and st.session_state.user_info is not None:
        # 显示用户头像
        avatar_url = st.session_state.user_info.get('avatar_url', 'https://ui-avatars.com/api/?name=' + st.session_state.user_info.get('username', 'User') + '&background=random')
        
        # 检查头像路径是否存在（使用基于 src 的绝对路径）
        if avatar_url.startswith('data/avatars/'):
            project_root = os.path.abspath(os.path.dirname(__file__))
            src_root = os.path.join(project_root, "src")
            abs_path = os.path.join(src_root, avatar_url.replace("/", os.sep))
            if os.path.exists(abs_path):
                st.image(abs_path, width=100)
            else:
                # 如果头像文件不存在，使用默认头像
                default_avatar = 'https://ui-avatars.com/api/?name=' + st.session_state.user_info.get('username', 'User') + '&background=random'
                st.image(default_avatar, width=100)
        else:
            st.image(avatar_url, width=100)
        
        # 显示用户名
        st.write(f"**{st.session_state.user_info['username']}**")
        
        # 简单显示统计信息，无额外容器
        st.write(f"使用次数：{st.session_state.user_info['usage_count']}")
        st.write(f"账号等级：{st.session_state.user_info['level']}")
        
        st.markdown("---")
        
        # 退出登录按钮
        if st.button("退出登录", key="logout"):
            st.session_state.user_info = None
            st.switch_page("pages/1_登录.py")

# 4. 主页面内容
st.markdown(f'''
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 class="big-font">欢迎回来, {st.session_state.user_info["username"]} 👋</h1>
    <p style="color: #666;">今天想要分析什么数据呢？</p>
</div>
''', unsafe_allow_html=True)

# 5. 功能区展示
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h3>📊 数据分析</h3>
        <p>上传您的数据文件，获取深入的数据分析报告</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开始数据分析", key="to_analysis"):
            st.sidebar.markdown("👈 点击左侧的'数据分析'开始")
            st.balloons()

with col2:
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h3>📈 数据可视化</h3>
        <p>将您的数据转化为直观的图表展示</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("创建可视化", key="to_viz"):
            st.sidebar.markdown("👈 点击左侧的'可视化'开始")
            st.balloons()

with col3:
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h3>👤 个人中心</h3>
        <p>管理您的个人信息和使用偏好设置</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入个人中心", key="to_profile"):
            st.sidebar.markdown("👈 点击左侧的'个人中心'开始")
            st.balloons()

# 6. 快速开始指南
st.markdown("""
<div style="background: white; padding: 2rem; border-radius: 15px; margin-top: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    <h3 style="color: #333; margin-bottom: 1rem;">🚀 快速开始</h3>
    <ol style="color: #666;">
        <li>点击左侧的"数据分析"页面</li>
        <li>上传您的CSV数据文件</li>
        <li>选择需要的分析功能</li>
        <li>查看分析结果和可视化图表</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# 7. 页面底部信息
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #333;">📫 联系我们</h3>
        <p style="color: #666;">邮箱：support@example.com</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #333;">🔗 快速链接</h3>
        <p style="color: #666;"><a href="#">使用文档</a></p>
        <p style="color: #666;"><a href="#">常见问题</a></p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h3 style="color: #333;">📢 公告</h3>
        <p style="color: #666;">系统将于本周六进行升级维护</p>
    </div>
    """, unsafe_allow_html=True)