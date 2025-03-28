import os
import pandas as pd
import streamlit as st
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
import time

# 创建一个本地命令行代码执行器。
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # 每个代码执行的超时时间（秒）。
    work_dir="codeexe",  # 使用临时目录来存储代码文件。
)

config_list = [
    {"model": "Qwen/Qwen2.5-72B-Instruct", "api_key": os.environ.get("MODELSCOPE_API_KEY"), "base_url": "https://api-inference.modelscope.cn/v1/"}
]

# message_with_code_block = """This is a message with code block.
# The code block is below:```python
# import numpy as np
# import matplotlib.pyplot as plt
# x = np.random.randint(0, 100, 100)
# y = np.random.randint(0, 100, 100)
# plt.scatter(x, y)
# plt.savefig('scatter_demo.png')
# print('Scatter plot saved to scatter.png')
# ```
# This is the end of the message.
# """


def process_data(df):
    """数据处理函数"""
    # 数据处理逻辑
    return df

def create_chart():
    """创建图表的函数"""
    # 确保codeexe目录存在
    if not os.path.exists('codeexe'):
        os.makedirs('codeexe')
    
    # 从session state获取数据
    df = st.session_state.df
    
    if df is None:
        return "无法生成图表：未找到数据"
    
    # 创建代码生成agent
    code_generator = ConversableAgent(
        "code_generator",
        system_message="你是一个专业的数据可视化专家。请根据提供的数据生成合适的Python代码来创建数据可视化。使用matplotlib或seaborn库。代码需要将生成的图表保存为'answer.png'。",
        llm_config={"config_list": config_list},
        human_input_mode="NEVER"
    )
    
    # 准备数据信息
    data_info = """
数据内容：
{}

请生成合适的Python代码来可视化这些数据。代码必须：
1. 导入必要的库（matplotlib）
2. 创建合适的可视化
3. 将图表保存为'answer.png'

请仅生成代码！不要生成其他内容！也不要生成```python```这样的符号！
""".format(df.to_string())
    
    # 生成代码
    code_response = code_generator.generate_reply(messages=[{"role": "user", "content": data_info}])
    
    # 保存生成的代码到session state
    st.session_state.generated_code = code_response
    
    # 创建代码执行agent
    code_executor = ConversableAgent(
        "code_executor",
        llm_config=False,
        code_execution_config={"executor": executor},
        human_input_mode="NEVER"
    )
    
    # 执行生成的代码
    message_with_code = """执行以下Python代码：
```python
{}
```""".format(code_response)
    
    reply = code_executor.generate_reply(messages=[{"role": "user", "content": message_with_code}])
    
    # 等待图片生成
    for _ in range(10):  # 增加等待时间到10秒
        if os.path.exists('codeexe/answer.png'):
            return "图表生成成功"
        time.sleep(1)
    
    return "图表生成失败"

    