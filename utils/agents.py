import os
from autogen import ConversableAgent

config_list = [
    {
        "model": "Qwen/Qwen2.5-72B-Instruct", 
        "api_key": os.environ.get("MODELSCOPE_API_KEY"), 
        "base_url": "https://api-inference.modelscope.cn/v1/"
    }
]

def get_response(user_message, data_context):
    """获取AI助手的回复
    
    Args:
        user_message (str): 用户的输入消息
        data_context (dict): 数据上下文，包含数据框等信息
    
    Returns:
        str: AI助手的回复
    """
    assistant = ConversableAgent(
        "data_analysis_assistant",
        system_message="你是一个专业的数据分析助手。你可以帮助用户分析和理解数据，并提供专业的见解。",
        llm_config={"config_list": config_list},
        human_input_mode="NEVER"
    )
    
    # 将数据上下文添加到消息中
    full_message = f"基于以下数据进行分析:\n{data_context}\n\n用户问题: {user_message}"
    
    reply = assistant.generate_reply(messages=[{"role": "user", "content": full_message}])
    return reply 