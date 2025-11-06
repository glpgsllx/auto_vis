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
            raise ValueError("MODELSCOPE_API_KEY is not set")
    
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
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
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
    system_message = """You are a professional data analysis assistant. You help users analyze and understand data and provide expert insights.
Please respond based on the conversation history and the current question.

Data source details:
"""
    ds_type = data_context.get("data_source_type")
    ds_details = data_context.get("data_source_details", {})
    col_descs = data_context.get("column_descriptions", {})

    # --- 修改：Prompt 指示使用占位符 --- 
    placeholder_filename = None
    load_instruction = ""

    if ds_type == 'csv':
        placeholder_filename = 'data.csv' # Fixed placeholder
        system_message += f"- Type: File (CSV)\n"
        system_message += f"- Column descriptions below."
        load_instruction = f"When loading data in code, always use `pd.read_csv('{placeholder_filename}')`."
    elif ds_type == 'excel':
        placeholder_filename = 'data.xlsx' # Fixed placeholder
        system_message += f"- Type: File (Excel)\n"
        system_message += f"- Column descriptions below."
        load_instruction = f"When loading data in code, always use `pd.read_excel('{placeholder_filename}')`."
    elif ds_type == 'mysql':
        # MySQL 保持不变，仍需提供连接信息
        conn_info = ds_details.get("connection_info", {})
        table_name = ds_details.get("table_name", "unknown_table")
        system_message += f"- Type: MySQL database\n"
        system_message += f"- Host: {conn_info.get('host', '?')}:{conn_info.get('port', '?')}\n"
        system_message += f"- Database: {conn_info.get('database', '?')}\n"
        system_message += f"- User: {conn_info.get('user', '?')}\n"
        system_message += f"- Table: {table_name}\n"
        load_instruction = f"In code, connect to the above MySQL (password will be injected at runtime) and query the table using `pd.read_sql('SELECT * FROM `{table_name}`', connection)`."
    else:
        system_message += "- Data source not provided or unrecognized.\n"
        load_instruction = "Unable to determine how to load the data."

    system_message += "\nColumn descriptions:\n"
    if col_descs:
        for col, desc in col_descs.items():
            system_message += f"- {col}: {desc if desc else '(no description)'}\n"
    else:
        system_message += "- No column descriptions.\n"

    system_message += """

Current visualization code (if any):
{current_code}

--- Code generation rules ---
{load_instruction}

1. Generate appropriate Python code based on the user's needs:

   A. If the user asks for a visualization (charts, figures):
      - Use matplotlib for plotting
      - Ensure the code is runnable and self-contained (includes necessary imports)
      - Save the final chart to 'answer.svg'
      - Do NOT use seaborn, plotly or other viz libraries
      - Output must be a single Markdown code block starting with ```python and ending with ```; no extra text

   B. If the user asks for analysis-only (stats, calculations, sorting):
      - Generate concise calculation code
      - Use print() to clearly print the question and results
      - Do not include plotting/saving code
      - Ensure outputs are easy to read

Remember: use the specified placeholders when loading files or the specified DB connection when using MySQL.

Do NOT generate extra explanations!!!
""".format(current_code=data_context.get('current_code', '(none)'), load_instruction=load_instruction)

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
                message_placeholder.error(f"Error generating response: {e}")
            except Exception:
                pass
            return None
    else:
        try:
            full_reply = llm.generate_response(messages, stream=False)
        except Exception as e:
            print(f"Error during non-streaming generation: {e}")
            try:
                st.error(f"Error generating response: {e}")
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
    system_message = """You are a professional data analyst. Your task is to explain the execution results of analysis code in a way the user can easily understand.
Ensure the explanation is accurate, professional, and concise. Do not merely repeat numbers; provide insights. If the output is empty, return nothing."""
    
    # 初始化上下文描述
    context_desc = ""
    if data_context:
        ds_type = data_context.get("data_source_type")
        if ds_type:
            context_desc += f"\n\nData source: {ds_type}\n"
        
        if data_context.get('column_descriptions'):
            context_desc += "\nColumn descriptions:\n"
            for col, desc in data_context.get('column_descriptions', {}).items():
                if desc:
                    context_desc += f"- {col}: {desc}\n"
    
    # 构建完整提示
    print("*" * 100)
    print(user_query)
    print("*" * 100)
    prompt = f"""Based on the following code execution output, provide a professional explanation for the user's query "{user_query}":

Output:
```
{output_text}
```
{context_desc}

Provide a concise, professional explanation focusing on key findings and insights, not on repeating numbers. If the output is empty, return nothing.
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
                # Provide a basic analysis if streaming fails
                fallback_response = f"## Analysis Result\n\nHere is the code execution output:\n\n```\n{output_text}\n```\n\nUnable to generate a detailed analysis; please review the output above."
                message_placeholder.markdown(fallback_response)
                return fallback_response
        else:
            try:
                full_reply = llm.generate_response(messages, stream=False)
            except Exception as e:
                print(f"Error during analysis non-streaming generation: {e}")
                # Return basic analysis
                return f"## Analysis Result\n\n```\n{output_text}\n```"
        
        return full_reply or f"## Analysis Result\n\n```\n{output_text}\n```"
    
    except Exception as global_e:
        # Global error handling
        error_message = f"Error generating analysis: {global_e}"
        print(error_message)
        if message_placeholder:
            message_placeholder.error(error_message)
        
        # Return a basic output
        basic_response = f"## Analysis Result\n\nOutput from code execution:\n\n```\n{output_text}\n```"
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
    system_message = """You are a professional data analyst. Your task is to explain the execution results of visualization code and make them easy to understand.
If the output is empty, return nothing. If the content is only warnings, return nothing as well."""
    
    # 初始化上下文描述
    context_desc = ""
    if data_context:
        ds_type = data_context.get("data_source_type")
        if ds_type:
            context_desc += f"\n\nData source: {ds_type}\n"
        
        if data_context.get('column_descriptions'):
            context_desc += "\nColumn descriptions:\n"
            for col, desc in data_context.get('column_descriptions', {}).items():
                if desc:
                    context_desc += f"- {col}: {desc}\n"
    
    # 构建完整提示
    prompt = f"""Based on the following code execution output, provide a professional explanation for the user's query "{user_query}":

Output:
```
{output_text}
```
{context_desc}

Provide a concise, professional explanation to help the user understand the results. If the output is empty, return nothing. If the content is only warnings, also return nothing.
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
                fallback_response = "No output"
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
        error_message = f"Error generating analysis: {global_e}"
        print(error_message)
        if message_placeholder:
            message_placeholder.error(error_message)
        
        # 返回一个基本的输出结果
        basic_response = f"## Analysis Result\n\nOutput from code execution:\n\n```\n{output_text}\n```"
        if message_placeholder:
            message_placeholder.markdown(basic_response)
        return basic_response 