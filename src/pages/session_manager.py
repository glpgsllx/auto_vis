import streamlit as st
from src.auth.auth import is_logged_in
from src.database.chat_history_db import get_sessions_by_user, create_new_session, delete_session
from datetime import datetime
import time

st.set_page_config(
    page_title="Session Manager | Data Analysis Assistant",
    page_icon="📂",
    layout="wide"
)

# 检查用户是否登录
if not is_logged_in():
    st.warning("Please log in first")
    st.switch_page("pages/login.py")
    st.stop() # 确保后续代码不执行

# 获取当前用户信息
user_info = st.session_state.user_info
user_id = user_info.get('username') # 假设 username 是 user_id

if not user_id:
    st.error("Failed to get user info, please re-login.")
    st.switch_page("pages/login.py")
    st.stop()

st.title("Session Management")
st.markdown("---")

# --- Start a new session ---
st.header("Start a New Analysis")
if st.button("➕ Create Session", type="primary", use_container_width=True):
    # 调用数据库函数创建新会话
    default_session_name = f"New Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    new_session_id = create_new_session(user_id=user_id, session_name=default_session_name)

    if new_session_id:
        # 将新会话ID存入session_state
        st.session_state.current_session_id = new_session_id
        st.session_state.current_session_name = default_session_name # also store name for data_analysis page
        # 清理可能存在的旧会话状态（可选，但推荐）
        keys_to_reset = ['messages', 'df', 'file_uploaded', 'column_descriptions',
                         'descriptions_provided', 'visualization_code', 'chart_status',
                         'file_path', 'current_image', 'file_type', 'mysql_step']
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        # Go to data analysis page
        st.success(f"Session created: {default_session_name}")
        time.sleep(1) # 短暂显示成功消息
        st.switch_page("pages/data_analysis.py")
    else:
        st.error("Failed to create session. Please try again later.")

st.markdown("---")
st.header("History")

# --- 显示历史会话列表 ---
sessions = get_sessions_by_user(user_id=user_id)

if not sessions:
    st.info("No history yet.")
else:
    for i, session in enumerate(sessions):
        with st.container(border=True):
            session_name = session.get('session_name', 'Untitled') # Provide default
            
            col_info, col_buttons = st.columns([0.7, 0.3])
            
            with col_info:
                st.subheader(f"📜 {session_name}")
                last_updated_at = session.get('last_updated_at')
                if last_updated_at:
                    last_updated_str = last_updated_at.strftime('%Y-%m-%d %H:%M')
                else:
                    last_updated_str = "Unknown"
                st.caption(f"Last updated: {last_updated_str}")

            with col_buttons:
                button_col1, button_col2 = st.columns(2)
                with button_col1:
                    enter_button_key = f"session_{session['_id']}"
                    if st.button("Enter", key=enter_button_key, use_container_width=True):
                        st.session_state.current_session_id = session['_id']
                        st.session_state.current_session_name = session['session_name']
                        keys_to_reset = ['messages', 'df', 'file_uploaded', 'column_descriptions',
                                         'descriptions_provided', 'visualization_code', 'chart_status',
                                         'file_path', 'current_image', 'file_type', 'mysql_step', 'loaded_context']
                        for key in keys_to_reset:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.switch_page("pages/data_analysis.py")

                with button_col2:
                    delete_confirm_key = f"delete_confirm_{session['_id']}"
                    
                    with st.popover(label="Delete", help="Delete this session"):
                        session_name_for_confirm = session.get('session_name', 'this untitled')
                        st.markdown(f"Are you sure to delete session **'{session_name_for_confirm}'**? This action cannot be undone.")
                        if st.button("Confirm Delete", key=delete_confirm_key, type="primary"):
                            with st.spinner("Deleting..."):
                                delete_success = delete_session(session['_id'])
                                if delete_success:
                                    st.toast(f"Session '{session['session_name']}' deleted.")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.toast(f"Failed to delete session '{session['session_name']}'.", icon="🚨")

            st.markdown("<br>", unsafe_allow_html=True) 