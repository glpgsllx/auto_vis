import os
import json
import uuid
import requests
import time
import streamlit as st

class StreamingLLM:
    """使用ModelScope API实现真正的流式输出"""
    
    def __init__(self):
        # self.api_key = os.environ.get("MODELSCOPE_API_KEY")
        # self.api_key = "sk-gJ3cBOaXnX40AE5XVpSyeVmnDgdrDJctFoM44oHegCYeP3JS"
        # self.base_url = "https://yunwu.ai/v1/chat/completions"
        # self.base_url = "http://101.42.22.132:8000/v1/chat/completions"
        self.api_key = "sk-NEuZniCRXEmJjiQ5CHNl8rtTDKcDogk04vUdjUgX7Zjpm9PU"
        self.model = "qwen2.5-72b-instruct"
        self.base_url = "https://yunwu.ai/v1"
        # self.model = "/model"
        
        if not self.api_key:
            raise ValueError("环境变量MODELSCOPE_API_KEY未设置")
    
    def _create_headers(self):
        """创建请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-APIKey": self.api_key,
            "User-Agent": "AutoVis/1.0"
        }
    
    def _create_payload(self, messages, stream=True):
        """创建请求数据"""
        return {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.8,
                "max_tokens": 1500
            }
        }
    
    def generate_response(self, messages, stream=True):
        """生成回复"""
        headers = self._create_headers()
        payload = self._create_payload(messages, stream)
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            stream=stream
        )
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        
        if stream:
            return self._handle_streaming_response(response)
        else:
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def _handle_streaming_response(self, response):
        """处理DashScope流式响应"""
        for line in response.iter_lines():
            if line:
                # 跳过空行
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # 去掉'data: '前缀
                    if data == '[DONE]':
                        break
                    
                    try:
                        json_data = json.loads(data)
                        # 适配DashScope API响应格式
                        if 'choices' in json_data:
                            delta = json_data.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        elif 'output' in json_data:  # DashScope格式
                            content = json_data.get('output', {}).get('text', '')
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

def get_streaming_response(user_message, data_context, history: list = None, message_placeholder=None, image_id=None):
    """获取真正的流式输出响应
    
    Args:
        user_message (str): 用户的当前输入消息
        data_context (dict): 数据上下文，包含数据源类型/详情和列描述
        history (list, optional): 之前的对话历史记录列表
        message_placeholder (streamlit.empty, optional): 用于显示流式输出的占位符
        image_id (str, optional): (目前未使用，因为路径在 code_execution 中处理)
    
    Returns:
        str: AI助手的完整回复, 或 None 如果出错
    """
    # 如果没有提供图片ID，则生成一个
    if image_id is None:
        image_id = uuid.uuid4().hex
    
    # 构建系统消息
    system_message = """你是一个专业的数据分析助手。你可以帮助用户分析和理解数据，并提供专业的见解。
请根据用户的历史对话和当前问题给出回复。

数据源信息:
"""
    ds_type = data_context.get("data_source_type")
    ds_details = data_context.get("data_source_details", {})
    col_descs = data_context.get("column_descriptions", {})

    # --- 修改：Prompt 指示使用占位符 --- 
    placeholder_filename = None
    load_instruction = ""

    if ds_type == 'csv':
        placeholder_filename = 'data.csv' # Fixed placeholder
        system_message += f"- 类型: 文件 (CSV)\n"
        system_message += f"- 列描述见下文。"
        load_instruction = f"代码中读取数据时，请始终使用 `pd.read_csv('{placeholder_filename}')`。"
    elif ds_type == 'excel':
        placeholder_filename = 'data.xlsx' # Fixed placeholder
        system_message += f"- 类型: 文件 (Excel)\n"
        system_message += f"- 列描述见下文。"
        load_instruction = f"代码中读取数据时，请始终使用 `pd.read_excel('{placeholder_filename}')`。"
    elif ds_type == 'mysql':
        # MySQL 保持不变，仍需提供连接信息
        conn_info = ds_details.get("connection_info", {})
        table_name = ds_details.get("table_name", "未知表名")
        system_message += f"- 类型: MySQL数据库\n"
        system_message += f"- 服务器: {conn_info.get('host', '?')}:{conn_info.get('port', '?')}\n"
        system_message += f"- 数据库: {conn_info.get('database', '?')}\n"
        system_message += f"- 用户名: {conn_info.get('user', '?')}\n"
        system_message += f"- 表名: {table_name}\n"
        load_instruction = f"代码中需要连接上述 MySQL 数据库 (密码将在执行时自动填充)，并使用 `pd.read_sql('SELECT * FROM `{table_name}`', connection)` 查询表 '{table_name}'。"
    else:
        system_message += "- 未提供或无法识别的数据源。\n"
        load_instruction = "无法确定数据加载方式。"

    system_message += "\n列描述:\n"
    if col_descs:
        for col, desc in col_descs.items():
            system_message += f"- {col}: {desc if desc else '(无描述)'}\n"
    else:
        system_message += "- 无列描述信息。\n"

    system_message += """

当前可视化代码 (如果存在):
{current_code}

--- 代码生成规则 ---
{load_instruction}

1. 请根据用户需求判断并生成合适的Python代码:

   A. 如果用户需要数据可视化（图表、图形等）:
      - 使用matplotlib进行绘图
      - 确保代码能独立运行（包含必要的import）
      - 务必将最终生成的图表保存为'answer.svg'
      - 不要使用seaborn、plotly或其他可视化库
      - 输出格式必须为【单个】Markdown 代码块，使用```python 开头并以```结尾；不要输出任何额外文字或说明

   B. 如果用户需要数据分析或计算（如均值、总和、排序等统计分析）:
      - 生成简洁的计算代码
      - 使用print()函数打印用户的问题和结果，格式清晰易读
      - 不要包含图表生成或保存代码
      - 确保输出结果便于阅读和理解

请记住：读取数据时使用指定的占位符（如果是文件）或指定的数据库连接/查询（如果是MySQL）。

请不要生成额外的解释！！！
""".format(current_code=data_context.get('current_code', '(无)'), load_instruction=load_instruction)

    # 构建包含历史记录的消息列表
    messages = [{"role": "system", "content": system_message}]
    if history:
        # 限制历史记录长度，避免超出 token 限制 (例如，保留最近 N 条消息)
        max_history_len = 10 # 可调整
        messages.extend(history[-(max_history_len*2):]) # 乘以2大致包含用户和助手
    messages.append({"role": "user", "content": user_message})

    print_messages = messages[-10:] 
    print("[Streaming Request] Sending messages to LLM (last 10):", json.dumps(print_messages, indent=2, ensure_ascii=False))

    # 初始化模型
    llm = StreamingLLM()
    
    # 创建一个空的回复字符串
    full_reply = ""
    
    # 处理流式响应
    if message_placeholder:
        try:
            for chunk in llm.generate_response(messages):
                full_reply += chunk
                message_placeholder.markdown(full_reply)
        except Exception as e:
            print(f"Error during streaming generation: {e}")
            try:
                message_placeholder.error(f"生成回复时出错: {e}")
            except Exception:
                pass
            return None
    else:
        try:
            full_reply = llm.generate_response(messages, stream=False)
        except Exception as e:
            print(f"Error during non-streaming generation: {e}")
            try:
                st.error(f"生成回复时出错: {e}")
            except Exception:
                pass
            return None
    
    return full_reply 

def process_analysis_streaming(output_text, user_query, data_context=None, message_placeholder=None):
    """处理分析结果并提供流式解释
    
    Args:
        output_text (str): 代码执行的输出文本
        user_query (str): 用户的原始查询
        data_context (dict, optional): 数据上下文信息
        message_placeholder (streamlit.empty, optional): 用于显示流式输出的占位符
        
    Returns:
        str: 对分析结果的专业解释
    """
    # 构建系统消息
    system_message = """你是一个专业的数据分析师。你的任务是解释分析代码的执行结果，并将其转化为用户易于理解的内容。
请确保解释准确、专业，同时简洁明了。不要简单重复数字，而是提供有价值的见解和解释。如果执行结果为空，请不要输出内容"""
    
    # 初始化上下文描述
    context_desc = ""
    if data_context:
        ds_type = data_context.get("data_source_type")
        if ds_type:
            context_desc += f"\n\n数据来源: {ds_type}\n"
        
        if data_context.get('column_descriptions'):
            context_desc += "\n列描述信息:\n"
            for col, desc in data_context.get('column_descriptions', {}).items():
                if desc:
                    context_desc += f"- {col}: {desc}\n"
    
    # 构建完整提示
    print("*" * 100)
    print(user_query)
    print("*" * 100)
    prompt = f"""基于以下代码执行结果，对用户的问题"{user_query}"进行专业解释：

执行结果:
```
{output_text}
```
{context_desc}

请提供简洁、专业的解释，帮助用户理解这些结果的意义。专注于重要的发现和洞见，而不是简单重复数字。如果执行结果为空，请不要输出内容
"""
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    
    # 尝试使用LLM进行分析
    try:
        # 初始化模型
        llm = StreamingLLM()
        
        # 创建一个空的回复字符串
        full_reply = ""
        
        # 处理流式响应
        if message_placeholder:
            try:
                for chunk in llm.generate_response(messages):
                    full_reply += chunk
                    message_placeholder.markdown(full_reply)
            except Exception as e:
                print(f"Error during analysis streaming generation: {e}")
                # 在出错情况下，提供一个基本的分析
                fallback_response = f"## 分析结果\n\n以下是代码执行的输出结果：\n\n```\n{output_text}\n```\n\n由于无法生成详细分析，请直接查看上述结果。"
                message_placeholder.markdown(fallback_response)
                return fallback_response
        else:
            try:
                full_reply = llm.generate_response(messages, stream=False)
            except Exception as e:
                print(f"Error during analysis non-streaming generation: {e}")
                # 返回基本分析
                return f"## 分析结果\n\n以下是代码执行的输出结果：\n\n```\n{output_text}\n```"
        
        return full_reply or f"## 分析结果\n\n```\n{output_text}\n```"
    
    except Exception as global_e:
        # 全局异常处理
        error_message = f"生成分析时出错: {global_e}"
        print(error_message)
        if message_placeholder:
            message_placeholder.error(error_message)
        
        # 返回一个基本的输出结果
        basic_response = f"## 分析结果\n\n以下是代码执行的输出结果：\n\n```\n{output_text}\n```"
        if message_placeholder:
            message_placeholder.markdown(basic_response)
        return basic_response 
    
    
def process_image_streaming(output_text, user_query, data_context=None, message_placeholder=None):
    """处理图像生成结果并提供流式解释
    
    Args:
        output_text (str): 代码执行的输出文本
        user_query (str): 用户的原始查询
        data_context (dict, optional): 数据上下文信息
        message_placeholder (streamlit.empty, optional): 用于显示流式输出的占位符
        
    Returns:
        str: 对分析结果的专业解释
    """
    # 构建系统消息
    system_message = """你是一个专业的数据分析师。你的任务是解释分析生成可视化图表代码的执行结果，并将其转化为用户易于理解的内容。
如果执行结果为空，请不要输出内容。如果内容都是警报，请不要输出内容"""
    
    # 初始化上下文描述
    context_desc = ""
    if data_context:
        ds_type = data_context.get("data_source_type")
        if ds_type:
            context_desc += f"\n\n数据来源: {ds_type}\n"
        
        if data_context.get('column_descriptions'):
            context_desc += "\n列描述信息:\n"
            for col, desc in data_context.get('column_descriptions', {}).items():
                if desc:
                    context_desc += f"- {col}: {desc}\n"
    
    # 构建完整提示
    prompt = f"""基于以下代码执行结果，对用户的问题"{user_query}"进行专业解释：

执行结果:
```
{output_text}
```
{context_desc}

请提供简洁、专业的解释，帮助用户理解这些结果的意义。如果执行结果为空，请不要输出内容。如果内容都是警报，请也不要输出内容
"""
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    
    # 尝试使用LLM进行分析
    try:
        # 初始化模型
        llm = StreamingLLM()
        
        # 创建一个空的回复字符串
        full_reply = ""
        
        # 处理流式响应
        if message_placeholder:
            try:
                for chunk in llm.generate_response(messages):
                    full_reply += chunk
                    message_placeholder.markdown(full_reply)
            except Exception as e:
                print(f"Error during analysis streaming generation: {e}")
                # 在出错情况下，提供一个基本的分析
                #fallback_response = f"## 分析结果\n\n以下是代码执行的输出结果：\n\n```\n{output_text}\n```\n\n由于无法生成详细分析，请直接查看上述结果。"
                fallback_response = "没有结果输出"
                message_placeholder.markdown(fallback_response)
                return fallback_response
        else:
            try:
                full_reply = llm.generate_response(messages, stream=False)
            except Exception as e:
                print(f"Error during analysis non-streaming generation: {e}")
                # 返回基本分析
                return ""
        
        return full_reply or ""
    
    except Exception as global_e:
        # 全局异常处理
        error_message = f"生成分析时出错: {global_e}"
        print(error_message)
        if message_placeholder:
            message_placeholder.error(error_message)
        
        # 返回一个基本的输出结果
        basic_response = f"## 分析结果\n\n以下是代码执行的输出结果：\n\n```\n{output_text}\n```"
        if message_placeholder:
            message_placeholder.markdown(basic_response)
        return basic_response 