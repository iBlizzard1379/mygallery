import os
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def test_openai_api():
    """测试OpenAI API连接"""
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    
    if not api_key:
        logger.error("未设置OPENAI_API_KEY环境变量")
        return False
    
    try:
        # 使用openai库
        logger.info("尝试使用openai库")
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # 测试简单请求
        logger.info(f"使用模型: {model}")
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个画廊中的智能助手。"},
                {"role": "user", "content": "你好，你是什么模型？"}
            ]
        )
        
        response = completion.choices[0].message.content
        logger.info(f"API响应: {response}")
        return True
        
    except Exception as e:
        logger.error(f"OpenAI API测试失败: {e}")
        return False
    
def test_langchain():
    """测试LangChain集成"""
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    
    if not api_key:
        logger.error("未设置OPENAI_API_KEY环境变量")
        return False
    
    try:
        # 使用LangChain
        logger.info("尝试使用langchain_openai")
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOpenAI(openai_api_key=api_key, model_name=model)
        
        messages = [
            SystemMessage(content="你是一个画廊中的智能助手。"),
            HumanMessage(content="你好，你是什么模型？")
        ]
        
        response = llm.invoke(messages)
        logger.info(f"LangChain响应: {response.content}")
        return True
        
    except Exception as e:
        logger.error(f"LangChain测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始测试OpenAI API")
    openai_success = test_openai_api()
    logger.info(f"OpenAI API测试结果: {'成功' if openai_success else '失败'}")
    
    logger.info("\n开始测试LangChain集成")
    langchain_success = test_langchain()
    logger.info(f"LangChain测试结果: {'成功' if langchain_success else '失败'}") 