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
    """生成可视化代码的函数
    
    Args:
        file_path (str): 数据文件的路径，支持CSV或Excel
        column_descriptions (dict): 数据列的描述信息，格式为 {列名: 描述}
        
    Returns:
        tuple: (生成的代码, 错误信息)
            - 如果成功生成代码，返回 (代码字符串, None)
            - 如果失败，返回 (None, 错误信息字符串)
    """
    # 根据文件扩展名确定文件类型
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # 根据文件类型选择不同的读取方法
        if file_extension == '.csv':
            df_sample = pd.read_csv(file_path, nrows=5)
        elif file_extension in ['.xlsx', '.xls']:
            df_sample = pd.read_excel(file_path, nrows=5)
        else:
            return None, f"不支持的文件类型: {file_extension}"
    except Exception as e:
        return None, f"无法读取数据文件：{str(e)}"
    
    # 创建代码生成agent
    code_generator = ConversableAgent(
        "code_generator",
        system_message="你是一个专业的数据可视化专家。请根据提供的数据描述和样本，对数据进行分析，并思考一种良好的可视化图表分析方法，生成合适的Python代码来创建数据可视化。使用matplotlib库。代码需要将生成的图表保存为'answer.png'。",
        llm_config={"config_list": config_list},
        human_input_mode="NEVER"
    )
    
    # 准备数据信息
    columns_info = ""
    for col, desc in column_descriptions.items():
        col_type = df_sample[col].dtype
        columns_info += f"- {col} ({col_type}): {desc}\n"
    
    # 根据文件类型生成不同的代码模板
    if file_extension == '.csv':
        file_read_code = f"df = pd.read_csv('../{file_path}')"
    else:  # Excel文件
        file_read_code = f"df = pd.read_excel('../{file_path}')"
    
    data_info = """
    数据文件路径: ../{}
    文件类型: {}

    数据列描述:
    {}

    数据示例:
    {}

    请生成合适的Python代码来可视化这些数据。代码必须：
    1. 导入必要的库（pandas, matplotlib）
    2. 读取数据文件（使用正确的函数读取{}文件）
    3. 创建合适的可视化
    4. 将图表保存为'answer.png'

    读取文件的代码应该是:
    {}

    请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
    """.format(
        file_path, 
        "CSV" if file_extension == '.csv' else "Excel", 
        columns_info, 
        df_sample.to_string(),
        "CSV" if file_extension == '.csv' else "Excel",
        file_read_code
    )
    
    # 生成代码
    code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
    
    return code_response, None

def generate_code_from_df(df, column_descriptions):
    """从DataFrame生成可视化代码
    
    Args:
        df (pandas.DataFrame): 数据框
        column_descriptions (dict): 数据列的描述信息，格式为 {列名: 描述}
        
    Returns:
        tuple: (生成的代码, 错误信息)
            - 如果成功生成代码，返回 (代码字符串, None)
            - 如果失败，返回 (None, 错误信息字符串)
    """
    try:
        # 创建代码生成agent
        code_generator = ConversableAgent(
            "code_generator",
            system_message="你是一个专业的数据可视化专家。请根据提供的数据描述和样本，对数据进行分析，并思考一种良好的可视化图表分析方法，生成合适的Python代码来创建数据可视化。使用matplotlib库。代码需要将生成的图表保存为'answer.png'。",
            llm_config={"config_list": config_list},
            human_input_mode="NEVER"
        )
        
        # 准备数据信息
        columns_info = ""
        for col, desc in column_descriptions.items():
            if col in df.columns:
                col_type = df[col].dtype
                columns_info += f"- {col} ({col_type}): {desc}\n"
        
        # 检查是不是MySQL数据源
        is_mysql_source = False
        table_name = None
        if "mysql_selected_table" in st.session_state and st.session_state.mysql_selected_table:
            is_mysql_source = True
            table_name = st.session_state.mysql_selected_table
        
        # 根据数据源类型选择不同的数据获取方式
        if is_mysql_source:
            # 保存样本数据到数据上下文
            data_sample = df.head().to_string()
            
            data_info = """
            数据来源: MySQL数据库表 '{}'
            
            数据列描述:
            {}

            数据示例:
            {}

            请生成合适的Python代码来可视化这些数据。代码必须：
            1. 导入必要的库（pandas, matplotlib, pymysql）
            2. 连接MySQL数据库获取数据
            3. 创建合适的可视化
            4. 将图表保存为'answer.png'

            数据库连接和查询的代码应该是:
            ```python
            import pymysql
            import pandas as pd
            import matplotlib.pyplot as plt

            # 连接MySQL数据库
            connection = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='password',
                database='database_name'
            )

            # 查询数据
            query = "SELECT * FROM `table_name`"  # 替换为实际表名
            df = pd.read_sql(query, connection)
            
            # 关闭连接
            connection.close()
            ```

            请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
            """.format(
                table_name,
                columns_info, 
                data_sample
            )
        else:
            # 保存DataFrame到临时文件
            temp_id = uuid.uuid4().hex
            temp_file = f"codeexe/temp_data_{temp_id}.csv"
            
            # 确保目录存在
            if not os.path.exists('codeexe'):
                os.makedirs('codeexe')
                
            df.to_csv(temp_file, index=False)
            
            data_info = """
            数据列描述:
            {}

            数据示例:
            {}

            请生成合适的Python代码来可视化这些数据。代码必须：
            1. 导入必要的库（pandas, matplotlib）
            2. 读取数据文件（使用pd.read_csv读取文件）
            3. 创建合适的可视化
            4. 将图表保存为'answer.png'

            读取文件的代码应该是:
            df = pd.read_csv('{}')

            请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
            """.format(
                columns_info, 
                df.head().to_string(),
                temp_file
            )
        
        # 生成代码
        code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
        
        return code_response, None
    except Exception as e:
        return None, f"生成可视化代码时出错：{str(e)}"

def create_chart(file_path=None, column_descriptions=None, df=None):
    """创建图表的函数
    
    Args:
        file_path (str, optional): 数据文件的路径
        column_descriptions (dict, optional): 数据列的描述信息，格式为 {列名: 描述}
        df (pandas.DataFrame, optional): 数据框，如果提供则使用数据框而不是文件
        
    Returns:
        tuple: (生成的代码, 图片路径, 结果信息)
            - 如果成功生成图表，返回 (代码字符串, 图片路径, "图表生成成功")
            - 如果失败，返回 (None, None, 错误信息字符串)
    """
    try:
        # 根据输入选择不同的代码生成方式
        if df is not None:
            code, error = generate_code_from_df(df, column_descriptions)
        elif file_path:
            code, error = generate_code(file_path, column_descriptions)
        else:
            return None, None, "需要提供数据文件路径或数据框"
        
        if error:
            return None, None, error
        
        # 执行代码生成图表
        success, image_path = execute_code(code)
        
        if success:
            return code, image_path, "图表生成成功"
        else:
            return None, None, "图表生成失败"
            
    except Exception as e:
        return None, None, f"创建图表时出错：{str(e)}" 