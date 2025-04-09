import streamlit as st
import pandas as pd
from utils.helpers import create_chart, regenerate_chart, generate_code
from utils.stream_agents import get_streaming_response
from utils.db import connect_mysql, get_mysql_tables, get_mysql_table_data, close_mysql_connection
import os
import uuid
import re
import time

st.set_page_config(layout="wide")  

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
if "file_type" not in st.session_state:  # 存储文件类型
    st.session_state.file_type = None
if "mysql_connection" not in st.session_state:  # 存储MySQL连接
    st.session_state.mysql_connection = None
if "mysql_tables" not in st.session_state:  # 存储MySQL表列表
    st.session_state.mysql_tables = None
if "mysql_selected_table" not in st.session_state:
    st.session_state.mysql_selected_table = None
if "mysql_connection_form_submitted" not in st.session_state:
    st.session_state.mysql_connection_form_submitted = False
if "mysql_data_fetched" not in st.session_state:
    st.session_state.mysql_data_fetched = False
if "mysql_fetch_error" not in st.session_state:
    st.session_state.mysql_fetch_error = None
if "mysql_fetch_progress" not in st.session_state:
    st.session_state.mysql_fetch_progress = 0
if "mysql_fetch_status" not in st.session_state:
    st.session_state.mysql_fetch_status = ""
if "mysql_connection_info" not in st.session_state:
    st.session_state.mysql_connection_info = None
if "mysql_step" not in st.session_state:
    st.session_state.mysql_step = "connect"  # 可能的值: "connect", "select_table", "fetch_data", "data_loaded"

# 仅在初始阶段显示文件上传组件
if not st.session_state.file_uploaded:
    # 添加数据来源选择
    data_source = st.radio(
        "请选择数据来源",
        ["本地文件", "MySQL数据库"],
        index=0
    )
    
    if data_source == "本地文件":
        # 添加文件类型选择下拉菜单
        file_type = st.selectbox(
            "请选择数据文件类型",
            ["CSV", "Excel"],
            index=0
        )
        
        # 根据选择的文件类型显示不同的文件上传器
        if file_type == "CSV":
            uploaded_file = st.file_uploader("请上传您的CSV文件", type=['csv'])
        else:  # Excel
            uploaded_file = st.file_uploader("请上传您的Excel文件", type=['xlsx', 'xls'])

        # 用户上传文件
        if uploaded_file is not None:
            # 保存文件类型
            st.session_state.file_type = file_type
            
            # 根据文件类型确定文件扩展名
            file_extension = '.csv' if file_type == "CSV" else '.xlsx'
            
            # 生成唯一文件名并保存上传的文件到本地
            file_name = f"data/{uuid.uuid4().hex}{file_extension}"
            with open(file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 根据文件类型读取数据
            try:
                if file_type == "CSV":
                    st.session_state.df = pd.read_csv(file_name)
                else:  # Excel
                    # 添加更详细的调试信息
                    st.write(f"正在读取文件: {file_name}")
                    st.write(f"文件大小: {os.path.getsize(file_name)} 字节")
                    
                    # 尝试使用openpyxl引擎读取
                    try:
                        st.session_state.df = pd.read_excel(file_name, engine='openpyxl')
                    except Exception as e1:
                        st.write(f"使用openpyxl引擎失败: {str(e1)}")
                        # 尝试使用xlrd引擎
                        try:
                            st.session_state.df = pd.read_excel(file_name, engine='xlrd')
                        except Exception as e2:
                            st.write(f"使用xlrd引擎失败: {str(e2)}")
                            raise Exception(f"无法读取Excel文件。openpyxl错误: {str(e1)}, xlrd错误: {str(e2)}")
            except Exception as e:
                st.error(f"读取文件时出错: {str(e)}")
                st.error("请确保文件格式正确且包含数据")
                st.stop()
            
            # 更新状态
            st.session_state.file_uploaded = True  # 更新文件上传状态
            st.session_state.file_path = file_name  # 更新文件名
            # 为每一列创建空描述字典
            st.session_state.column_descriptions = {col: "" for col in st.session_state.df.columns}
            st.rerun()  # 重新运行应用以更新UI
    
    else:  # MySQL数据库
        # 初始化MySQL相关的session state变量
        if "mysql_connection" not in st.session_state:
            st.session_state.mysql_connection = None
        if "mysql_tables" not in st.session_state:
            st.session_state.mysql_tables = None
        if "mysql_selected_table" not in st.session_state:
            st.session_state.mysql_selected_table = None
        if "mysql_connection_form_submitted" not in st.session_state:
            st.session_state.mysql_connection_form_submitted = False
        if "mysql_data_fetched" not in st.session_state:
            st.session_state.mysql_data_fetched = False
        if "mysql_fetch_error" not in st.session_state:
            st.session_state.mysql_fetch_error = None
        if "mysql_fetch_progress" not in st.session_state:
            st.session_state.mysql_fetch_progress = 0
        if "mysql_fetch_status" not in st.session_state:
            st.session_state.mysql_fetch_status = ""
        if "mysql_connection_info" not in st.session_state:
            st.session_state.mysql_connection_info = None
        if "mysql_step" not in st.session_state:
            st.session_state.mysql_step = "connect"  # 可能的值: "connect", "select_table", "fetch_data", "data_loaded"
        
        # 步骤1: 连接数据库
        if st.session_state.mysql_step == "connect":
            st.subheader("步骤1: 连接MySQL数据库")
            
            # 创建输入字段
            col1, col2 = st.columns(2)
            
            with col1:
                host = st.text_input("服务器地址", value="localhost")
                port = st.number_input("端口", min_value=1, max_value=65535, value=3306)
                user = st.text_input("用户名")
                password = st.text_input("密码", type="password")
            
            with col2:
                database = st.text_input("数据库名")
                charset = st.selectbox(
                    "字符集",
                    ["utf8mb4", "utf8", "latin1", "gbk"],
                    index=0
                )
            
            # 连接按钮
            if st.button("连接数据库"):
                # 保存连接信息到session state
                st.session_state.mysql_connection_info = {
                    "host": host,
                    "port": port,
                    "user": user,
                    "password": password,
                    "database": database,
                    "charset": charset
                }
                
                # 尝试连接MySQL数据库
                connection, error = connect_mysql(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    charset=charset
                )
                
                if error:
                    st.error(f"连接失败: {error}")
                else:
                    # 保存连接对象到session state
                    st.session_state.mysql_connection = connection
                    
                    # 获取数据库中的所有表
                    tables = get_mysql_tables(connection)
                    
                    if not tables:
                        st.warning("数据库中没有找到表")
                    else:
                        # 保存表列表到session state
                        st.session_state.mysql_tables = tables
                        st.session_state.mysql_connection_form_submitted = True
                        st.session_state.mysql_step = "select_table"
                        st.success("数据库连接成功！请选择要分析的表。")
                        st.rerun()
        
        # 步骤2: 选择表
        elif st.session_state.mysql_step == "select_table":
            st.subheader("步骤2: 选择要分析的表")
            st.info(f"已连接到 {st.session_state.mysql_connection_info['database']} 数据库")
            
            # 显示表选择下拉菜单
            selected_table = st.selectbox("请选择要分析的表", st.session_state.mysql_tables)
            
            # 保存选择的表到session state
            st.session_state.mysql_selected_table = selected_table
            
            # 创建两列布局
            col1, col2 = st.columns(2)
            
            with col1:
                # 获取数据按钮
                if st.button("获取表数据"):
                    st.session_state.mysql_step = "fetch_data"
                    st.rerun()
            
            with col2:
                # 断开连接按钮
                if st.button("断开连接"):
                    # 关闭数据库连接
                    close_mysql_connection(st.session_state.mysql_connection)
                    # 清除session state
                    st.session_state.mysql_connection = None
                    st.session_state.mysql_tables = None
                    st.session_state.mysql_selected_table = None
                    st.session_state.mysql_connection_form_submitted = False
                    st.session_state.mysql_data_fetched = False
                    st.session_state.mysql_connection_info = None
                    st.session_state.mysql_step = "connect"
                    st.rerun()
        
        # 步骤3: 获取数据
        elif st.session_state.mysql_step == "fetch_data":
            st.subheader("步骤3: 获取表数据")
            st.info(f"正在从 {st.session_state.mysql_connection_info['database']} 数据库的 {st.session_state.mysql_selected_table} 表中获取数据")
            
            # 显示进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("正在连接数据库...")
                progress_bar.progress(10)
                
                # 检查连接是否有效
                if not st.session_state.mysql_connection or not st.session_state.mysql_connection.is_connected():
                    # 尝试重新连接
                    connection, error = connect_mysql(**st.session_state.mysql_connection_info)
                    
                    if error:
                        st.error(f"重新连接失败: {error}")
                        st.session_state.mysql_connection = None
                        st.session_state.mysql_tables = None
                        st.session_state.mysql_connection_form_submitted = False
                        st.session_state.mysql_step = "connect"
                        st.rerun()
                        st.stop()
                    else:
                        st.session_state.mysql_connection = connection
                
                status_text.text("正在获取表数据...")
                progress_bar.progress(30)
                
                # 从选定的表中获取数据，限制最大行数为1000
                try:
                    df, error = get_mysql_table_data(st.session_state.mysql_connection, st.session_state.mysql_selected_table, limit=1000)
                    
                    if error:
                        st.error(f"获取数据失败: {error}")
                        progress_bar.progress(100)
                        st.session_state.mysql_step = "select_table"
                        st.rerun()
                        st.stop()
                        
                    if df is None or df.empty:
                        st.error("获取到的数据为空")
                        progress_bar.progress(100)
                        st.session_state.mysql_step = "select_table"
                        st.rerun()
                        st.stop()
                        
                    progress_bar.progress(70)
                    status_text.text("数据处理中...")
                    progress_bar.progress(90)
                    
                    # 保存数据到session state
                    st.session_state.df = df
                    st.session_state.file_uploaded = True
                    st.session_state.file_type = "mysql"
                    # 为每一列创建空描述字典
                    st.session_state.column_descriptions = {col: "" for col in st.session_state.df.columns}
                    st.session_state.mysql_data_fetched = True
                    
                    status_text.text("数据获取成功！")
                    progress_bar.progress(100)
                    
                    # 显示数据预览
                    st.subheader("数据预览")
                    st.dataframe(st.session_state.df.head())
                    
                    # 显示数据统计信息
                    st.subheader("数据统计")
                    st.write(f"总行数: {len(st.session_state.df)}")
                    st.write(f"总列数: {len(st.session_state.df.columns)}")
                    
                    # 设置步骤为数据已加载
                    st.session_state.mysql_step = "data_loaded"
                    
                    # 添加继续按钮
                    if st.button("继续分析"):
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"获取表数据时发生错误: {str(e)}")
                    progress_bar.progress(100)
                    st.session_state.mysql_step = "select_table"
                    st.rerun()
                    st.stop()
                    
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
                progress_bar.progress(100)
                st.session_state.mysql_step = "select_table"
                st.rerun()
        
        # 步骤4: 数据已加载
        elif st.session_state.mysql_step == "data_loaded":
            st.subheader("数据已加载")
            st.success(f"已成功从 {st.session_state.mysql_connection_info['database']} 数据库的 {st.session_state.mysql_selected_table} 表中获取数据")
            
            # 显示数据预览
            st.subheader("数据预览")
            st.dataframe(st.session_state.df.head())
            
            # 显示数据统计信息
            st.subheader("数据统计")
            st.write(f"总行数: {len(st.session_state.df)}")
            st.write(f"总列数: {len(st.session_state.df.columns)}")
            
            # 添加断开连接按钮
            if st.button("断开连接"):
                # 关闭数据库连接
                close_mysql_connection(st.session_state.mysql_connection)
                # 清除session state
                st.session_state.mysql_connection = None
                st.session_state.mysql_tables = None
                st.session_state.mysql_selected_table = None
                st.session_state.mysql_connection_form_submitted = False
                st.session_state.mysql_data_fetched = False
                st.session_state.mysql_connection_info = None
                st.session_state.mysql_step = "connect"
                st.rerun()

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
            print(success)
            
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
                                # 添加"应用代码"按钮，使用消息在历史记录中的索引和代码块的索引来确保key的唯一性
                                button_key = f"apply_code_{st.session_state.messages.index(message)}_{i}_{len(code_part)}"
                                if st.button("应用此代码", key=button_key):
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
                    
                    # 使用新的真正流式响应
                    response = get_streaming_response(
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

# 在页面底部添加清理代码，确保MySQL连接被正确关闭
if st.session_state.mysql_connection:
    close_mysql_connection(st.session_state.mysql_connection)
    st.session_state.mysql_connection = None