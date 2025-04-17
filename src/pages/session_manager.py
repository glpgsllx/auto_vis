import streamlit as st
from src.auth.auth import is_logged_in
from src.database.chat_history_db import get_sessions_by_user, create_new_session, delete_session
from datetime import datetime
import time

st.set_page_config(
    page_title="会话管理 | 数据分析助手",
    page_icon="📂",
    layout="wide"
)

# 检查用户是否登录
if not is_logged_in():
    st.warning("请先登录")
    st.switch_page("pages/login.py")
    st.stop() # 确保后续代码不执行

# 获取当前用户信息
user_info = st.session_state.user_info
user_id = user_info.get('username') # 假设 username 是 user_id

if not user_id:
    st.error("无法获取用户信息，请重新登录。")
    st.switch_page("pages/login.py")
    st.stop()

st.title("会话管理")
st.markdown("---")

# --- 开始新会话 ---
st.header("开始新的分析")
if st.button("➕ 创建新会话", type="primary", use_container_width=True):
    # 调用数据库函数创建新会话
    default_session_name = f"新会话 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    new_session_id = create_new_session(user_id=user_id, session_name=default_session_name)

    if new_session_id:
        # 将新会话ID存入session_state
        st.session_state.current_session_id = new_session_id
        st.session_state.current_session_name = default_session_name # 也存储一下名字，方便 data_analysis 页面显示
        # 清理可能存在的旧会话状态（可选，但推荐）
        keys_to_reset = ['messages', 'df', 'file_uploaded', 'column_descriptions',
                         'descriptions_provided', 'visualization_code', 'chart_status',
                         'file_path', 'current_image', 'file_type', 'mysql_step']
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        # 跳转到数据分析页面
        st.success(f"已创建新会话: {default_session_name}")
        time.sleep(1) # 短暂显示成功消息
        st.switch_page("pages/data_analysis.py")
    else:
        st.error("创建新会话失败，请稍后再试。")

st.markdown("---")
st.header("历史会话")

# --- 显示历史会话列表 ---
sessions = get_sessions_by_user(user_id=user_id)

if not sessions:
    st.info("您还没有历史会话记录。")
else:
    cols_per_row = 3
    cols = st.columns(cols_per_row)
    for i, session in enumerate(sessions):
        col_index = i % cols_per_row
        with cols[col_index]:
            with st.container(border=True):
                session_name = session.get('session_name', '未命名会话') # Provide default
                st.subheader(f"📜 {session_name}")
                last_updated_at = session.get('last_updated_at')
                if last_updated_at:
                    last_updated_str = last_updated_at.strftime('%Y-%m-%d %H:%M')
                else:
                    last_updated_str = "未知时间"
                st.caption(f"最后更新: {last_updated_str}")

                button_col1, button_col2 = st.columns(2)

                with button_col1:
                    enter_button_key = f"session_{session['_id']}"
                    if st.button("进入", key=enter_button_key, use_container_width=True):
                        # 设置当前会话ID
                        st.session_state.current_session_id = session['_id']
                        st.session_state.current_session_name = session['session_name']
                        # 清理可能存在的旧会话状态
                        keys_to_reset = ['messages', 'df', 'file_uploaded', 'column_descriptions',
                                         'descriptions_provided', 'visualization_code', 'chart_status',
                                         'file_path', 'current_image', 'file_type', 'mysql_step', 'loaded_context']
                        for key in keys_to_reset:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.switch_page("pages/data_analysis.py")

                with button_col2:
                    delete_button_key = f"delete_popover_{session['_id']}"
                    delete_confirm_key = f"delete_confirm_{session['_id']}"
                    delete_button_placeholder = st.empty()
                    
                    with st.popover(label="删除确认"):
                        session_name_for_confirm = session.get('session_name', '此未命名')
                        st.markdown(f"确定要删除会话 **'{session_name_for_confirm}'** 吗？此操作无法撤销。")
                        if st.button("确认删除", key=delete_confirm_key, type="primary"):
                            with st.spinner("正在删除..."):
                                delete_success = delete_session(session['_id'])
                                if delete_success:
                                    st.toast(f"会话 '{session['session_name']}' 已删除。")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.toast(f"删除会话 '{session['session_name']}' 失败。", icon="🚨")
                                
                    with delete_button_placeholder:
                        st.button("删除", key=delete_button_key, type="secondary", use_container_width=True) 