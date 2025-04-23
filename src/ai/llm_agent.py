import os
from autogen import ConversableAgent
import time
import streamlit as st
import uuid

# 配置大语言模型
config_list = [
    {
        "model": "Qwen/Qwen2.5-72B-Instruct", 
        "api_key": os.environ.get("MODELSCOPE_API_KEY"), 
        "base_url": "https://api-inference.modelscope.cn/v1/"
    }
]

def get_response(user_message, data_context, message_placeholder=None, image_id=None):
    """获取AI助手的回复，支持流式输出
    
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
    
    # 构建系统消息，包含处理图片路径的指令
    system_message = f"""你是一个专业的数据分析助手。你可以帮助用户分析和理解数据，并提供专业的见解。同时，您还可以阅读数据可视化的代码并帮助用户修改。

当用户请求生成或修改可视化代码时，请遵循以下规则：
1. 当你需要生成新的可视化代码时，务必将图片保存为'answer.png'
2. 如果你需要修改现有代码，请保留代码的整体结构，图片保存为'answer.png'
3. 确保使用相对路径保存图片，不要使用绝对路径
4. 确保代码能独立运行，必须包含导入必要的库、读取数据和保存图片的完整过程

请记住：所有可视化代码必须将结果保存为'answer.png'，这一点非常重要。最终的代码会由系统自动执行，图片路径会被系统自动修改和管理。
"""
    
    assistant = ConversableAgent(
        "data_analysis_assistant",
        system_message=system_message,
        llm_config={"config_list": config_list},
        human_input_mode="NEVER"
    )
    
    # 将数据上下文添加到消息中
    full_message = f"基于以下数据进行分析:\n{data_context}\n\n用户问题: {user_message}"
    
    # 创建一个空的回复字符串
    full_reply = ""
    
    # 如果提供了占位符，使用流式输出
    if message_placeholder:
        # 使用generate_reply的stream参数获取流式响应
        for chunk in assistant.generate_reply(
            messages=[{"role": "user", "content": full_message}],
            stream=True
        ):
            if chunk:
                full_reply += chunk
                # 更新占位符显示
                message_placeholder.write(full_reply + "▌")
                time.sleep(0.01)  # 添加小延迟使输出更自然
        
        # 最后更新一次，移除光标
        message_placeholder.write(full_reply)
    else:
        # 如果没有提供占位符，使用普通输出
        full_reply = assistant.generate_reply(messages=[{"role": "user", "content": full_message}])
    
    return full_reply 

def process_analysis_result(output_text, user_query, data_context=None, message_placeholder=None):
    """处理分析结果并让LLM解释，支持流式输出
    
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
请确保解释准确、专业，同时简洁明了。不要简单重复数字，而是提供有价值的见解和解释。"""
    
    # 初始化上下文描述
    context_desc = ""
    if data_context:
        if data_context.get('column_descriptions'):
            context_desc += "\n\n列描述信息:\n"
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

请提供简洁、专业的解释，帮助用户理解这些结果的意义。专注于重要的发现和洞见，而不是简单重复数字。
"""
    
    # 使用ConversableAgent获取解释
    explanation_agent = ConversableAgent(
        "analysis_explainer",
        system_message=system_message,
        llm_config={"config_list": config_list},
        human_input_mode="NEVER"
    )
    
    # 创建一个空的回复字符串
    full_reply = ""
    
    # 如果提供了占位符，使用流式输出
    if message_placeholder:
        # 使用generate_reply的stream参数获取流式响应
        for chunk in explanation_agent.generate_reply(
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            if chunk:
                full_reply += chunk
                # 更新占位符显示
                message_placeholder.markdown(full_reply + "▌")
                time.sleep(0.01)  # 添加小延迟使输出更自然
        
        # 最后更新一次，移除光标
        message_placeholder.markdown(full_reply)
    else:
        # 如果没有提供占位符，使用普通输出
        full_reply = explanation_agent.generate_reply(messages=[{"role": "user", "content": prompt}])
    
    return full_reply