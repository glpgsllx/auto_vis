import streamlit as st

st.title("个人中心")

# 个人信息展示
col1, col2 = st.columns([1, 2])
with col1:
    st.image("https://placeholder.com/150", caption="头像")
with col2:
    st.write("用户名：测试用户")
    st.write("账号等级：VIP")

# 个人设置
st.subheader("个人设置")
settings = st.container()
with settings:
    st.toggle("开启通知")
    st.toggle("深色模式")
    theme = st.selectbox("界面主题", ["默认", "暗黑", "明亮"])