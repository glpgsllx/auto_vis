import streamlit as st
import pandas as pd
from utils.helpers import create_chart
from utils.agents import get_response
import os
import time

st.title("数据分析")

# 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None
if "chart_generated" not in st.session_state:
    st.session_state.chart_generated = False
if "chart_status" not in st.session_state:
    st.session_state.chart_status = None

# 如果还没有上传文件，显示文件上传器
uploaded_file = st.file_uploader("请上传您的CSV文件", type=['csv'])

if uploaded_file is not None and not st.session_state.file_uploaded:
    # 读取数据并存储在 session state 中
    st.session_state.df = pd.read_csv(uploaded_file)
    st.session_state.file_uploaded = True
    st.session_state.chart_status = "generating"

# 如果文件已上传，显示数据分析界面
if st.session_state.file_uploaded:
    # 显示数据预览
    st.subheader("数据预览")
    st.dataframe(st.session_state.df.head())
    
    # 创建进度显示窗口
    with st.expander("查看生成过程", expanded=True):
        # 1. 数据内容（始终显示）
        st.write("1. 数据内容：")
        st.text(st.session_state.df.to_string())
        
        # 2. 代码生成部分（始终显示）
        st.write("2. 生成可视化代码：")
        if st.session_state.chart_status == "generating":
            with st.spinner("正在生成代码..."):
                result = create_chart()
                if result == "图表生成成功":
                    st.session_state.chart_status = "generated"
        
        # 显示代码（只要存在就显示）
        if st.session_state.generated_code:
            st.code(st.session_state.generated_code, language="python")
        
        # 3. 图表显示部分
        st.write("3. 生成的可视化图表：")
        if os.path.exists('codeexe/answer.png'):
            st.image('codeexe/answer.png')
            if st.session_state.chart_status == "generated":
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "我已经生成了一个初步的数据可视化图表供您参考：",
                    "image": 'codeexe/answer.png'
                })
                st.session_state.chart_status = "completed"
        elif st.session_state.chart_status == "generated":
            st.error("图表生成失败，请重试")

    # 显示聊天界面
    st.subheader("对话")
    # 显示聊天记录
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "image" in message:
                st.image(message["image"])

    # 聊天输入
    if prompt := st.chat_input("请输入您的问题"):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 获取AI助手回复
        data_context = {
            "数据预览": st.session_state.df.head().to_string(),
            "数据描述": st.session_state.df.describe().to_string()
        }
        response = get_response(prompt, data_context)
        
        # 添加助手回复
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 重新运行以更新界面
        st.rerun()