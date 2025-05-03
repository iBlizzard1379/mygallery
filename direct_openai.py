"""
直接使用OpenAI客户端的聊天处理器
"""

import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class DirectOpenAIChatHandler:
    """
    直接使用OpenAI客户端的聊天处理器
    """
    
    def __init__(self):
        """初始化聊天处理器"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.chat_history = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。"}]
        
        # 测试API连接
        self.test_connection()
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            logger.info("测试OpenAI API连接...")
            from openai import OpenAI
            
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=120.0,
                max_retries=5
            )
            
            # 测试连接，使用短的提示
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个助手。"},
                    {"role": "user", "content": "你好"}
                ]
            )
            
            logger.info("OpenAI API连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI API连接测试失败: {e}")
            self.client = None
            return False
    
    def chat(self, message: str) -> str:
        """
        处理用户消息并返回回复
        
        Args:
            message: 用户输入的消息
        
        Returns:
            AI的响应文本
        """
        if not self.client:
            # 重新尝试连接
            if not self.test_connection():
                return f"抱歉，无法连接到AI服务。您的消息是：{message}"
            
        try:
            # 添加用户消息
            self.chat_history.append({"role": "user", "content": message})
            
            # 只保留最近的10个消息，以避免超出token限制
            if len(self.chat_history) > 11:  # system消息 + 最多10个交互消息
                # 保留system消息和最近的消息
                self.chat_history = [self.chat_history[0]] + self.chat_history[-10:]
            
            # 发送请求
            logger.info(f"向OpenAI发送请求，使用模型：{self.model_name}")
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.chat_history,
                temperature=0.7,
                timeout=120.0
            )
            
            # 获取回复
            response = completion.choices[0].message.content
            
            # 添加到历史
            self.chat_history.append({"role": "assistant", "content": response})
            
            logger.info(f"收到OpenAI响应: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"处理聊天消息时出错: {e}")
            return f"抱歉，处理您的消息时出现了问题: {str(e)}"
    
    def clear_history(self) -> None:
        """清空聊天历史，仅保留系统提示"""
        self.chat_history = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。"}]
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取聊天历史"""
        return self.chat_history

# 创建单例实例
_chat_handler = None

def get_chat_handler():
    """
    获取聊天处理器实例
    
    Returns:
        DirectOpenAIChatHandler实例
    """
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = DirectOpenAIChatHandler()
    return _chat_handler 