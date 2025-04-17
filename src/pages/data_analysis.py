import streamlit as st
import pandas as pd
import os
import tempfile
import uuid
import re
import time
from src.auth.auth import is_logged_in, update_settings
from src.utils.data_processing import load_data_file, process_data, infer_column_descriptions
from src.visualization.code_generation import create_chart
from src.ai.llm_agent import get_response
from src.web_utils.ui_elements import display_sidebar_user_info, display_error, display_success, display_code, display_dataframe_info
from src.database.mysql import connect_mysql, get_mysql_tables, get_mysql_table_data, close_mysql_connection
from src.visualization.code_execution import execute_code
from src.ai.streaming import get_streaming_response
from src.database.chat_history_db import add_message_to_session, get_messages_by_session, update_session_name, get_session_details, update_session_data_context
from bson import ObjectId
import functools # Import functools for partial if needed, or use args/kwargs directly

st.set_page_config(
    page_title="数据分析 | 数据分析助手",
    page_icon="📊",
    layout="wide"
)

# --- Define the callback function --- 
def apply_code_callback(code_to_apply):
    if code_to_apply:
        print("调用回调函数！！！")
        print(f"[Apply Code Callback] Applying code:\n---\n{code_to_apply}\n---")
        st.session_state.visualization_code = code_to_apply
        st.session_state.chart_status = "applied" # Set status directly
        print(f"[Apply Code Callback] visualization_code and chart_status updated.")
        st.toast("代码已应用到右侧面板！")
    else:
        print("[Apply Code Callback] Error: Code to apply is empty.")
        st.toast("错误：无法应用空代码。", icon="🚨")

# Initialize the flag if it doesn't exist
if 'code_just_applied' not in st.session_state:
    st.session_state.code_just_applied = False

# 检查用户是否登录
if not is_logged_in():
    st.warning("请先登录")
    st.switch_page("pages/login.py")
    st.stop()

# --- 新增：检查当前是否有激活的会话ID ---
if "current_session_id" not in st.session_state or st.session_state.current_session_id is None:
    st.warning("没有活动的会话。请先选择一个历史会话或创建一个新会话。")
    st.switch_page("pages/session_manager.py")
    st.stop()

# 获取当前会话ID和名称 (此时它们应该已存在)
current_session_id = st.session_state.current_session_id
# 确保 current_session_name 也存在，如果不存在，可以尝试从数据库获取或设为默认值
if "current_session_name" not in st.session_state:
     session_details = db.chat_sessions.find_one({"_id": ObjectId(current_session_id)}, {"session_name": 1})
     if session_details:
         st.session_state.current_session_name = session_details.get("session_name", "会话")
     else:
        st.session_state.current_session_name = "会话" # 或从数据库查询名称

# 设置页面样式
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stButton>button {
        border-radius: 20px;
        height: 3em;
        background: linear-gradient(90deg, #FF6B6B 0%, #FF8E53 100%);
        border: none;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
    }
    .analysis-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #F0F2F6;
        border-left: 5px solid #7E57C2;
    }
    .ai-message {
        background-color: #F9F9F9;
        border-left: 5px solid #26A69A;
    }
    .chat-container {
        height: 60vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    .code-container {
        height: 60vh;
        overflow-y: auto;
        padding-left: 10px;
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

# 显示侧边栏
with st.sidebar:
    # 可以添加一个返回会话管理页面的按钮
    if st.button("返回会话列表"): # 使用不同的 key 以避免冲突
        st.switch_page("pages/session_manager.py")
    st.markdown("---")
    # 确保 user_info 存在
    if 'user_info' in st.session_state:
        display_sidebar_user_info(st.session_state.user_info)

# 页面标题
st.title("数据分析")

# 显示和编辑当前会话名称 
# 使用 session state 来控制编辑状态
if 'editing_session_name' not in st.session_state:
    st.session_state.editing_session_name = False

# 创建两列布局用于显示名称和编辑按钮
title_col1, title_col2 = st.columns([0.85, 0.15]) # 调整比例

with title_col1:
    if st.session_state.editing_session_name:
        # 显示文本输入框供编辑
        new_name = st.text_input(
            "编辑会话名称:",
            value=st.session_state.current_session_name,
            key="edit_session_name_input",
            label_visibility="collapsed" # 隐藏标签
        )
    else:
        # 显示当前会话名称
        st.subheader(f"当前会话: {st.session_state.current_session_name}")

with title_col2:
    if st.session_state.editing_session_name:
        # 显示保存和取消按钮
        save_col, cancel_col = st.columns(2)
        with save_col:
            if st.button("✔️", key="save_session_name", help="保存名称"):
                if new_name != st.session_state.current_session_name:
                    # 调用数据库更新
                    # 需要从 chat_history_db 导入 ObjectId 和 db 用于后备查询
                    from src.database.chat_history_db import db, ObjectId
                    success = update_session_name(current_session_id, new_name)
                    if success:
                        st.session_state.current_session_name = new_name
                        st.success("名称已更新")
                    else:
                        st.error("更新失败")
                st.session_state.editing_session_name = False
                st.rerun() # 更新UI
        with cancel_col:
            if st.button("✖️", key="cancel_edit_session_name", help="取消编辑"):
               st.session_state.editing_session_name = False
               st.rerun() # 更新UI
    else:
        # 显示编辑按钮
        if st.button("✏️", key="edit_session_name_button", help="编辑会话名称"):
            st.session_state.editing_session_name = True
            st.rerun() # 更新UI以显示输入框

st.markdown("---") # 分隔线

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = get_messages_by_session(current_session_id)
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

# --- 新增：会话管理状态 ---
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None # 初始时没有当前会话

# --- Modify Context Recovery ---
# 修改：在检查 flag 之前初始化 has_data_context 和 session_details
has_data_context = False
session_details = None

# Check the flag BEFORE potentially resetting states
if not st.session_state.code_just_applied:
    with st.spinner("正在加载会话信息..."): # Keep spinner for normal load
        session_details = get_session_details(current_session_id)
    
    if not session_details:
        st.error("无法加载会话信息，请返回会话列表重试。")
        if st.button("返回会话列表"):
            st.switch_page("pages/session_manager.py")
        st.stop()
    
    if session_details.get("data_source_details"):
        has_data_context = True # Set to True only if details exist
        st.session_state.loaded_context = session_details
        # Only preset if df not loaded to avoid overwriting
        if 'df' not in st.session_state or st.session_state.df is None:
            st.session_state.file_uploaded = True
            st.session_state.descriptions_provided = True
        # Restore other context details if not already present
        if 'column_descriptions' not in st.session_state and session_details["data_source_details"].get("column_descriptions"):
            st.session_state.column_descriptions = session_details["data_source_details"]["column_descriptions"]
        if 'file_type' not in st.session_state and session_details.get("data_source_type"):
            st.session_state.file_type = session_details["data_source_type"]
        if 'file_path' not in st.session_state and session_details["data_source_details"].get("stored_path"):
            st.session_state.file_path = session_details["data_source_details"]["stored_path"]
        if 'mysql_connection_info' not in st.session_state and session_details["data_source_details"].get("connection_info"):
            st.session_state.mysql_connection_info = session_details["data_source_details"]["connection_info"]
        if 'mysql_selected_table' not in st.session_state and session_details["data_source_details"].get("table_name"):
            st.session_state.mysql_selected_table = session_details["data_source_details"]["table_name"]
    else:
        # Initialize states if no context and not already set
        if 'file_uploaded' not in st.session_state: st.session_state.file_uploaded = False
        if 'descriptions_provided' not in st.session_state: st.session_state.descriptions_provided = False
        if 'df' not in st.session_state: st.session_state.df = None
        if 'column_descriptions' not in st.session_state: st.session_state.column_descriptions = {}
elif st.session_state.code_just_applied: # Added elif for clarity
    print("[Context Check] Skipping context recovery due to code_just_applied flag.")
    # Important: Reset the flag after checking it for this run
    st.session_state.code_just_applied = False
    if 'loaded_context' in st.session_state:
        session_details = st.session_state.loaded_context # Use stored context if available
        # Re-determine has_data_context based on stored context
        if session_details and session_details.get("data_source_details"):
            has_data_context = True
            # Restore minimal needed state if not already set
            if 'column_descriptions' not in st.session_state and session_details["data_source_details"].get("column_descriptions"):
                st.session_state.column_descriptions = session_details["data_source_details"]["column_descriptions"]
            # ... restore other essential states for rendering ...
            if 'file_type' not in st.session_state and session_details.get("data_source_type"):
                st.session_state.file_type = session_details["data_source_type"]
            if 'file_path' not in st.session_state and session_details["data_source_details"].get("stored_path"):
                st.session_state.file_path = session_details["data_source_details"]["stored_path"]
                  
    elif 'session_details' not in locals() or session_details is None: # If not available even from state
        # Fetch essential details if necessary (e.g., for name)
        print("[Context Check] Fetching minimal session details after flag check.") # Log this
        with st.spinner("加载基本会话信息..."): # Add spinner here too
            session_details = get_session_details(current_session_id)
        # Determine context based on freshly fetched details
        if session_details and session_details.get("data_source_details"):
            has_data_context = True
            # Restore minimal state again if needed
            if 'column_descriptions' not in st.session_state and session_details["data_source_details"].get("column_descriptions"):
                st.session_state.column_descriptions = session_details["data_source_details"]["column_descriptions"]


# Ensure session name is present after context check
if "current_session_name" not in st.session_state and session_details:
    st.session_state.current_session_name = session_details.get("session_name", "会话")

# 检查 df 是否已加载 (用于判断是否需要显示加载按钮或数据已加载)
df_loaded = 'df' in st.session_state and isinstance(st.session_state.df, pd.DataFrame) and not st.session_state.df.empty

if has_data_context and not df_loaded:
    # --- 情况1：有历史上下文，但数据尚未加载 --- 
    st.subheader("数据源信息")
    context_type = st.session_state.loaded_context.get("data_source_type", "未知")
    context_details = st.session_state.loaded_context.get("data_source_details", {})

    if context_type in ['csv', 'excel']:
        file_path = context_details.get("stored_path", "未知路径")
        # 尝试从路径中提取原始文件名
        try:
            original_filename = os.path.basename(file_path).split('_', 1)[-1]
        except Exception:
            original_filename = os.path.basename(file_path) # Fallback
             
        st.info(f"当前会话使用文件: **{original_filename}** (类型: {context_type.upper()}) Path: `{file_path}`")
        load_button_label = "加载数据文件"

        with st.expander("查看列描述"):
            descriptions = context_details.get("column_descriptions", {})
            if descriptions:
                for col, desc in descriptions.items():
                    st.write(f"**{col}**: {desc if desc else '-'}")
            else:
                st.write("无列描述信息。")

        # --- 加载数据按钮 ---
        if st.button(load_button_label, key="load_file_context", type="primary"):
            with st.spinner(f"正在加载文件 {original_filename}..."):
                try:
                    # 构建完整路径来读取
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                    full_path = os.path.join(project_root, "src", file_path)
                    print(f"Attempting to load file from: {full_path}") # Debug print

                    if not os.path.exists(full_path):
                        raise FileNotFoundError(f"数据文件未找到: {full_path}")

                    if context_type == "csv":
                        st.session_state.df = pd.read_csv(full_path)
                    else: # excel
                        try:
                            st.session_state.df = pd.read_excel(full_path, engine='openpyxl')
                        except Exception as e_openpyxl:
                            print(f"Failed loading Excel with openpyxl: {e_openpyxl}")
                            try:
                                st.session_state.df = pd.read_excel(full_path, engine='xlrd') # Try xlrd
                            except Exception as e_xlrd:
                                print(f"Failed loading Excel with xlrd: {e_xlrd}")
                                raise Exception(f"无法读取Excel文件 {original_filename}。请确保文件存在且格式正确。")

                    # 检查加载后的DataFrame
                    if isinstance(st.session_state.df, pd.DataFrame) and not st.session_state.df.empty:
                        time.sleep(0.5) # Short delay before rerun
                        st.rerun()
                    else:
                        st.error("加载数据失败或文件为空。")
                        if 'df' in st.session_state: del st.session_state.df 
                        
                except FileNotFoundError as fnf_error:
                    st.error(str(fnf_error))
                except Exception as e:
                    st.error(f"加载数据时出错: {e}")
                    if 'df' in st.session_state: del st.session_state.df 

    elif context_type == 'mysql':
        conn_info = context_details.get("connection_info", {})
        table_name = context_details.get("table_name", "未知表")
        st.info(f"当前会话使用 MySQL 表: **{table_name}** (来自数据库: {conn_info.get('database', '?')} at {conn_info.get('host','?')}) ")
        load_button_label = "连接并加载 MySQL 数据"

        with st.expander("查看列描述"):
            descriptions = context_details.get("column_descriptions", {})
            if descriptions:
                for col, desc in descriptions.items():
                    st.write(f"**{col}**: {desc if desc else '-'}")
            else:
                st.write("无列描述信息。")

        # --- 加载 MySQL 数据按钮 --- 
        st.warning("加载 MySQL 数据需要您重新确认连接信息并输入密码。")
        with st.form("mysql_reload_form"):
            st.write("**数据库连接信息 (无密码):**")
            st.json(conn_info) # Display saved connection info (no password)
            password = st.text_input("请输入数据库密码", type="password", key="mysql_reload_password")
            submitted = st.form_submit_button(load_button_label)

            if submitted:
                if not password:
                    st.error("请输入密码。")
                else:
                    full_conn_info = {**conn_info, "password": password}
                    with st.spinner(f"正在连接并加载表 {table_name}..."):
                        try:
                            connection, conn_error = connect_mysql(**full_conn_info)
                            if conn_error:
                                raise Exception(f"连接失败: {conn_error}")
                            
                            df, data_error = get_mysql_table_data(connection, table_name, limit=1000) # Use limit?
                            close_mysql_connection(connection) # Close connection after fetching
                            
                            if data_error:
                                raise Exception(f"获取数据失败: {data_error}")
                            
                            if df is None or df.empty:
                                raise Exception("从数据库获取的数据为空。")
                                
                            st.session_state.df = df
                            # --- 修改：确保保存包含密码的完整连接信息 --- 
                            st.session_state.mysql_connection_info = full_conn_info # 使用包含密码的版本
                            st.session_state.mysql_selected_table = table_name
                            st.session_state.mysql_data_fetched = True
                            st.session_state.mysql_step = "data_loaded"
                            # Don't show success toast here
                            time.sleep(0.5)
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"加载 MySQL 数据时出错: {e}")
                            if 'df' in st.session_state: del st.session_state.df 

    else:
        st.error("无法识别的数据源上下文。请尝试重新上传数据或联系管理员。")

# --- 情况2：没有历史上下文，需要用户上传或连接 --- 
elif not st.session_state.get('file_uploaded'): # Use .get() for safety
     # 包含整个 if data_source == "本地文件": ... else: # MySQL数据库 ... end 的块
     # (确保这里的代码是完整的) 
    data_source = st.radio(
        "请选择数据来源",
        ["本地文件", "MySQL数据库"],
        index=0, key="data_source_selection"
    )
    if data_source == "本地文件":
        # (文件上传UI...)
        file_type = st.selectbox("请选择数据文件类型", ["CSV", "Excel"], index=0, key="file_type_selection")
        uploaded_file = st.file_uploader(f"请上传您的{file_type}文件", type=['csv'] if file_type == "CSV" else ['xlsx', 'xls'], key="file_uploader_widget")
        if uploaded_file is not None:
            try:
                original_filename = uploaded_file.name
                user_id = st.session_state.user_info['username']
                session_id = current_session_id
                file_extension = os.path.splitext(original_filename)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                upload_dir_relative = os.path.join("user_uploads", str(user_id), str(session_id))
                stored_path_relative = os.path.join(upload_dir_relative, unique_filename)
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                upload_dir_full = os.path.join(project_root, "src", upload_dir_relative)
                stored_path_full = os.path.join(upload_dir_full, unique_filename)
                os.makedirs(upload_dir_full, exist_ok=True)
                with open(stored_path_full, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                print(f"文件已保存到: {stored_path_full}")
                if file_type == "CSV":
                    st.session_state.df = pd.read_csv(stored_path_full)
                else:
                    try:
                        st.session_state.df = pd.read_excel(stored_path_full, engine='openpyxl')
                    except Exception as e1:
                        print(f"使用openpyxl读取失败: {e1}")
                        st.session_state.df = pd.read_excel(stored_path_full, engine='xlrd')
                file_info_content = {
                    "original_filename": original_filename,
                    "stored_path": stored_path_relative.replace(os.sep, '/'),
                    "file_size": uploaded_file.size,
                    "mime_type": uploaded_file.type
                }
                add_message_to_session(
                    session_id=session_id,
                    username=user_id,
                    role="user",
                    content_type="file_upload",
                    content=file_info_content
                )
                st.session_state.file_uploaded = True
                st.session_state.file_path = stored_path_relative.replace(os.sep, '/')
                st.session_state.file_type = file_type.lower() # Use lower case type
                st.session_state.column_descriptions = {col: "" for col in st.session_state.df.columns}
                st.session_state.messages = get_messages_by_session(session_id)
                st.success(f"文件 '{original_filename}' 上传并加载成功！")
                st.rerun()
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                st.error(f"处理上传文件时出错: {str(e)}")
                if 'df' in st.session_state: del st.session_state.df
                st.session_state.file_uploaded = False
                st.stop()
    else: # MySQL数据库
        # (MySQL 连接 UI 逻辑 - 保持原样或根据需要调整)
        if 'mysql_step' not in st.session_state: st.session_state.mysql_step = "connect"
         
        if st.session_state.mysql_step == "connect":
            st.subheader("步骤1: 连接MySQL数据库")
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("服务器地址", value="localhost", key="mysql_host")
                port = st.number_input("端口", min_value=1, max_value=65535, value=3306, key="mysql_port")
                user = st.text_input("用户名", key="mysql_user")
                password = st.text_input("密码", type="password", key="mysql_pass")
            with col2:
                database = st.text_input("数据库名", key="mysql_db")
                # 可以添加 charset 输入，如果需要
                charset = st.text_input("字符集 (可选)", value="utf8mb4", key="mysql_charset")

            if st.button("连接并获取表列表", key="mysql_connect_btn"):
                conn_info = {"host": host, "port": port, "user": user, "password": password, "database": database}
                if charset: # 添加 charset 到连接信息
                    conn_info["charset"] = charset
                
                connection = None # Initialize connection variable
                try:
                    with st.spinner("正在连接数据库并获取表列表..."):
                        connection, error = connect_mysql(**conn_info)
                        if error:
                            st.error(f"连接失败: {error}")
                        else:
                            tables = get_mysql_tables(connection)
                            if not tables:
                                st.warning("数据库中没有找到表。")
                            else:
                                st.session_state.mysql_tables = tables
                                # --- 修改：只保存不含密码的连接信息 ---
                                safe_conn_info = {k: v for k, v in conn_info.items() if k != 'password'}
                                st.session_state.mysql_connection_info = safe_conn_info 
                                st.session_state.mysql_step = "select_table"
                                st.success("数据库连接成功！请选择要分析的表。")
                                # --- 修改：不再存储连接对象，获取完表就关闭 ---
                                # del st.session_state['mysql_connection'] # 移除旧代码
                                st.rerun() # 跳转到下一步
                except Exception as e:
                     st.error(f"连接或获取表列表时发生意外错误: {e}")
                finally:
                    # --- 新增：无论如何都尝试关闭连接 ---
                    if connection:
                        close_mysql_connection(connection)

        elif st.session_state.mysql_step == "select_table":
            st.subheader("步骤2: 选择要分析的表")
            if 'mysql_connection_info' in st.session_state: # 检查是否有连接信息
                st.info(f"已连接到 {st.session_state.mysql_connection_info.get('database','?')} 数据库 (Host: {st.session_state.mysql_connection_info.get('host','?')})")
                selected_table = st.selectbox(
                    "请选择要分析的表", 
                    st.session_state.get('mysql_tables', []), # 使用 .get 防错
                    key="mysql_table_select"
                )
                # 及时更新选择的表名到session_state
                if selected_table: 
                    st.session_state.mysql_selected_table = selected_table
                
                col1, col2 = st.columns(2)
                with col1:
                    # --- 修改：按钮触发 fetch_data 状态 ---
                    if st.button("下一步：获取表数据", key="mysql_goto_fetch_btn"): 
                        if selected_table:
                            st.session_state.mysql_step = "fetch_data"
                            st.rerun()
                        else:
                            st.warning("请先选择一个表。")
                with col2:
                    # --- 修改：返回连接步骤 ---
                    if st.button("重新连接", key="mysql_reconnect_btn"): 
                        # 清理与MySQL选择和获取相关的状态
                        keys_to_clear = ['mysql_tables', 'mysql_selected_table', 'mysql_connection_info', 'mysql_step', 'mysql_data_fetched', 'df']
                        for key in keys_to_clear:
                            if key in st.session_state: del st.session_state[key]
                        st.session_state.mysql_step = "connect" # 设置回连接步骤
                        st.rerun()
            else:
                st.warning("缺少数据库连接信息，请返回上一步重新连接。")
                if st.button("返回连接步骤"):
                     st.session_state.mysql_step = "connect"
                     st.rerun()
        
        elif st.session_state.mysql_step == "fetch_data":
            st.subheader("步骤3: 获取表数据")
            # --- 重写 fetch_data 逻辑 ---
            if 'mysql_connection_info' not in st.session_state or 'mysql_selected_table' not in st.session_state:
                st.error("缺少数据库连接信息或未选择表。请返回重新操作。")
                st.session_state.mysql_step = "connect" # 或者 select_table? connect 更安全
                st.rerun()
                st.stop()

            conn_info_safe = st.session_state.mysql_connection_info
            selected_table = st.session_state.mysql_selected_table
            
            st.info(f"准备从 {conn_info_safe.get('database','?')} 的 {selected_table} 表获取数据")
            st.warning("需要再次输入数据库密码以确认操作。")
            
            with st.form("mysql_fetch_form"):
                password = st.text_input("请输入数据库密码", type="password", key="mysql_fetch_password")
                limit_rows = st.number_input("限制加载行数 (0表示不限制)", min_value=0, value=1000, key="mysql_limit_rows")
                submitted = st.form_submit_button("获取数据")

                if submitted:
                    if not password:
                        st.error("请输入密码。")
                    else:
                        # 构建完整的连接信息 (包括密码)
                        full_conn_info = {**conn_info_safe, "password": password}
                        connection = None # Initialize connection
                        try:
                            with st.spinner(f"正在连接并加载表 {selected_table}..."):
                                connection, conn_error = connect_mysql(**full_conn_info)
                                if conn_error:
                                    raise Exception(f"连接失败: {conn_error}")
                                
                                limit = limit_rows if limit_rows > 0 else None
                                df, data_error = get_mysql_table_data(connection, selected_table, limit=limit) 
                                
                                if data_error:
                                    raise Exception(f"获取数据失败: {data_error}")
                                
                                if df is None or df.empty:
                                    st.warning("从数据库获取的数据为空。")
                                    # 即使为空也认为是成功获取了，可以继续分析空数据框？或者报错？
                                    # 这里选择继续，但标记 df 为空
                                    st.session_state.df = pd.DataFrame() # 创建空 DF
                                else:
                                    st.session_state.df = df

                                # --- 成功获取数据后的状态更新 ---
                                st.session_state.file_uploaded = True # 标记数据已"上传" (概念上)
                                st.session_state.file_type = "mysql" 
                                # 初始化列描述 (即使是空df)
                                st.session_state.column_descriptions = {col: "" for col in st.session_state.df.columns}
                                # --- 修改：保存包含密码的完整连接信息 --- 
                                st.session_state.mysql_connection_info = full_conn_info 
                                st.session_state.mysql_data_fetched = True
                                st.session_state.mysql_step = "data_loaded" # 进入显示和描述阶段
                                
                                # 记录 file_upload 类型的消息到历史记录
                                # --- 修改：保存到消息记录时，仍然用不含密码的版本 --- 
                                conn_info_for_log = {k: v for k, v in full_conn_info.items() if k != 'password'}
                                mysql_info_content = {
                                    "connection_info": conn_info_for_log,
                                    "table_name": selected_table,
                                    "rows_loaded": len(st.session_state.df)
                                }
                                add_message_to_session(
                                    session_id=current_session_id,
                                    username=st.session_state.user_info['username'],
                                    role="user", # 认为是用户操作触发
                                    content_type="mysql_connection", # 使用特定类型
                                    content=mysql_info_content
                                )
                                
                                st.success("数据获取成功！")
                                time.sleep(0.5) # 短暂延迟
                                st.rerun() # Rerun 进入下一步 (描述或聊天)
                        
                        except Exception as e:
                            st.error(f"获取 MySQL 数据时出错: {e}")
                            # --- 修改：错误时不改变步骤，让用户看到错误 ---
                            # del st.session_state.mysql_step # 不改变步骤
                            if 'df' in st.session_state: del st.session_state.df # 清理可能的部分数据
                        finally:
                            # --- 新增：确保关闭连接 ---
                            if connection:
                                close_mysql_connection(connection)

        elif st.session_state.mysql_step == "data_loaded":
            # --- data_loaded 逻辑基本不变，用于显示成功信息和 df.head() ---
            st.subheader("MySQL 数据已加载")
            st.success(f"已从表 '{st.session_state.mysql_selected_table}' 加载数据。")
            if 'df' in st.session_state and isinstance(st.session_state.df, pd.DataFrame) and not st.session_state.df.empty:
                st.dataframe(st.session_state.df.head())
            elif 'df' in st.session_state: # 如果 df 是空 DataFrame
                 st.info("加载的数据为空。")
            else: # 如果 df 不存在 (理论上不应发生在此状态)
                st.warning("数据框未加载。")

            # --- 修改：不再需要rerun，直接进入列描述或聊天 ---
            # 如果 file_uploaded 为 True，后续逻辑会自动进入列描述阶段
            # st.session_state.file_uploaded = True # 已在 fetch_data 中设置
            # st.rerun() # 移除这里的 rerun
            # 让页面自然流转到下面的 elif ... descriptions_provided ...

# --- 情况3：数据已上传/加载，但未提供列描述 ---
elif st.session_state.get('file_uploaded') and not st.session_state.get('descriptions_provided'):
    # 包含整个 "用户填写描述表单" 的逻辑
    st.subheader("请为每列提供描述")
    with st.form("column_descriptions_form"):
        if 'column_descriptions' not in st.session_state: st.session_state.column_descriptions = {}
        if 'df' in st.session_state and isinstance(st.session_state.df, pd.DataFrame):
            for col in st.session_state.df.columns:
                col_type = st.session_state.df[col].dtype
                st.session_state.column_descriptions[col] = st.text_area(
                    f"{col} ({col_type})", 
                    st.session_state.column_descriptions.get(col, ""),
                    placeholder="请输入对该列数据的描述...",
                    key=f"desc_{col}" # Add key
                )
        else:
            st.warning("无法加载数据列以提供描述。")
            
        submit_button = st.form_submit_button("提交列描述")
        if submit_button:
            try:
                data_source_type = None
                data_source_details = {}
                descriptions = st.session_state.column_descriptions
                source_type_raw = st.session_state.get('file_type')
                if source_type_raw in ['csv', 'excel']:
                    data_source_type = source_type_raw
                    stored_path = st.session_state.get('file_path')
                    if stored_path:
                        data_source_details = {"stored_path": stored_path, "column_descriptions": descriptions}
                    else: raise ValueError("文件路径未找到")
                elif source_type_raw == 'mysql':
                    data_source_type = 'mysql'
                    conn_info = st.session_state.get('mysql_connection_info')
                    table_name = st.session_state.get('mysql_selected_table')
                    if conn_info and table_name:
                        safe_conn_info = {k: v for k, v in conn_info.items() if k != 'password'}
                        data_source_details = {"connection_info": safe_conn_info, "table_name": table_name, "column_descriptions": descriptions}
                    else: raise ValueError("MySQL 信息未找到")
                else: raise ValueError(f"未知数据源类型 '{source_type_raw}'")
                update_success = update_session_data_context(current_session_id, data_source_type, data_source_details)
                if not update_success: st.toast("警告：未能保存数据源上下文信息。", icon="⚠️")
                else: st.toast("数据源上下文已保存。", icon="✅")
                st.session_state.descriptions_provided = True
                st.session_state.chart_status = "initial_generation"
                st.rerun()
            except Exception as e:
                st.error(f"保存数据上下文时出错: {e}")
                st.stop()

# --- 情况4：上下文已恢复或已完成加载和描述 -> 显示聊天界面 ---
elif st.session_state.get('file_uploaded') and st.session_state.get('descriptions_provided') and df_loaded:
    print("[Render Check] Entering Case 4: Chat Interface Display")
    
    # Initial Chart Generation (if needed) - NO RERUN at the end
    if st.session_state.get('chart_status') == "initial_generation":
        with st.spinner("正在生成初始数据可视化..."):
            # --- 确保传递了 data_source_type --- 
            code, image_path, result = create_chart(
                user_id=st.session_state.user_info['username'],
                session_id=current_session_id,
                df=st.session_state.df,
                column_descriptions=st.session_state.column_descriptions,
                data_source_type=st.session_state.get('file_type'), # Pass the type
                persistent_file_path=st.session_state.get('file_path') # Pass the path
            )
            if result == "图表生成成功" and code and image_path:
                 st.session_state.visualization_code = code
                 st.session_state.current_image = image_path
                 st.session_state.chart_status = "generated"

                 # --- 修改：先手动添加消息到 state，再存DB ---
                 initial_message_content = "我已经基于您提供的数据生成了可视化图表。您可以通过聊天询问更多分析或修改可视化。"
                 # 构建消息结构 (与数据库保存的 image 类型一致)
                 initial_message = {
                     "role": "assistant",
                     "content_type": "image", 
                     "content": {"path": image_path, "text": initial_message_content}, # Add text part to content
                     "metadata": {"code": code},
                     "_id": f"initial_{uuid.uuid4().hex}" # Fake ID for immediate display
                 }
                 # Ensure messages list exists
                 if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
                     st.session_state.messages = []
                 st.session_state.messages.append(initial_message) # Add to state first

                 # 再尝试存入数据库
                 if current_session_id:
                     add_success = add_message_to_session(
                         session_id=current_session_id,
                         username=st.session_state.user_info['username'],
                         role="assistant",
                         content_type="image", # Save as image type
                         content={"path": image_path, "text": initial_message_content}, # Save path and text
                         metadata={"code": code}
                     )
                     if add_success:
                         print("[Initial Chart Gen] Initial message saved to DB successfully.")
                     else:
                         print("[Initial Chart Gen] Failed to save initial message to DB.")
            else:
                st.error(f"图表生成失败: {result}")
                st.session_state.chart_status = "failed"

    # Regenerate Chart Logic - Keep st.rerun() here
    if st.session_state.get('should_regenerate'):
        with st.spinner("正在重新生成图表..."):
             # --- 修改：直接从加载的上下文获取数据类型 ---
             # data_type = st.session_state.get('file_type') # 不再使用这个
             loaded_context = st.session_state.get('loaded_context')
             if loaded_context and loaded_context.get("data_source_type"):
                 data_type = loaded_context.get("data_source_type")
             else:
                 # 后备方案：尝试从 session_state 获取 (如果上面失败)
                 data_type = st.session_state.get('file_type')
                 if not data_type:
                     st.error("错误：无法确定重新生成图表所需的数据源类型！")
                     success = False ; image_path = None # Set default fail state
                     print("[Regen Check] Error: data_type is None, cannot proceed.")
                 else:
                     print("[Regen Check] Warning: data_type obtained from session_state as fallback.")

             # 只有在 data_type 有效时才继续获取路径和代码
             if data_type:
                 # --- 获取 persistent_path --- 
                 persistent_path = None # Initialize path
                 if data_type in ['csv', 'excel']: # 只有文件类型需要路径
                     if loaded_context and loaded_context.get("data_source_details") and loaded_context["data_source_details"].get("stored_path"):
                         persistent_path = loaded_context["data_source_details"]["stored_path"]
                     else:
                         # 后备方案：尝试从 session state 获取
                         persistent_path = st.session_state.get('file_path')
                         if not persistent_path:
                             st.error("错误：无法确定重新生成图表所需的数据文件路径！")
                             success = False ; image_path = None # Set fail state
                             print("[Regen Check] Error: persistent_path is None for file type, cannot proceed.")
                         else:
                             print("[Regen Check] Warning: persistent_path obtained from session_state as fallback.")
                 # else: # 对于 mysql 等类型，persistent_path 保持 None

                 print(f"[Regen Check] Determined data_type: {data_type}")
                 print(f"[Regen Check] Determined persistent_path: {persistent_path}") # Log the path

                 # 获取要运行的代码
                 code_to_run = st.session_state.get('visualization_code')

                 # 只有在路径有效(或不需要) 且 代码存在 时才执行
                 path_ok = (data_type not in ['csv', 'excel']) or persistent_path
                 if path_ok and code_to_run:
                     print(f"[Regen Check] Path OK, proceeding to execute code: {code_to_run[:100]}...") # Log before exec
                     success, image_path = execute_code(
                         code_to_run, 
                         user_id=st.session_state.user_info['username'], # user_id 在外部已获取和检查
                         session_id=current_session_id, 
                         data_source_type=data_type,
                         persistent_file_path=persistent_path # 使用新获取的 path
                     )
                     print(f"[Regen Check] Execute code result: {success}, image_path: {image_path}")
                     if success:
                         st.session_state.current_image = image_path
                         st.session_state.chart_status = "generated"
                         regenerated_message_content = "我已经根据您的要求重新生成了可视化图表："
                         regen_message = {"role": "assistant","content_type": "image","content": {"path": image_path, "text": regenerated_message_content},"metadata": {"code": code_to_run}}
                         if "messages" not in st.session_state: st.session_state.messages = []
                         st.session_state.messages.append(regen_message) # Append first
                         add_message_to_session(session_id=current_session_id, username=st.session_state.user_info['username'], role="assistant", content_type="image", content=regen_message["content"], metadata=regen_message["metadata"])
                     else: 
                         # execute_code 内部应该已经打印了错误，这里可以只标记失败
                         st.error("图表生成失败，请查看终端日志获取详细信息。")
                         st.session_state.chart_status = "failed"
                 elif not path_ok:
                     # 如果是因为路径问题失败，这里无需再显示错误，上面已经显示过了
                     st.session_state.chart_status = "failed" # Mark as failed
                 else: # code_to_run is None
                     st.error("没有可用于重新生成的代码。")
                     st.session_state.chart_status = "failed" # Mark as failed
             # else: # 如果 data_type 获取失败，上面已经处理了错误
             
             # 重置标志位 (无论成功与否都应重置)
             st.session_state.should_regenerate = False

    # --- Chat Interface Layout --- 
    left_col, right_col = st.columns([3, 1])
    with st.expander("数据信息", expanded=False):
        st.subheader("数据预览")
        if 'df' in st.session_state and isinstance(st.session_state.df, pd.DataFrame):
            st.dataframe(st.session_state.df.head())
        else:
            st.warning("数据尚未加载或加载失败。")
        st.subheader("列描述")
        if 'column_descriptions' in st.session_state and st.session_state.column_descriptions:
            for col, desc in st.session_state.column_descriptions.items():
                st.write(f"**{col}**: {desc if desc else '-'}")
        else:
            st.write("无列描述信息。")
    
    with left_col:
        chat_container = st.container(height=600)
        with chat_container:
            if isinstance(st.session_state.get("messages"), list) and st.session_state.messages:
                # --- 添加日志：打印最后一条消息，确认内容 --- 
                print(f"[Chat Display] Content of last message before loop: {st.session_state.messages[-1].get('content')}")
                # ---------------------------------------- 
                try: # Add try-except around path logic
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                    src_root = os.path.join(project_root, "src")
                except NameError: src_root = os.path.abspath("./src"); print("Warning: __file__ not found...")

                for message_index, message in enumerate(st.session_state.messages): # Add index
                    with st.chat_message(message["role"]):
                        content_type = message.get('content_type', 'text')
                        content = message.get('content')
                        metadata = message.get('metadata', {})
                        message_id = message.get('_id', uuid.uuid4().hex)
                        role = message.get('role') # Get role

                        print(f"[Display Loop {message_index}] Role: {role}, Type: {content_type}, Content Start: {str(content)[:50]}...") # Log each message start

                        if content_type == 'text' and isinstance(content, str):
                            is_assistant = (role == "assistant")
                            # --- 修改：使用 Regex 查找代码块 --- 
                            code_block_pattern = r"```(?:python|py)?\s*\n?(.*?)\s*\n?```"
                            match = re.search(code_block_pattern, content, re.DOTALL)

                            print(f"  [Check Code Block] Is Assistant: {is_assistant}, Regex Match: {'Found' if match else 'None'}")
                            # --------------------------------------- 
                            if is_assistant and match: # If it's an assistant message AND regex found a block
                                print(f"  [Code Block Found via Regex] Trying to parse content.")
                                try:
                                    # Extract text before, code, and text after
                                    text_before = content[:match.start()].strip()
                                    display_code = match.group(1).strip() # Extract code from group 1
                                    text_after = content[match.end():].strip()

                                    # Display parts
                                    if text_before: st.write(text_before)
                                    print(f"  [Code Parsed] Extracted Code Length: {len(display_code)}")
                                    if display_code:
                                        st.code(display_code, language="python")
                                        button_key = f"apply_code_{message_id}_{message_index}" # Use index too for uniqueness
                                        st.button(
                                            "应用此代码",
                                            key=button_key,
                                            on_click=apply_code_callback,
                                            args=(display_code,)
                                        )
                                    else: print("  [Code Parsed Warning] Extracted code was empty.")
                                    if text_after: st.write(text_after)

                                except Exception as parse_e:
                                     print(f"  [Code Parse Error] Error parsing regex-found code block: {parse_e}")
                                     st.write(content) # Fallback to showing raw content on error
                            else:
                                # Display as normal text if not assistant or no code block found by regex
                                st.write(content)
                        elif content_type == 'image':
                            image_path_relative = content.get('path') if isinstance(content, dict) else None
                            associated_text = content.get('text') if isinstance(content, dict) else None
                            code_str = metadata.get('code') if isinstance(metadata, dict) else None

                            if associated_text:
                                st.write(associated_text)

                            if image_path_relative:
                                try:
                                    # --- 修改：构建完整路径进行检查和打开 ---
                                    full_image_path = os.path.join(src_root, image_path_relative)
                                    print(f"[Image Display] Checking for image at: {full_image_path}") # DEBUG Log
                                    if os.path.exists(full_image_path):
                                        with open(full_image_path, 'r', encoding='utf-8') as f:
                                            svg_content = f.read()
                                        if "svg_scale" not in st.session_state: st.session_state.svg_scale = {}
                                        if full_image_path not in st.session_state.svg_scale: st.session_state.svg_scale[full_image_path] = 1.0 # Use full path as key?
                                        if '<svg ' in svg_content:
                                            w_match = re.search(r'width="([^"]*)"', svg_content)
                                            h_match = re.search(r'height="([^"]*)"', svg_content)
                                            o_w = w_match.group(1) if w_match else "600"
                                            o_h = h_match.group(1) if h_match else "400"
                                            o_w = re.sub(r'[^0-9.]', '', o_w)
                                            o_h = re.sub(r'[^0-9.]', '', o_h)
                                            try:
                                                scale = st.session_state.svg_scale[full_image_path]
                                                s_w = float(o_w)*scale
                                                s_h = float(o_h)*scale
                                                svg_content = re.sub(r'width="[^"]*"', f'width="{s_w}px"', svg_content)
                                                svg_content = re.sub(r'height="[^"]*"', f'height="{s_h}px"', svg_content)
                                            except ValueError:
                                                pass
                                        st.markdown(svg_content, unsafe_allow_html=True)

                                        cols = st.columns(3)
                                        with cols[0]:
                                            if st.button("+", key=f"zoom_in_{message_id}"):
                                                st.session_state.svg_scale[full_image_path] *= 1.2; st.rerun()
                                        with cols[1]:
                                            if st.button("-", key=f"zoom_out_{message_id}"):
                                                st.session_state.svg_scale[full_image_path] *= 0.8; st.rerun()
                                        with cols[2]:
                                            with open(full_image_path, "rb") as file: # Use full path here
                                                btn = st.download_button(label="down", data=file, file_name=f"chart_{message_id}.svg", mime="image/svg+xml", key=f"download_{message_id}")
                                    else:
                                        st.warning(f"图表文件未找到: {full_image_path} (Relative path: {image_path_relative})")
                                except Exception as e:
                                    st.error(f"显示图表时出错: {e}")
                        elif content_type == 'file_upload':
                            if isinstance(content, dict):
                                st.info(f"文件上传: {content.get('original_filename', '?')}")
                            else:
                                st.info("文件上传记录")
                        else:
                            st.write(f"未知消息类型 '{content_type}': {content}")
            else:
                st.info("开始您的分析对话吧！")

            if st.session_state.get('is_thinking'):
                with st.chat_message("assistant"): st.write("正在思考...")
            
            # 对话
            if st.session_state.get('need_ai_response'):
                # --- 修改：构建新的 data_context 和 history --- 
                
                # 1. 构建 data_context (检查这部分)
                data_context = {
                    "column_descriptions": st.session_state.get('column_descriptions', {}),
                    "current_code": st.session_state.get('visualization_code')
                }
                loaded_context_details = st.session_state.get('loaded_context')
                if loaded_context_details:
                    data_context["data_source_type"] = loaded_context_details.get("data_source_type")
                    data_context["data_source_details"] = loaded_context_details.get("data_source_details")
                    # 如果 loaded_context 中有更权威的 descriptions，应该覆盖 session_state 中的
                    if loaded_context_details.get("data_source_details", {}).get("column_descriptions"):
                        data_context["column_descriptions"] = loaded_context_details["data_source_details"]["column_descriptions"]
                        print("[AI Context Check] Using column descriptions loaded from session context.") # Add log
                    else:
                        print("[AI Context Check] Using column descriptions from current session state (if any).") # Add log
                else:
                    data_context["data_source_type"] = st.session_state.get('file_type')
                    if data_context["data_source_type"] in ['csv', 'excel']:
                        data_context["data_source_details"] = {"stored_path": st.session_state.get('file_path')}
                    elif data_context["data_source_type"] == 'mysql':
                         data_context["data_source_details"] = {
                             "connection_info": st.session_state.get('mysql_connection_info'),
                             "table_name": st.session_state.get('mysql_selected_table')
                         }
                    print("Warning: Using possibly incomplete data context from session state as loaded_context was missing.")

                # 2. 构建 history
                chat_history_for_llm = []
                if isinstance(st.session_state.get("messages"), list):
                    for msg in st.session_state.messages:
                        role = msg.get('role'); content_type = msg.get('content_type', 'text'); content = msg.get('content')
                        text_content = None
                        if content_type == 'text' and isinstance(content, str): text_content = content
                        elif content_type == 'image' and isinstance(content, dict) and content.get('text'): text_content = content['text']
                        elif content_type == 'file_upload' and isinstance(content, dict): text_content = f"[用户上传了文件: {content.get('original_filename', '?')}]"
                        if role and text_content: chat_history_for_llm.append({"role": role, "content": text_content})
                
                print(f"[AI Request] History length: {len(chat_history_for_llm)}")
                print(f"[AI Request] Data Context: {data_context}")

                # 3. 调用流式响应函数 (传递 history)
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    response = None
                    print("[AI Response] Calling get_streaming_response...")
                    try:
                        response = get_streaming_response(
                            user_message=st.session_state.current_input,
                            data_context=data_context,
                            history=chat_history_for_llm,
                            message_placeholder=message_placeholder
                        )
                        # --- 新增：在 try 块内部用最终 response 更新占位符 --- 
                        if response:
                            message_placeholder.markdown(response) 
                        else: 
                            message_placeholder.empty()
                        print(f"[AI Response] get_streaming_response returned: {'Exists' if response else 'None'}")
                    except Exception as stream_e:
                        print(f"[AI Response] Error during get_streaming_response: {stream_e}")
                        st.error(f"获取AI响应时出错: {stream_e}")
                        response = None
                        message_placeholder.empty()
                
                # --- 新增：处理最终响应 (保存到 state 和 DB) --- 
                if response:
                    ai_message = {
                        "role": "assistant",
                        "content_type": "text",
                        "content": response,
                    }
                    if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
                        st.session_state.messages = []
                    st.session_state.messages.append(ai_message)
                    print("[AI Response] Appended final response to session_state.messages.")

                    # 保存到数据库
                    if current_session_id:
                        # 获取 user_id (再次确保存在)
                        user_id_for_save = st.session_state.user_info.get('username')
                        if user_id_for_save:
                            add_success = add_message_to_session(
                                session_id=current_session_id,
                                username=user_id_for_save,
                                role="assistant",
                                content_type="text",
                                content=response
                            )
                            if add_success:
                                print("[AI Response] Final response saved to DB successfully.")
                            else:
                                print("[AI Response] Failed to save final response to DB.")
                        else:
                             print("[AI Response] Error: Cannot save message, username not found.")
                    else:
                        print("错误：无法保存AI消息，缺少 current_session_id")
                else:
                    print("[AI Response] No valid response received, skipping state update and DB save.")

                # 重置标记 & Rerun (保持不变)
                st.session_state.need_ai_response = False
                st.session_state.current_input = ""
                st.session_state.is_thinking = False
                st.rerun()

        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("请输入您的问题", key="temp_input")
            submit_button = st.form_submit_button("发送")
            if submit_button and user_input:
                # 1. 立即显示用户消息
                with chat_container: # 确保在聊天容器内显示
                     with st.chat_message("user"):
                         st.write(user_input)

                # 2. 立即将用户消息添加到 session_state
                user_message_struct = {
                    "role": "user",
                    "content_type": "text",
                    "content": user_input,
                    "_id": f"user_{uuid.uuid4().hex}" # 临时ID用于显示
                }
                # 确保 messages 列表存在
                if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
                    st.session_state.messages = []
                st.session_state.messages.append(user_message_struct)

                # 3. 立即将用户消息存入数据库
                user_id_for_save = st.session_state.user_info.get('username')
                if current_session_id and user_id_for_save:
                    add_success = add_message_to_session(
                        session_id=current_session_id,
                        username=user_id_for_save,
                        role="user",
                        content_type="text",
                        content=user_input
                    )
                    if not add_success:
                        st.toast("警告：未能保存您的消息到数据库。", icon="⚠️")
                    else:
                        print("[User Input] User message saved to DB successfully.")
                else:
                    st.toast("错误：无法保存您的消息，缺少会话或用户信息。", icon="🚨")

                # 4. 设置状态以触发 AI 响应
                st.session_state.need_ai_response = True
                st.session_state.current_input = user_input # 仍然需要这个给 get_streaming_response
                st.session_state.is_thinking = True

                # 5. Rerun 以处理 AI 响应
                st.rerun()

    with right_col:
        with st.expander("可视化代码", expanded=True):
            viz_code = st.session_state.get('visualization_code')
            if viz_code:
                # 使用时间戳作为唯一key，确保每次rerun时都重新渲染
                st.code(viz_code, language="python")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("复制代码"):
                        st.toast("请手动复制上面的代码。")
                with col2:
                    if st.button("重新生成图表"):
                        st.session_state.should_regenerate = True
                        st.rerun()
            else:
                st.info("暂无可视化代码。")

# --- 页面底部清理代码 --- 
if st.session_state.get("mysql_connection"):
    close_mysql_connection(st.session_state.mysql_connection)
    st.session_state.mysql_connection = None 

