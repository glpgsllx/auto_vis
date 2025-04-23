import os
import pandas as pd
from autogen import ConversableAgent
import uuid
from src.visualization.code_execution import execute_code
import streamlit as st
import pymysql

# 配置大语言模型
config_list = [
    {
        "model": "Qwen/Qwen2.5-72B-Instruct", 
        "api_key": os.environ.get("MODELSCOPE_API_KEY"), 
        "base_url": "https://api-inference.modelscope.cn/v1/"
    }
]

def generate_code(file_path, column_descriptions):
    """生成可视化代码的函数 (处理直接文件路径输入)"""
    file_extension = os.path.splitext(file_path)[1].lower()
    try:
        if file_extension == '.csv':
            df_sample = pd.read_csv(file_path, nrows=5)
        elif file_extension in ['.xlsx', '.xls']:
            df_sample = pd.read_excel(file_path, nrows=5)
        else:
            return None, f"不支持的文件类型: {file_extension}"
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
            return None, f"无法读取数据文件样本：{str(e_full)}"

    code_generator = ConversableAgent(
        "code_generator",
        system_message="你是一个专业的数据可视化专家。请根据提供的数据描述和样本，对数据进行分析，并思考一种良好的可视化图表分析方法，生成合适的Python代码来创建数据可视化。必须使用matplotlib库，不要使用seaborn或其他可视化库。代码需要将生成的图表保存为'answer.svg'。",
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
数据类型: 文件 ({file_type})
列描述:
{columns_info}
数据示例:
{sample_data}

请生成合适的Python代码来可视化这些数据。代码必须：
1. 导入必要的库（pandas, matplotlib）
2. 读取数据文件（使用下面提供的代码读取文件）
3. 创建合适的可视化（必须使用matplotlib，不要使用seaborn）
4. 将图表保存为'answer.svg'

读取文件的代码应该是:
{file_read_code}

请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
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
            system_message="你是一个专业的数据可视化专家。请根据提供的数据描述和样本，对数据进行分析，并思考一种良好的可视化图表分析方法，生成合适的Python代码来创建数据可视化。必须使用matplotlib库，不要使用seaborn或其他可视化库。代码需要将生成的图表保存为'answer.svg'。",
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
            file_type_for_prompt = f"MySQL 表 ({table_name})"

            # --- 构建 MySQL 的 Prompt (修正 f-string 和内部代码) ---
            sample_data_string = df.head().to_string()
            # 确保 table_name 和 database_name 对 SQL 和 Python 字符串安全
            safe_table_name = table_name.replace('`', '``') # 转义 SQL 中的反引号
            safe_database_name = database_name.replace('"', '\"') # 转义 Python 字符串中的双引号
            
            data_info = f"""
数据来源: {file_type_for_prompt}

数据列描述:
{columns_info}

数据示例 (来自数据库的前几行):
{sample_data_string}

请生成合适的Python代码来可视化这些数据。代码必须：
1.  导入必要的库（pandas, matplotlib, mysql.connector 或 pymysql）
2.  使用 **占位符凭据** 连接到 MySQL 数据库。(Host: 'localhost', User: 'root', Password: 'password', Database: '{safe_database_name}')
3.  执行 SQL 查询从 `{safe_table_name}` 表获取数据 (例如 SELECT * FROM `{safe_table_name}` LIMIT 1000)。将结果读入名为 'df' 的 Pandas DataFrame。
4.  使用 matplotlib 基于 'df' 创建合适的可视化。
5.  将图表保存为 'answer.svg'。
6.  关闭数据库连接。

SQL 查询和绘图的 Python 代码示例结构：
```python
import mysql.connector # 或者 import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib # 引入 matplotlib

# 设置 Agg 后端 (如果需要避免 GUI 问题)
matplotlib.use('Agg')

# 添加中文字体支持 (如果需要)
plt.rcParams['font.sans-serif'] = ['SimHei'] # 例如 SimHei
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['svg.fonttype'] = 'none'

# 1. 连接数据库 (使用占位符)
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="{safe_database_name}", # 使用转义后的数据库名
        # charset='utf8mb4' # 根据需要添加
    )

    # 2. 执行 SQL 查询
    # 使用 f-string 构建 SQL 查询，并用反引号包裹表名
    query = f"SELECT * FROM `{safe_table_name}` LIMIT 1000"
    print(f"Executing query: {{query}}") # 打印查询语句
    df = pd.read_sql(query, conn)
    print(f"Data loaded into DataFrame, shape: {{df.shape}}") # 打印数据形状

    # 3. 创建可视化 (示例：绘制前两列)
    if not df.empty and len(df.columns) >= 2:
        plt.figure(figsize=(10, 6))
        # --- 这里替换成基于数据分析的实际绘图逻辑 ---
        col1 = df.columns[0]
        col2 = df.columns[1]
        plt.plot(df[col1], df[col2]) 
        plt.title('数据可视化标题') # 使用简单标题
        plt.xlabel(str(col1)) # 转换为字符串以防万一
        plt.ylabel(str(col2))
        # --- 绘图逻辑结束 ---
        plt.tight_layout() # 调整布局

        # 4. 保存图片
        save_path = 'answer.svg'
        plt.savefig(save_path)
        print(f"Chart saved to {{save_path}}")
        plt.close() # 关闭图形，释放内存
    else:
        print("DataFrame 为空或列数不足，无法生成图表。")

except Exception as e:
    # 使用 repr(e) 获取更详细的错误表示
    print(f"An error occurred: {{repr(e)}}") 

finally:
    # 5. 关闭连接
    # 检查 conn 是否定义并且是连接对象并且已连接
    if 'conn' in locals() and hasattr(conn, 'is_connected') and conn.is_connected():
        conn.close()
        print("Database connection closed.")

```

请仅生成完整的 Python 代码块！不要包含 markdown 的 ```python ``` 标记。
"""

        else: # File Case (CSV/Excel)
            # --- 文件类型的 Prompt (保持不变) ---
            file_read_code = "# 无法确定文件类型，请手动添加读取代码" # Default
            placeholder = None
            file_type_for_prompt = "未知文件"
            file_extension = os.path.splitext(persistent_file_path)[1].lower()
            if file_extension == '.csv':
                 placeholder = 'data.csv'
                 file_read_code = f"df = pd.read_csv('{placeholder}')"
                 file_type_for_prompt = "CSV 文件"
            elif file_extension in ['.xlsx', '.xls']:
                 placeholder = 'data.xlsx'
                 file_read_code = f"df = pd.read_excel('{placeholder}')"
                 file_type_for_prompt = "Excel 文件"
            
            # 使用 f-string 并确保 df.head() 结果正确转义
            sample_data_string_file = df.head().to_string()
            data_info = f"""
数据来源: {file_type_for_prompt}
列描述:
{columns_info}
数据示例 (DataFrame 的前几行):
{sample_data_string_file}

请生成合适的Python代码来可视化这些数据。代码必须：
1. 导入必要的库（pandas, matplotlib）
2. 读取数据文件（使用下面提供的代码读取文件）
3. 创建合适的可视化（必须使用matplotlib，不要使用seaborn）
4. 将图表保存为'answer.svg'

读取文件的代码应该是:
{file_read_code}

请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
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
        print(f"生成可视化代码时出错: {e}\\n{traceback.format_exc()}") # 打印堆栈跟踪
        return None, f"生成可视化代码时出错：{str(e)}" 

def create_chart(user_id: str, session_id: str, column_descriptions, data_source_type: str, df=None, persistent_file_path=None):
    """创建图表的函数

    Args:
        # ... (user_id, session_id, column_descriptions, df, persistent_file_path)
        data_source_type (str): 数据源类型 ('csv', 'excel', 'mysql')
        
    Returns:
        tuple: (生成的代码, 图片相对路径, 结果信息)
    """
    if not user_id or not session_id:
         return None, None, "创建图表需要 user_id 和 session_id"
    
    # --- 修改：移除对 df 和 persistent_file_path 同时存在的严格要求（因为 mysql 类型只有 df）---
    # if df is not None and not persistent_file_path:
    #      return None, None, "从 DataFrame 创建图表时需要提供 persistent_file_path"
    
    # --- 新增：对 MySQL 类型的处理 --- 
    is_mysql = (data_source_type == 'mysql')
    if not is_mysql and not persistent_file_path:
         return None, None, "文件类型数据源需要 persistent_file_path"
    if df is None and not persistent_file_path: # Should not happen with current flow
         return None, None, "需要提供 DataFrame 或文件路径"

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
            return None, None, "无法确定生成代码的方式。"

        if error: return None, None, error
        if not code: return None, None, "未能生成可视化代码"

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
            return code, image_path, "图表生成成功"
        else:
             return code, None, f"图表生成失败 (代码执行出错): {output_text}"

    except Exception as e:
        import traceback
        print(f"创建图表时发生严重错误: {e}\n{traceback.format_exc()}")
        return None, None, f"创建图表时出错：{str(e)}" 