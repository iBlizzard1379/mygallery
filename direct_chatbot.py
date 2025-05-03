#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接使用OpenAI API的聊天处理器
作为一个简单但可靠的处理器
"""

import os
import logging
import time
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class DirectChatHandler:
    """直接使用OpenAI API的聊天处理器"""
    
    def __init__(self):
        """初始化聊天处理器"""
        # 加载API Key
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.messages = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。回答要简洁但有帮助。"}]
        
        # 检查API Key
        if not self.api_key:
            logger.error("未找到OPENAI_API_KEY环境变量")
            raise ValueError("未找到OPENAI_API_KEY环境变量")
        
        # 规范化API Key (移除可能的空格和换行符)
        self.api_key = self.api_key.strip()
        
        # 导入OpenAI客户端
        try:
            from openai import OpenAI
            # 创建客户端 - 移除不兼容参数
            self.client = OpenAI(api_key=self.api_key)
            logger.info("成功创建OpenAI客户端")
            
            # 测试API连接
            self._test_connection()
        except ImportError as e:
            logger.error(f"导入OpenAI客户端失败: {e}")
            raise
    
    def _test_connection(self):
        """测试与OpenAI API的连接"""
        try:
            test_messages = [
                {"role": "system", "content": "你是一个用于测试API连接的助手。"},
                {"role": "user", "content": "返回'连接成功'"}
            ]
            
            logger.info("测试OpenAI API连接...")
            start_time = time.time()
            
            # 移除不兼容参数
            response = self.client.chat.completions.create(
                model=self.model,
                messages=test_messages
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"API连接测试成功，耗时: {duration:.2f}秒")
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            raise
    
    def chat(self, message):
        """处理用户消息并返回回复"""
        try:
            # 添加用户消息到历史
            self.messages.append({"role": "user", "content": message})
            
            # 调用OpenAI API
            logger.info(f"向OpenAI发送请求 (模型: {self.model})")
            start_time = time.time()
            
            # 移除不兼容参数
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 获取回复
            response = completion.choices[0].message.content
            logger.info(f"收到OpenAI回复，耗时: {duration:.2f}秒")
            
            # 添加助手回复到历史
            self.messages.append({"role": "assistant", "content": response})
            
            return response
        except Exception as e:
            logger.error(f"OpenAI API请求失败: {e}")
            return f"抱歉，无法连接到OpenAI API: {str(e)}"
    
    def clear_history(self):
        """清空聊天历史"""
        self.messages = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。"}]

# 创建单例实例
try:
    chat_handler = DirectChatHandler()
    logger.info("成功创建DirectChatHandler单例")
except Exception as e:
    logger.error(f"创建DirectChatHandler失败: {e}")
    chat_handler = None

def get_chat_handler():
    """获取聊天处理器实例"""
    return chat_handler 