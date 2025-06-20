"""
LangChain助手模块，负责初始化LLM模型、链接组件并处理聊天功能
"""

import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from config import DefaultConfig

# LangChain导入
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """
你是一个画廊中的智能助手，能够回答关于艺术品和展示的PDF文档的问题。
如果用户问的问题在你的知识库中，请基于你的知识库回答。
如果用户问的问题不在你的知识库中，请告诉用户你不知道，然后尝试使用搜索工具寻找答案。
保持友好和专业的语气，回答应该简洁明了。
"""

class BaseLLMModel(ABC):
    """LLM模型的基类"""
    
    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        """返回LLM实例"""
        pass

class OpenAIModel(BaseLLMModel):
    """OpenAI模型"""
    
    def __init__(self, model_name: str = None, temperature: float = 0.7):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("OPENAI_MODEL", DefaultConfig.DEFAULT_OPENAI_MODEL)
        self.temperature = temperature
    
    def get_llm(self) -> BaseChatModel:
        """返回OpenAI LLM实例"""
        if not self.api_key:
            raise ValueError("未设置OpenAI API Key")
        
        return ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            request_timeout=120,  # 增加超时时间到120秒
            max_retries=5,        # 设置最大重试次数为5次
            streaming=False       # 禁用流式传输以避免连接问题
        )

class ChatHandler:
    """聊天处理器，管理聊天历史和模型响应"""
    
    def __init__(self):
        """初始化聊天处理器"""
        self.llm = self._init_llm()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.system_prompt = os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
        self.chat_history = []
        self._init_conversation()
    
    def _init_llm(self) -> BaseChatModel:
        """初始化OpenAI LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", DefaultConfig.DEFAULT_OPENAI_MODEL)
        
        if not api_key:
            raise ValueError("未设置OpenAI API Key")
        
        return ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=0.7,
            request_timeout=120,
            max_retries=5,
            streaming=False
        )
    
    def _init_conversation(self) -> None:
        """初始化对话，设置系统提示词"""
        self.chat_history = [SystemMessage(content=self.system_prompt)]
    
    def chat(self, user_message: str) -> str:
        """
        处理用户消息并返回AI响应
        
        Args:
            user_message: 用户输入的消息
        
        Returns:
            AI的响应文本
        """
        try:
            # 添加用户消息到历史
            self.chat_history.append(HumanMessage(content=user_message))
            
            # 获取AI响应
            ai_message = self.llm.invoke(self.chat_history)
            
            # 添加AI响应到历史
            self.chat_history.append(ai_message)
            
            return ai_message.content
        except Exception as e:
            logger.error(f"生成聊天响应时出错: {e}")
            return f"抱歉，处理您的请求时出现了问题: {str(e)}"
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        获取格式化的聊天历史
        
        Returns:
            聊天历史列表，格式为 [{"role": "human", "content": "..."}, {"role": "ai", "content": "..."}]
        """
        formatted_history = []
        
        for message in self.chat_history:
            if isinstance(message, HumanMessage):
                formatted_history.append({"role": "human", "content": message.content})
            elif isinstance(message, AIMessage):
                formatted_history.append({"role": "ai", "content": message.content})
            # 跳过系统消息
        
        return formatted_history
    
    def clear_history(self) -> None:
        """清空聊天历史，仅保留系统提示"""
        self._init_conversation()

def get_available_models() -> Dict[str, List[str]]:
    """
    获取可用的模型列表
    
    Returns:
        字典，包含模型类型和对应的模型列表
    """
    models = {
        "openai": [
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo"
        ]
    }
    
    return models

def create_chat_handler(model_type: str = None) -> ChatHandler:
    """
    创建聊天处理器
    
    Args:
        model_type: 使用的模型类型 ("openai" 或 "huggingface")
    
    Returns:
        ChatHandler实例
    """
    if model_type is None:
        # 从环境变量读取默认模型类型
        model_type = os.getenv("LLM_MODEL_TYPE", "openai")
    
    try:
        return ChatHandler()
    except Exception as e:
        logger.error(f"创建聊天处理器失败: {e}")
        # 如果无法创建指定模型，尝试使用备用模型
        if model_type.lower() != "openai":
            logger.info("尝试使用OpenAI模型作为备用")
            return ChatHandler()
        raise 