import streamlit as st
import pandas as pd
from utils.helpers import create_chart, regenerate_chart, generate_code
from utils.agents import get_response
import os
import uuid
import re

st.set_page_config(layout="wide")  # 设置为宽屏模式

# 自定义CSS样式去除线框并调整界面样式
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
    }
    div[data-testid="stChatMessage"] {
        border: none;
        background-color: rgba(240, 242, 246, 0.6);
        border-radius: 10px;
    }
    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 2rem;
    }
    img {
        border-radius: 10px;
    }
    .code-buttons {
        display: flex;
        justify-content: flex-end;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("数据分析")

# 初始化session state变量，用于存储应用状态
if "messages" not in st.session_state:  # 存储对话历史
    st.session_state.messages = []
if "df" not in st.session_state:  # 存储数据框
    st.session_state.df = None
if "file_uploaded" not in st.session_state:  # 标记文件是否已上传
    st.session_state.file_uploaded = False
if "column_descriptions" not in st.session_state:  # 存储列描述信息
    st.session_state.column_descriptions = {}
if "descriptions_provided" not in st.session_state:  # 标记是否已提供列描述
    st.session_state.descriptions_provided = False
if "visualization_code" not in st.session_state:  # 统一存储可视化代码
    st.session_state.visualization_code = None
if "chart_status" not in st.session_state:  # 存储图表生成状态
    st.session_state.chart_status = None
if "file_path" not in st.session_state:  # 存储文件路径
    st.session_state.file_path = None
if "current_image" not in st.session_state:  # 存储当前生成的图片路径
    st.session_state.current_image = None
if "need_ai_response" not in st.session_state:  # 标记是否需要处理AI响应
    st.session_state.need_ai_response = False
if "current_input" not in st.session_state:  # 存储当前用户输入
    st.session_state.current_input = ""
if "is_thinking" not in st.session_state:  # 标记AI是否正在思考
    st.session_state.is_thinking = False
if "temp_response" not in st.session_state:  # 临时存储AI响应
    st.session_state.temp_response = ""
if "should_regenerate" not in st.session_state:  # 标记是否应该重新生成图表
    st.session_state.should_regenerate = False

# 仅在初始阶段显示文件上传组件
if not st.session_state.file_uploaded:
    uploaded_file = st.file_uploader("请上传您的CSV文件", type=['csv'])

    # 用户上传.csv文件
    if uploaded_file is not None:
        # 生成唯一文件名并保存上传的文件到本地
        file_name = f"data/{uuid.uuid4().hex}.csv"
        with open(file_name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 读取数据并初始化相关状态
        st.session_state.df = pd.read_csv(file_name) # 更新df
        st.session_state.file_uploaded = True # 更新文件上传状态
        st.session_state.file_path = file_name # 更新文件名
        # 为每一列创建空描述字典
        st.session_state.column_descriptions = {col: "" for col in st.session_state.df.columns}
        st.rerun()  # 重新运行应用以更新UI

# 用户填写描述表单
if st.session_state.file_uploaded and not st.session_state.descriptions_provided:
    # 显示数据预览
    st.subheader("数据预览")
    st.dataframe(st.session_state.df.head())
    
    # 创建列描述输入表单
    st.subheader("请为每列提供描述")
    
    with st.form("column_descriptions_form"):
        # 为每一列创建文本输入区域
        for col in st.session_state.df.columns:
            # 显示列名和数据类型
            col_type = st.session_state.df[col].dtype
            # 创建文本区域用于输入描述
            st.session_state.column_descriptions[col] = st.text_area(
                f"{col} ({col_type})", 
                st.session_state.column_descriptions.get(col, ""),
                placeholder="请输入对该列数据的描述..."
            )
        
        # 提交按钮
        submit_button = st.form_submit_button("提交列描述")
        
        # 处理提交操作
        if submit_button:
            st.session_state.descriptions_provided = True
            st.session_state.chart_status = "initial_generation"  # 设置图表状态为初次生成
            st.rerun()  # 重新运行应用以更新UI

# 当文件已上传且列描述已提供时，显示Claude模式界面
if st.session_state.file_uploaded and st.session_state.descriptions_provided:
    # 创建两列布局，调整比例为3:1，扩大左侧聊天区域
    left_col, right_col = st.columns([3, 1])
    
    # 显示数据预览和列描述信息（可折叠）
    with st.expander("数据信息", expanded=False):
        st.subheader("数据预览")
        st.dataframe(st.session_state.df.head())
        
        st.subheader("列描述")
        for col, desc in st.session_state.column_descriptions.items():
            st.write(f"**{col}**: {desc}")
    
    # 初次生成可视化图表
    if st.session_state.chart_status == "initial_generation":
        with st.spinner("正在生成数据可视化..."):
            # 首次生成可视化，使用create_chart
            code, image_path, result = create_chart(
                file_path=st.session_state.file_path,
                column_descriptions=st.session_state.column_descriptions
            )
            # 更新图表状态和代码
            if result == "图表生成成功":
                st.session_state.visualization_code = code
                st.session_state.current_image = image_path
                st.session_state.chart_status = "generated"
                # 添加系统消息到对话历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "我已经基于您提供的数据生成了可视化图表。您可以通过聊天询问更多分析或修改可视化。",
                    "image": st.session_state.current_image
                })
            st.rerun()  # 更新UI展示结果
    
    # 如果需要重新生成图表（用户点击了"重新生成图表"按钮）
    if st.session_state.should_regenerate:
        with st.spinner("正在重新生成图表..."):
            # 使用当前可视化代码重新生成图表
            success, image_path, result = regenerate_chart(st.session_state.visualization_code)
            
            if success:
                st.session_state.current_image = image_path
                st.session_state.should_regenerate = False
                st.session_state.chart_status = "generated"
                # 添加新的图表到聊天历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "我已经根据代码重新生成了可视化图表：",
                    "image": st.session_state.current_image
                })
                st.rerun()
            else:
                st.error(result)
                st.session_state.should_regenerate = False
    
    with left_col:
        # 创建一个固定高度的聊天容器
        chat_container = st.container(height=600)
        
        # 在聊天容器中显示所有消息
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    # 处理带有代码块的消息
                    content = message["content"]
                    if "```python" in content and message["role"] == "assistant":
                        # 分割内容，提取代码块前的文本
                        parts = content.split("```python")
                        st.write(parts[0])
                        
                        # 遍历所有代码块
                        for i, part in enumerate(parts[1:]):
                            if "```" in part:
                                code_part, text_part = part.split("```", 1)
                                # 显示代码块
                                st.code(code_part.strip(), language="python")
                                # 添加"应用代码"按钮
                                if st.button("应用此代码", key=f"apply_code_{i}_{hash(code_part)}"):
                                    st.session_state.visualization_code = code_part.strip()
                                    st.rerun()
                                # 显示代码块后的文本
                                st.write(text_part)
                            else:
                                # 如果没有结束标记，显示整个部分
                                st.code(part.strip(), language="python")
                    else:
                        # 常规消息直接显示
                        st.write(content)
                    
                    # 显示图片（如果有）
                    if "image" in message:
                        st.image(message["image"])
            
            # 如果AI正在思考，显示思考状态
            if st.session_state.is_thinking:
                with st.chat_message("assistant"):
                    st.write("正在思考...")
            
            # 如果需要AI响应
            if st.session_state.need_ai_response:
                # 获取AI助手回复
                data_context = {
                    "数据预览": st.session_state.df.head().to_string(),
                    "数据描述": st.session_state.df.describe().to_string(),
                    "列描述": st.session_state.column_descriptions,
                    "当前代码": st.session_state.visualization_code
                }
                
                # 创建空容器用于流式输出
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    
                    # 调用AI获取回复
                    response = get_response(
                        user_message=st.session_state.current_input, 
                        data_context=data_context, 
                        message_placeholder=message_placeholder
                    )
                    
                    # 存储响应到session state
                    st.session_state.temp_response = response
                
                # 添加助手回复到历史记录
                st.session_state.messages.append({"role": "assistant", "content": st.session_state.temp_response})
                
                # 重置标记
                st.session_state.need_ai_response = False
                st.session_state.current_input = ""
                st.session_state.is_thinking = False
                st.session_state.temp_response = ""
                
                # 重新运行应用以更新UI并避免重复添加消息
                st.rerun()
        
        # 在聊天容器下方添加一个表单，确保只有在提交时才处理输入
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("请输入您的问题", key="temp_input")
            submit_button = st.form_submit_button("发送")
            
            # 当表单提交时处理输入
            if submit_button and user_input:
                # 添加用户消息到历史记录
                st.session_state.messages.append({"role": "user", "content": user_input})
                # 添加一个标记，表示需要处理AI响应
                st.session_state.need_ai_response = True
                # 存储当前用户输入供AI使用
                st.session_state.current_input = user_input
                # 设置思考状态
                st.session_state.is_thinking = True
                # 重新运行应用以更新UI
                st.rerun()
    
    with right_col:
        # 创建可折叠的可视化画布，类似浮窗
        with st.expander("可视化代码", expanded=True):
            if st.session_state.visualization_code:
                st.code(st.session_state.visualization_code, language="python")
                
                col1, col2 = st.columns(2)
                # 添加代码复制按钮
                with col1:
                    if st.button("复制代码"):
                        st.write("代码已复制到剪贴板")
                
                # 添加重新生成图表按钮
                with col2:
                    if st.button("重新生成图表"):
                        st.session_state.should_regenerate = True
                        st.rerun()