import os
import pandas as pd
from autogen import ConversableAgent
import uuid
from src.visualization.code_execution import execute_code
import streamlit as st
import pymysql

# 配置大语言模型
# config_list = [
#     {
#         "model": "Qwen/Qwen2.5-72B-Instruct", 
#         "api_key": os.environ.get("MODELSCOPE_API_KEY"), 
#         "base_url": "https://api-inference.modelscope.cn/v1/"
#     }
# ]

config_list = [
    {
        "model": "qwen2.5-72b-instruct", 
        "api_key": "sk-NEuZniCRXEmJjiQ5CHNl8rtTDKcDogk04vUdjUgX7Zjpm9PU", 
        "base_url": "https://yunwu.ai/v1",
    }
]

# config_list = [
#     {
#         "model": "/model", 
#         "api_key": os.environ.get("MODELSCOPE_API_KEY"), 
#         "base_url": "http://101.42.22.132:8000/v1"
#     }
# ]

def generate_code(file_path, column_descriptions):
    """生成可视化代码的函数 (处理直接文件路径输入)"""
    file_extension = os.path.splitext(file_path)[1].lower()
    try:
        if file_extension == '.csv':
            df_sample = pd.read_csv(file_path, nrows=5)
        elif file_extension in ['.xlsx', '.xls']:
            df_sample = pd.read_excel(file_path, nrows=5)
        else:
            return None, f"Unsupported file type: {file_extension}"
    except Exception as e:
        # Need to construct full path to read sample if file_path is relative to src
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            full_path_for_sample = os.path.join(project_root, "src", file_path)
            print(f"[generate_code] Reading sample from: {full_path_for_sample}")
            if file_extension == '.csv':
                df_sample = pd.read_csv(full_path_for_sample, nrows=5)
            elif file_extension in ['.xlsx', '.xls']:
                df_sample = pd.read_excel(full_path_for_sample, nrows=5)
        except Exception as e_full:
            print(f"[generate_code] Error reading sample: {e_full}")
            return None, f"Failed to read data file sample: {str(e_full)}"

    code_generator = ConversableAgent(
        "code_generator",
        system_message="You are a professional data visualization expert. Based on the provided column descriptions and sample rows, generate Python code to produce a suitable visualization using matplotlib only (no seaborn/others). Save the chart to 'answer.svg'. Output only code.",
        llm_config={"config_list": config_list},
        human_input_mode="NEVER"
    )

    columns_info = ""
    for col, desc in column_descriptions.items():
        if col in df_sample.columns:
            col_type = df_sample[col].dtype
            columns_info += f"- {col} ({col_type}): {desc}\n"
        else:
             columns_info += f"- {col}: {desc} (Type info unavailable)\n"

    # --- 修改： 使用占位符 --- 
    placeholder = 'data.csv' if file_extension == '.csv' else 'data.xlsx'
    read_func = f"pd.read_{'csv' if file_extension == '.csv' else 'excel'}"
    file_read_code = f"df = {read_func}('{placeholder}')"

    data_info = """
Data type: File ({file_type})
Column descriptions:
{columns_info}
Sample rows:
{sample_data}

Generate Python code to visualize these data:
1. Import pandas and matplotlib
2. Load data using the code below
3. Use matplotlib only (no seaborn)
4. Save the chart as 'answer.svg'

Use this to read the file:
{file_read_code}

Only output code; do NOT include ```python fences or any extra text.
""".format(
        file_type="CSV" if file_extension == '.csv' else "Excel",
        columns_info=columns_info,
        sample_data=df_sample.to_string(),
        file_read_code=file_read_code
    )
    code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
    return code_response, None

def generate_code_from_df(df, column_descriptions, persistent_file_path: str | None):
    """从DataFrame生成可视化代码，根据数据源类型生成不同提示"""
    try:
        code_generator = ConversableAgent(
            "code_generator",
            system_message="You are a professional data visualization expert. Based on provided descriptions and samples, generate Python code to create a visualization using matplotlib only. Save to 'answer.svg'. Output code only.",
            llm_config={"config_list": config_list},
            human_input_mode="NEVER"
        )
        
        columns_info = ""
        for col, desc in column_descriptions.items():
            if col in df.columns:
                col_type = df[col].dtype
                columns_info += f"- {col} ({col_type}): {repr(desc)}\\n"

        # --- 根据 persistent_file_path 判断数据源类型并生成不同的提示 ---
        if persistent_file_path is None: # MySQL Case
            # --- 获取表名和数据库名 ---
            table_name = st.session_state.get('mysql_selected_table', 'your_table_name')
            conn_info_safe = st.session_state.get('mysql_connection_info', {})
            database_name = conn_info_safe.get('database', 'your_database_name')
            file_type_for_prompt = f"MySQL table ({table_name})"

            # --- 构建 MySQL 的 Prompt (修正 f-string 和内部代码) ---
            sample_data_string = df.head().to_string()
            # 确保 table_name 和 database_name 对 SQL 和 Python 字符串安全
            safe_table_name = table_name.replace('`', '``') # 转义 SQL 中的反引号
            safe_database_name = database_name.replace('"', '\"') # 转义 Python 字符串中的双引号
            
            data_info = f"""
Data source: {file_type_for_prompt}

Column descriptions:
{columns_info}

Sample rows (from database):
{sample_data_string}

Generate Python code to visualize these data. Requirements:
1. Import pandas, matplotlib, and mysql.connector (or pymysql)
2. Connect to MySQL using placeholder credentials (Host: 'localhost', User: 'root', Password: 'password', Database: '{safe_database_name}')
3. Execute SQL like SELECT * FROM `{safe_table_name}` LIMIT 1000 and load to a DataFrame named 'df'
4. Create a visualization using matplotlib
5. Save to 'answer.svg'
6. Close the DB connection

Example Python structure (for reference only):
```python
import mysql.connector  # or: import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Use headless backend and embed fonts properly for SVG
matplotlib.use('Agg')
plt.rcParams['svg.fonttype'] = 'none'

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="{safe_database_name}",
    )

    # Query data
    query = f"SELECT * FROM `{safe_table_name}` LIMIT 1000"
    df = pd.read_sql(query, conn)

    # Simple demo plot (replace with data-driven logic)
    if not df.empty and len(df.columns) >= 2:
        plt.figure(figsize=(10, 6))
        col1, col2 = df.columns[0], df.columns[1]
        plt.plot(df[col1], df[col2])
        plt.title("Chart Title")
        plt.xlabel(str(col1))
        plt.ylabel(str(col2))
        plt.tight_layout()
        plt.savefig('answer.svg')
        plt.close()
except Exception as e:
    print(f"An error occurred: {repr(e)}")
finally:
    if 'conn' in locals() and hasattr(conn, 'close'):
        try:
            conn.close()
        except Exception:
            pass
```

Only output a complete Python code block. Do NOT include ```python fences.
"""

        else: # File Case (CSV/Excel)
            # --- 文件类型的 Prompt (保持不变) ---
            file_read_code = "# Unable to determine file type; please add loading code manually" # Default
            placeholder = None
            file_type_for_prompt = "Unknown file"
            file_extension = os.path.splitext(persistent_file_path)[1].lower()
            if file_extension == '.csv':
                 placeholder = 'data.csv'
                 file_read_code = f"df = pd.read_csv('{placeholder}')"
                 file_type_for_prompt = "CSV file"
            elif file_extension in ['.xlsx', '.xls']:
                 placeholder = 'data.xlsx'
                 file_read_code = f"df = pd.read_excel('{placeholder}')"
                 file_type_for_prompt = "Excel file"
            
            # 使用 f-string 并确保 df.head() 结果正确转义
            sample_data_string_file = df.head().to_string()
            data_info = f"""
Data source: {file_type_for_prompt}
Column descriptions:
{columns_info}
Sample rows (head of DataFrame):
{sample_data_string_file}

Generate Python code to visualize the data:
1. Import pandas and matplotlib
2. Load the file using the code below
3. Create an appropriate visualization using matplotlib only (no seaborn)
4. Save the chart as 'answer.svg'

Use this to read the file:
{file_read_code}

Only output code; do NOT include any other text or ```python fences.
"""
        
        # --- 打印 Prompt 用于调试 (保持不变) ---
        print("[generate_code_from_df] Generated Prompt for LLM:")
        print("-" * 30)
        print(data_info)
        print("-" * 30)

        # --- 调用 LLM 生成代码 (保持不变) ---
        code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
        return code_response, None
    except Exception as e:
        import traceback # 确保导入 traceback
        print(f"Error generating visualization code: {e}\\n{traceback.format_exc()}")
        return None, f"Error generating visualization code: {str(e)}" 

def create_chart(user_id: str, session_id: str, column_descriptions, data_source_type: str, df=None, persistent_file_path=None):
    """创建图表的函数

    Args:
        # ... (user_id, session_id, column_descriptions, df, persistent_file_path)
        data_source_type (str): 数据源类型 ('csv', 'excel', 'mysql')
        
    Returns:
        tuple: (生成的代码, 图片相对路径, 结果信息)
    """
    if not user_id or not session_id:
         return None, None, "Creating a chart requires user_id and session_id"
    
    # --- 修改：移除对 df 和 persistent_file_path 同时存在的严格要求（因为 mysql 类型只有 df）---
    # if df is not None and not persistent_file_path:
    #      return None, None, "从 DataFrame 创建图表时需要提供 persistent_file_path"
    
    # --- 新增：对 MySQL 类型的处理 --- 
    is_mysql = (data_source_type == 'mysql')
    if not is_mysql and not persistent_file_path:
         return None, None, "File-based data source requires persistent_file_path"
    if df is None and not persistent_file_path: # Should not happen with current flow
         return None, None, "A DataFrame or file path is required"

    try:
        code = None
        error = None
        
        # --- 修改：调用 generate_code* 函数时，传递必要的参数 ---
        # generate_code_from_df/generate_code 现在也需要知道类型以使用正确的占位符
        # 它们内部不再保存临时文件，而是直接构建 prompt
        if df is not None: 
            # 对于文件类型，需要路径来告知LLM如何读取；对于MySQL，路径为空
            path_to_use_in_prompt = persistent_file_path if not is_mysql else None 
            print(f"[create_chart] Generating code from DF. Type: {data_source_type}, Path for prompt: {path_to_use_in_prompt}")
            # TODO: Refactor generate_code_from_df to accept type and path
            # Assuming generate_code_from_df is updated or implicitly handles this via context passed earlier
            code, error = generate_code_from_df(df, column_descriptions, persistent_file_path if not is_mysql else None) # Pass path only if file
        elif persistent_file_path: # Only file path case
            print(f"[create_chart] Generating code from file path: {persistent_file_path}")
            code, error = generate_code(persistent_file_path, column_descriptions)
        else:
            return None, None, "Cannot determine how to generate code."

        if error: return None, None, error
        if not code: return None, None, "Failed to generate visualization code"

        # --- 修改：调用 execute_code 时传递 data_source_type 和 persistent_file_path --- 
        print(f"[create_chart] Generated code, attempting execution with type: {data_source_type}, path: {persistent_file_path}")
        success, image_path, output_text = execute_code(
            code,
            user_id=user_id, 
            session_id=session_id,
            data_source_type=data_source_type, # Pass the type
            persistent_file_path=persistent_file_path # Pass the path (can be None for mysql)
        )
        
        if success:
            return code, image_path, "Chart generated successfully"
        else:
            return code, None, f"Chart generation failed (code execution error): {output_text}"

    except Exception as e:
        import traceback
        print(f"Critical error when creating chart: {e}\n{traceback.format_exc()}")
        return None, None, f"Error creating chart: {str(e)}"