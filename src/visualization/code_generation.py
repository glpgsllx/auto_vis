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
    """从DataFrame生成可视化代码，使用传入的持久文件路径"""
    if not persistent_file_path:
         return None, "错误：需要提供 persistent_file_path 来生成代码。"
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
                columns_info += f"- {col} ({col_type}): {desc}\n"

        # --- 修改： 使用占位符 (需要知道文件类型) --- 
        file_read_code = "# 无法确定文件类型，请手动添加读取代码" # Default if path is None
        placeholder = None
        file_type_for_prompt = "未知文件"
        if persistent_file_path:
            file_extension = os.path.splitext(persistent_file_path)[1].lower()
            if file_extension == '.csv':
                 placeholder = 'data.csv'
                 file_read_code = f"df = pd.read_csv('{placeholder}')"
                 file_type_for_prompt = "CSV"
            elif file_extension in ['.xlsx', '.xls']:
                 placeholder = 'data.xlsx'
                 file_read_code = f"df = pd.read_excel('{placeholder}')"
                 file_type_for_prompt = "Excel"

        data_info = """
数据类型: {file_type}
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
            file_type=file_type_for_prompt,
            columns_info=columns_info,
            sample_data=df.head().to_string(),
            file_read_code=file_read_code
        )
        
        code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
        return code_response, None
    except Exception as e:
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
        success, image_path = execute_code(
            code,
            user_id=user_id, 
            session_id=session_id,
            data_source_type=data_source_type, # Pass the type
            persistent_file_path=persistent_file_path # Pass the path (can be None for mysql)
        )
        
        if success:
            return code, image_path, "图表生成成功"
        else:
             return code, None, "图表生成失败 (代码执行出错)"

    except Exception as e:
        import traceback
        print(f"创建图表时发生严重错误: {e}\n{traceback.format_exc()}")
        return None, None, f"创建图表时出错：{str(e)}" 