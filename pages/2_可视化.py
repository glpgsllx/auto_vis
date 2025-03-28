import streamlit as st
import plotly.express as px

st.title("数据可视化")

if st.session_state.user_data is not None:
    df = st.session_state.user_data
    
    # 选择图表类型
    chart_type = st.selectbox(
        "选择图表类型",
        ["折线图", "柱状图", "散点图"]
    )
    
    # 选择数据列
    columns = df.columns.tolist()
    x_col = st.selectbox("选择X轴数据", columns)
    y_col = st.selectbox("选择Y轴数据", columns)
    
    # 绘制图表
    if chart_type == "折线图":
        fig = px.line(df, x=x_col, y=y_col)
        st.plotly_chart(fig)
    elif chart_type == "柱状图":
        fig = px.bar(df, x=x_col, y=y_col)
        st.plotly_chart(fig)
    elif chart_type == "散点图":
        fig = px.scatter(df, x=x_col, y=y_col)
        st.plotly_chart(fig)
else:
    st.info("请先在数据分析页面上传数据")