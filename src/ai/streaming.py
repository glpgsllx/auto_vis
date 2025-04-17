import os
import json
import uuid
import requests
import time
import streamlit as st

class StreamingLLM:
    """使用ModelScope API实现真正的流式输出"""
    
    def __init__(self):
        self.api_key = os.environ.get("MODELSCOPE_API_KEY")
        self.base_url = "https://api-inference.modelscope.cn/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-72B-Instruct"
        
        if not self.api_key:
            raise ValueError("环境变量MODELSCOPE_API_KEY未设置")
    
    def _create_headers(self):
        """创建请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _create_payload(self, messages, stream=True):
        """创建请求数据"""
        return {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
    
    def generate_response(self, messages, stream=True):
        """生成回复"""
        headers = self._create_headers()
        payload = self._create_payload(messages, stream)
        
        response = requests.post(
            self.base_url,
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
        """处理流式响应"""
        for line in response.iter_lines():
            if line:
                # 跳过空行和以data: [DONE]结尾的行
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # 去掉'data: '前缀
                    if data == '[DONE]':
                        break
                    
                    try:
                        json_data = json.loads(data)
                        delta = json_data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
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
{load_instruction} # Add the specific loading instruction here

1. 请根据数据和用户需求生成合适的 Python 代码进行可视化。
2. **必须** 使用 matplotlib 进行绘图，**禁止** 使用 seaborn、plotly 或其他可视化库。
3. 确保代码能独立运行（包含必要的 import）。
4. **务必** 将最终生成的图表保存为 'answer.svg'。

请记住：读取数据时使用指定的占位符（如果是文件）或指定的数据库连接/查询（如果是MySQL），并将图表保存为 'answer.svg'。
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