import os
import time
import uuid
import streamlit as st
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor, CodeBlock
import re # Import re for more robust replacement if needed
import traceback # Make sure traceback is imported for the except block

# 创建一个本地命令行代码执行器，工作目录设定为 codeexe
# 注意：所有在代码中使用的相对路径都是相对于这个 work_dir
executor = LocalCommandLineCodeExecutor(
    timeout=20,  # 增加超时时间
    work_dir="codeexe",
)

def execute_code(code, user_id: str, session_id: str, data_source_type: str, persistent_file_path: str | None = None, image_id=None):
    """执行代码并生成图片的通用函数

    Args:
        code (str): 要执行的Python代码字符串 (可能包含占位符如 'data.csv')
        user_id (str): 当前用户的ID
        session_id (str): 当前会话的ID
        data_source_type (str): 数据源类型 ('csv', 'excel', 'mysql')
        persistent_file_path (str | None): 数据文件相对于 src 的持久化路径 (仅文件类型需要)
        image_id (str, optional): 图片的唯一ID

    Returns:
        tuple: (是否成功, 图片相对路径 | None)
    """
    print(f"[Execute Code] Data source type: {data_source_type}")
    if not user_id or not session_id:
        print("错误: execute_code 需要 user_id 和 session_id。")
        return False, None
    # --- 新增：检查文件类型参数 --- 
    if data_source_type in ['csv', 'excel'] and not persistent_file_path:
         print(f"错误: 文件类型({data_source_type}) 需要 persistent_file_path。")
         return False, None

    try: # --- Main Try Block Starts Here ---
        # --- 1. 构建目标图表路径 (不变) ---
        image_id = image_id or str(uuid.uuid4().hex)
        chart_filename = f"chart_{image_id}.svg"
        target_dir_relative_to_src = os.path.join("session_assets", str(user_id), str(session_id))
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        target_dir_full = os.path.join(project_root, "src", target_dir_relative_to_src)
        target_file_full_path = os.path.join(target_dir_full, chart_filename)
        relative_chart_save_path_for_code = os.path.normpath(os.path.join("..", target_dir_relative_to_src, chart_filename)).replace(os.sep, '/')

        # --- 2. 创建目标目录 (不变) ---
        os.makedirs(target_dir_full, exist_ok=True)

        # --- 3. 初始代码修改：替换图表保存路径 (不变) ---
        modified_code = code.replace("'answer.png'", f"'{relative_chart_save_path_for_code}'")
        modified_code = modified_code.replace("'answer.svg'", f"'{relative_chart_save_path_for_code}'")

        # --- 4. 添加中文字体支持 (不变) ---
        font_support_code = """
# 添加中文字体支持
import matplotlib.pyplot as plt
import matplotlib

# 设置matplotlib后端为Agg，避免字体问题
matplotlib.use('Agg')

# 直接设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['svg.fonttype'] = 'none'  # 确保字体被正确嵌入到SVG中
"""
        import_pos = modified_code.find("import")
        if import_pos != -1:
            newline_pos = modified_code.find("\n", import_pos)
            if newline_pos != -1:
                modified_code = modified_code[:newline_pos+1] + font_support_code + modified_code[newline_pos+1:]
            else:
                modified_code = font_support_code + modified_code
        else:
             modified_code = font_support_code + modified_code

        # --- 5. 处理数据加载路径/信息 --- 
        if data_source_type in ['csv', 'excel']:
            # --- 计算文件执行路径 (不变) ---
            relative_data_exec_path = os.path.normpath(os.path.join("..", persistent_file_path)).replace(os.sep, '/')
            print(f"[Execute Code] Calculated data execution path: {relative_data_exec_path}")

            # --- 根据文件类型替换不同的占位文件名 ---
            if data_source_type == 'csv':
                modified_code = modified_code.replace("'data.csv'", f"'{relative_data_exec_path}'")
            elif data_source_type == 'excel':
                modified_code = re.sub(r"""(['"])data\.xls[x|m|b]?\1""", rf"\1{relative_data_exec_path}\1", modified_code)



        elif data_source_type == 'mysql':
            # --- 修复：确保有 pass 或实际逻辑 --- 
            if "mysql_connection_info" in st.session_state:
                 conn_info = st.session_state.mysql_connection_info
                 # ... (MySQL connection info replacement logic - should be here and complete) ...
                 modified_code = modified_code.replace('host="localhost"', f'host="{conn_info["host"]}"') # Example
                 # ... add all other replacements for port, user, pass, db, charset ...
                 print(f"MySQL连接信息已替换 (来自 session_state): {conn_info}")
            else:
                 print("警告：无法替换 MySQL 连接信息，st.session_state 中未找到 mysql_connection_info。")
            # --- Ensure MySQL connection string replacement (section 6 from previous state) is handled correctly --- 
            # This section might be redundant if the above handles it
            # if ("mysql.connector.connect" in modified_code or "pymysql.connect" in modified_code) ...:
                 # ... (replacement logic) ...
            
        # --- 6. 处理MySQL连接信息 (保持不变) ---
        if ("mysql.connector.connect" in modified_code or "pymysql.connect" in modified_code) and "mysql_connection_info" in st.session_state:
            conn_info = st.session_state.mysql_connection_info
            # (替换逻辑保持不变) ...
            modified_code = modified_code.replace(
                'host="localhost"', f'host="{conn_info["host"]}"'
            ).replace(
                "host='localhost'", f"host='{conn_info['host']}'"
            )
            if "port" in conn_info:
                 modified_code = modified_code.replace(
                     'port=3306', f'port={conn_info["port"]}'
                 ).replace(
                     "port=3306", f"port={conn_info['port']}"
                 )
            modified_code = modified_code.replace(
                'user="root"', f'user="{conn_info["user"]}"'
            ).replace(
                "user='root'", f"user='{conn_info['user']}'"
            )
            modified_code = modified_code.replace(
                 'password="password"', f'password="{conn_info["password"]}"'
            ).replace(
                 'password=""', f'password="{conn_info["password"]}"'
            ).replace(
                "password='password'", f"password='{conn_info['password']}'"
            ).replace(
                "password=''", f"password='{conn_info['password']}'"
            )
            modified_code = modified_code.replace(
                 'database="database_name"', f'database="{conn_info["database"]}"'
            ).replace(
                 "database='database_name'", f"database='{conn_info['database']}'"
             )
            # (处理 charset 的逻辑也保持不变) ...
            if "charset" in conn_info:
                 if "charset=" not in modified_code:
                     connect_pos = modified_code.find("mysql.connector.connect(")
                     if connect_pos == -1:
                         connect_pos = modified_code.find("pymysql.connect(")
                     if connect_pos != -1:
                         bracket_count = 1
                         for i in range(connect_pos + modified_code[connect_pos:].find("(") + 1, len(modified_code)):
                             if modified_code[i] == "(": bracket_count += 1
                             elif modified_code[i] == ")":
                                 bracket_count -= 1
                                 if bracket_count == 0:
                                     modified_code = modified_code[:i] + f", charset='{conn_info['charset']}'" + modified_code[i:]
                                     break
                 else:
                     modified_code = modified_code.replace(
                         'charset="utf8"', f'charset="{conn_info["charset"]}"'
                     ).replace(
                         "charset='utf8'", f"charset='{conn_info['charset']}'"
                     ).replace(
                          'charset="utf8mb4"', f'charset="{conn_info["charset"]}"'
                     ).replace(
                         "charset='utf8mb4'", f"charset='{conn_info['charset']}'"
                     )
            print(f"MySQL连接信息: {conn_info}")

        print("执行的代码 (路径替换后):")
        print("-" * 50)
        print(modified_code)
        print("-" * 50)

        # --- 7. 执行代码 (使用设定好工作目录的 executor) ---
        # --- 修改：使用 CodeBlock 对象 --- 
        # code_executor_agent = ConversableAgent(
        #     "code_executor_agent",
        #     llm_config=False,
        #     code_execution_config={"executor": executor},
        #     human_input_mode="NEVER",
        # )
        # code_block = f"```python\n{modified_code}\n```" # Old string format
        # execution_result = executor.execute_code_blocks([code_block]) # Old call
        
        # 创建 CodeBlock 对象
        code_block_obj = CodeBlock(code=modified_code, language="python")
        # 直接使用 executor 执行 CodeBlock 列表
        execution_result = executor.execute_code_blocks([code_block_obj])

        print(f"代码执行退出码: {execution_result.exit_code}")
        print(f"代码执行输出:\n{execution_result.output}")

        # --- 8. 检查图片生成并返回相对路径 ---
        if execution_result.exit_code == 0: # 检查退出码是否为0 (成功)
            # 检查目标文件是否真的被创建
            if os.path.exists(target_file_full_path):
                print(f"图表成功生成于: {target_file_full_path}")
                # 返回相对于 src 目录的路径
                return True, os.path.join(target_dir_relative_to_src, chart_filename).replace(os.sep, '/')
            else:
                print(f"代码执行成功，但目标文件未找到: {target_file_full_path}")
                print(f"请检查代码中的保存路径是否正确设置为: {relative_chart_save_path_for_code}")
                return False, None
        else:
            print(f"代码执行失败 (退出码: {execution_result.exit_code})。输出:\n{execution_result.output}")
            return False, None

    except Exception as e:
        print(f"执行代码时发生严重错误：{str(e)}\n{traceback.format_exc()}")
        return False, None

# --- 修改：regenerate_chart 也需要传递数据源信息 ---
def regenerate_chart(code, user_id: str, session_id: str, data_source_type: str, persistent_file_path: str | None = None):
    """重新生成图表

    Args:
        code (str): 可视化代码
        user_id (str): 当前用户的ID
        session_id (str): 当前会话的ID
        data_source_type (str): 数据源类型
        persistent_file_path (str | None): 持久化文件路径 (如果类型是文件)

    Returns:
        tuple: (是否成功, 图片相对路径 | None)
    """
    image_id = uuid.uuid4().hex
    return execute_code(code, user_id, session_id, data_source_type, persistent_file_path, image_id) 