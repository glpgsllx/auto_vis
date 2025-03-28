import streamlit as st

# 1. 页面基础配置
st.set_page_config(
    page_title="数据分析助手",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 设置页面样式
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .feature-box {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 初始化session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = {
        'username': '测试用户',
        'level': 'VIP',
        'usage_count': 0
    }

# 4. 侧边栏配置
with st.sidebar:
    st.image("https://placeholder.com/150", caption="Logo")
    st.markdown("---")

# 5. 主页面内容
st.markdown('<p class="big-font">欢迎使用数据分析助手 👋</p>', unsafe_allow_html=True)

# 6. 功能区展示
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

# 7. 快速开始指南
st.markdown("### 🚀 快速开始")
st.markdown("""
1. 点击左侧的"数据分析"页面
2. 上传您的CSV数据文件
3. 选择需要的分析功能
4. 查看分析结果和可视化图表
""")

# 8. 最近使用记录
if st.session_state.user_data is not None:
    st.markdown("### 📋 最近的分析")
    st.dataframe(st.session_state.user_data.head(3))

# 9. 页面底部信息
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 📫 联系我们")
    st.markdown("邮箱：support@example.com")
with col2:
    st.markdown("### 🔗 快速链接")
    st.markdown("- [使用文档]()")
    st.markdown("- [常见问题]()")
with col3:
    st.markdown("### 📢 公告")
    st.info("系统将于本周六进行升级维护")