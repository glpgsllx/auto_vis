import os
import pandas as pd
import streamlit as st
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
import time
import uuid

# 创建一个本地命令行代码执行器
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # 每个代码执行的超时时间（秒）
    work_dir="codeexe",  # 使用临时目录来存储代码文件
)

config_list = [
    {"model": "Qwen/Qwen2.5-72B-Instruct", "api_key": os.environ.get("MODELSCOPE_API_KEY"), "base_url": "https://api-inference.modelscope.cn/v1/"}
]

def execute_code(code, image_id=None):
    """执行代码并生成图片的通用函数
    
    Args:
        code (str): 要执行的Python代码字符串
        image_id (str, optional): 图片的唯一ID，如果不提供则自动生成
        
    Returns:
        tuple: (是否成功, 图片路径)
            - 如果成功生成图片，返回 (True, 图片路径)
            - 如果失败，返回 (False, None)
            
    Note:
        该函数会在codeexe目录下执行代码，并等待图片生成
        最多等待10秒
    """
    # 确保codeexe目录存在
    if not os.path.exists('codeexe'):
        os.makedirs('codeexe')
    
    # 生成图片ID
    if image_id is None:
        image_id = str(uuid.uuid4().hex)
    
    # 修改代码中的图片保存路径
    modified_code = code.replace("'answer.png'", f"'chart_{image_id}.png'")
    
    # 创建代码执行agent
    code_executor = ConversableAgent(
        "code_executor",
        llm_config=False,
        code_execution_config={"executor": executor},
        human_input_mode="NEVER"
    )
    
    # 执行代码
    message_with_code = f"""执行以下Python代码：
```python
{modified_code}
```"""
    
    reply = code_executor.generate_reply(messages=[{"role": "user", "content": message_with_code}])
    
    # 等待图片生成
    image_path = f'codeexe/chart_{image_id}.png'
    for _ in range(10):
        if os.path.exists(image_path):
            return True, image_path
        time.sleep(1)
    
    return False, None

def generate_code(file_path, column_descriptions):
    """生成可视化代码的函数
    
    Args:
        file_path (str): CSV文件的路径
        column_descriptions (dict): 数据列的描述信息，格式为 {列名: 描述}
        
    Returns:
        tuple: (生成的代码, 错误信息)
            - 如果成功生成代码，返回 (代码字符串, None)
            - 如果失败，返回 (None, 错误信息字符串)
            
    Note:
        该函数会读取CSV文件的前5行作为样本数据，用于生成可视化代码
        使用Qwen模型生成代码
    """
    # 读取CSV文件的前5行作为样本数据
    try:
        df_sample = pd.read_csv(file_path, nrows=5)
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
    
    data_info = """
数据文件路径: ../{}

数据列描述:
{}

数据示例:
{}

请生成合适的Python代码来可视化这些数据。代码必须：
1. 导入必要的库（pandas, matplotlib）
2. 读取CSV文件 
3. 创建合适的可视化
4. 将图表保存为'answer.png'

请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
""".format(file_path, columns_info, df_sample.to_string())
    
    # 生成代码
    code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
    
    return code_response, None

def create_chart(file_path=None, column_descriptions=None):
    """首次创建图表的函数
    
    Args:
        file_path (str, optional): CSV文件的路径
        column_descriptions (dict, optional): 数据列的描述信息，格式为 {列名: 描述}
        
    Returns:
        tuple: (生成的代码, 图片路径, 结果信息)
            - 如果成功生成图表，返回 (代码字符串, 图片路径, "图表生成成功")
            - 如果失败，返回 (None, None, 错误信息字符串)
            
    Note:
        该函数会先调用generate_code生成可视化代码，然后调用execute_code执行代码生成图表
        整个过程包括代码生成和图表生成两个步骤
    """
    if file_path is None or not os.path.exists(file_path):
        return None, None, "无法生成图表：未找到数据文件"
    
    # 生成代码
    code, error = generate_code(file_path, column_descriptions)
    if error:
        return None, None, error
    
    # 执行代码生成图片
    success, image_path = execute_code(code)
    if success:
        return code, image_path, "图表生成成功"
    return None, None, "图表生成失败"

def regenerate_chart(code):
    """根据现有代码重新生成图表的函数
    
    Args:
        code (str): 要执行的Python代码字符串
        
    Returns:
        tuple: (是否成功, 图片路径, 结果信息)
            - 成功时返回 (True, 图片路径, "图表生成成功")
            - 失败时返回 (False, None, 错误信息字符串)
            
    Note:
        该函数直接执行提供的代码来生成图表，不涉及代码生成过程
        适用于用户修改代码后重新生成图表的场景
    """
    if not code:
        return False, None, "无法生成图表：未提供代码"
    
    success, image_path = execute_code(code)
    if success:
        return True, image_path, "图表生成成功"
    return False, None, "图表生成失败"

def process_data(df):
    """数据处理函数
    
    Args:
        df (pandas.DataFrame): 要处理的数据框
        
    Returns:
        pandas.DataFrame: 处理后的数据框
        
    Note:
        这是一个预留的数据处理函数，目前没有实现具体的处理逻辑
        可以根据需要添加数据清洗、转换等处理步骤
    """
    # 数据处理逻辑
    return df

    