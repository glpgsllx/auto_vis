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

def get_streaming_response(user_message, data_context, message_placeholder=None, image_id=None):
    """获取真正的流式输出响应
    
    Args:
        user_message (str): 用户的输入消息
        data_context (dict): 数据上下文，包含数据框等信息
        message_placeholder (streamlit.empty, optional): 用于显示流式输出的占位符
        image_id (str, optional): 用于保存图片的唯一ID
    
    Returns:
        str: AI助手的完整回复
    """
    # 如果没有提供图片ID，则生成一个
    if image_id is None:
        image_id = uuid.uuid4().hex
    
    # 构建系统消息
    system_message = """你是一个专业的数据分析助手。你可以帮助用户分析和理解数据，并提供专业的见解。同时，您还可以阅读数据可视化的代码并帮助用户修改。

当用户请求生成或修改可视化代码时，请遵循以下规则：
1. 当你需要生成新的可视化代码时，务必将图片保存为'answer.png'
2. 如果你需要修改现有代码，请保留代码的整体结构，图片保存为'answer.png'
3. 确保使用相对路径保存图片，不要使用绝对路径
4. 确保代码能独立运行，必须包含导入必要的库、读取数据和保存图片的完整过程

请记住：所有可视化代码必须将结果保存为'answer.png'，这一点非常重要。最终的代码会由系统自动执行，图片路径会被系统自动修改和管理。
"""
    
    # 创建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"基于以下数据进行分析:\n{data_context}\n\n用户问题: {user_message}"}
    ]
    
    # 初始化模型
    llm = StreamingLLM()
    
    # 创建一个空的回复字符串
    full_reply = ""
    
    # 处理流式响应
    if message_placeholder:
        # 真正的流式输出
        for chunk in llm.generate_response(messages):
            full_reply += chunk
            # 实时更新显示，不添加光标和延迟
            message_placeholder.markdown(full_reply)
    else:
        # 非流式输出
        full_reply = llm.generate_response(messages, stream=False)
    
    return full_reply 