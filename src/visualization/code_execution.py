import os
import time
import uuid
import streamlit as st
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor

# 创建一个本地命令行代码执行器
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # 每个代码执行的超时时间（秒）
    work_dir="codeexe",  # 使用临时目录来存储代码文件
)

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
    try:
        # 确保codeexe目录存在
        if not os.path.exists('codeexe'):
            os.makedirs('codeexe')
        
        # 生成图片ID
        if image_id is None:
            image_id = str(uuid.uuid4().hex)
        
        # 修改代码中的图片保存路径
        modified_code = code.replace("'answer.png'", f"'chart_{image_id}.svg'").replace("'answer.svg'", f"'chart_{image_id}.svg'")
        
        # 添加中文字体支持
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
        
        # 在import语句后插入字体设置代码
        import_pos = modified_code.find("import")
        if import_pos != -1:
            # 找到import语句后的换行符
            newline_pos = modified_code.find("\n", import_pos)
            if newline_pos != -1:
                # 在import语句后插入字体设置代码
                modified_code = modified_code[:newline_pos+1] + font_support_code + modified_code[newline_pos+1:]
            else:
                # 如果没有找到换行符，直接在代码前添加字体设置
                modified_code = font_support_code + modified_code
        else:
            # 如果没有import语句，直接在代码前添加字体设置
            modified_code = font_support_code + modified_code
        
        # 如果是MySQL查询代码，需要替换连接信息
        if ("mysql.connector.connect" in modified_code or "pymysql.connect" in modified_code) and "mysql_connection_info" in st.session_state:
            # 获取MySQL连接信息
            conn_info = st.session_state.mysql_connection_info
            
            # 替换连接信息 - 同时支持mysql.connector和pymysql格式
            # 处理host
            modified_code = modified_code.replace(
                'host="localhost"',
                f'host="{conn_info["host"]}"'
            ).replace(
                "host='localhost'",
                f"host='{conn_info['host']}'"
            )
            
            # 处理port，如果存在
            if "port" in conn_info:
                modified_code = modified_code.replace(
                    'port=3306',
                    f'port={conn_info["port"]}'
                ).replace(
                    "port=3306",
                    f"port={conn_info['port']}"
                )
            
            # 处理user
            modified_code = modified_code.replace(
                'user="root"',
                f'user="{conn_info["user"]}"'
            ).replace(
                "user='root'",
                f"user='{conn_info['user']}'"
            )
            
            # 处理password
            modified_code = modified_code.replace(
                'password="password"',
                f'password="{conn_info["password"]}"'
            ).replace(
                'password=""',
                f'password="{conn_info["password"]}"'
            ).replace(
                "password='password'",
                f"password='{conn_info['password']}'"
            ).replace(
                "password=''",
                f"password='{conn_info['password']}'"
            )
            
            # 处理database
            modified_code = modified_code.replace(
                'database="database_name"',
                f'database="{conn_info["database"]}"'
            ).replace(
                "database='database_name'",
                f"database='{conn_info['database']}'"
            )
            
            # 处理charset参数，如果存在
            if "charset" in conn_info:
                if "charset=" not in modified_code:
                    # 查找连接函数的结束括号
                    connect_pos = modified_code.find("mysql.connector.connect(")
                    if connect_pos == -1:
                        connect_pos = modified_code.find("pymysql.connect(")
                    
                    if connect_pos != -1:
                        # 寻找对应的结束括号
                        bracket_count = 1
                        for i in range(connect_pos + modified_code[connect_pos:].find("(") + 1, len(modified_code)):
                            if modified_code[i] == "(":
                                bracket_count += 1
                            elif modified_code[i] == ")":
                                bracket_count -= 1
                                if bracket_count == 0:
                                    # 在括号结束前添加charset参数
                                    modified_code = modified_code[:i] + f", charset='{conn_info['charset']}'" + modified_code[i:]
                                    break
                else:
                    # 如果已经存在charset参数，则替换它
                    modified_code = modified_code.replace(
                        'charset="utf8"',
                        f'charset="{conn_info["charset"]}"'
                    ).replace(
                        "charset='utf8'",
                        f"charset='{conn_info['charset']}'"
                    ).replace(
                        'charset="utf8mb4"',
                        f'charset="{conn_info["charset"]}"'
                    ).replace(
                        "charset='utf8mb4'",
                        f"charset='{conn_info['charset']}'"
                    )
            
            # 添加调试信息
            print(f"MySQL连接信息: {conn_info}")
        
        # 打印修改后的代码，方便调试
        print("执行的代码:")
        print("-" * 50)
        print(modified_code)
        print("-" * 50)
        
        # 保存代码到临时文件
        temp_code_file = f'codeexe/code_{image_id}.py'
        with open(temp_code_file, 'w') as f:
            f.write(modified_code)
        
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
        image_path = f'codeexe/chart_{image_id}.svg'
        for _ in range(10):
            if os.path.exists(image_path):
                return True, image_path
            time.sleep(1)
        
        print(f"图片未生成，代码执行结果：{reply}")
        return False, None
    except Exception as e:
        print(f"执行代码时出错：{str(e)}")
        return False, None

def regenerate_chart(code):
    """重新生成图表
    
    Args:
        code (str): 可视化代码
        
    Returns:
        tuple: (是否成功, 图片路径)
            - 如果成功生成图表，返回 (True, 图片路径)
            - 如果失败，返回 (False, None)
    """
    # 生成唯一的图片ID
    image_id = uuid.uuid4().hex
    
    # 执行代码
    return execute_code(code, image_id) 