import streamlit as st
import os

def display_sidebar_user_info(user_info):
    """在侧边栏显示用户信息
    
    Args:
        user_info (dict): 用户信息
    """
    if user_info:
        # 显示用户头像
        avatar_url = user_info.get('avatar_url', 'https://ui-avatars.com/api/?name=' + user_info.get('username', 'User') + '&background=random')
        
        # 检查头像路径是否存在
        if avatar_url.startswith('data/avatars/'):
            # 如果在src目录下运行，需要添加../ 
            avatar_path = avatar_url
            if not os.path.exists(avatar_path) and os.path.exists("../"+avatar_path):
                avatar_path = "../" + avatar_path
                
            if os.path.exists(avatar_path):
                st.image(avatar_path, width=100)
            else:
                # 如果头像文件不存在，使用默认头像
                default_avatar = 'https://ui-avatars.com/api/?name=' + user_info.get('username', 'User') + '&background=random'
                st.image(default_avatar, width=100)
        else:
            st.image(avatar_url, width=100)
        
        # 显示用户名
        st.write(f"**{user_info['username']}**")
        
        # 简单显示统计信息，无额外容器
        st.write(f"使用次数：{user_info['usage_count']}")
        st.write(f"账号等级：{user_info['level']}")
        
        st.markdown("---")
        
        # 退出登录按钮
        if st.button("退出登录", key="logout"):
            st.session_state.user_info = None
            st.switch_page("login.py")

def display_error(message):
    """显示错误消息
    
    Args:
        message (str): 错误消息
    """
    st.error(message)

def display_success(message):
    """显示成功消息
    
    Args:
        message (str): 成功消息
    """
    st.success(message)

def display_info(message):
    """显示信息消息
    
    Args:
        message (str): 消息内容
    """
    st.info(message)

def display_warning(message):
    """显示警告消息
    
    Args:
        message (str): 警告消息
    """
    st.warning(message)

def display_code(code, language="python"):
    """显示代码块
    
    Args:
        code (str): 代码内容
        language (str, optional): 代码语言，默认为python
    """
    st.code(code, language=language)

def display_dataframe_info(df):
    """显示数据框信息
    
    Args:
        df (pandas.DataFrame): 数据框
    """
    st.write(f"数据形状: {df.shape[0]} 行 x {df.shape[1]} 列")
    
    # 显示列信息
    col_info = ""
    for col in df.columns:
        col_info += f"- **{col}** ({df[col].dtype})\n"
    
    st.markdown("### 列信息")
    st.markdown(col_info)
    
    # 显示数据预览
    st.markdown("### 数据预览")
    st.dataframe(df.head(5))

def create_file_uploader(label, file_types, key=None):
    """创建文件上传组件
    
    Args:
        label (str): 上传组件标签
        file_types (list): 允许的文件类型列表
        key (str, optional): 组件唯一标识
        
    Returns:
        uploaded_file: 上传的文件对象
    """
    return st.file_uploader(label, type=file_types, key=key)

def create_text_input(label, value="", key=None, type="default"):
    """创建文本输入框
    
    Args:
        label (str): 输入框标签
        value (str, optional): 默认值
        key (str, optional): 组件唯一标识
        type (str, optional): 输入类型，可以是"default", "password"等
        
    Returns:
        str: 输入的文本
    """
    return st.text_input(label, value=value, key=key, type=type)

def create_button(label, key=None):
    """创建按钮
    
    Args:
        label (str): 按钮标签
        key (str, optional): 组件唯一标识
        
    Returns:
        bool: 按钮是否被点击
    """
    return st.button(label, key=key) 