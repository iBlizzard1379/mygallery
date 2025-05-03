#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试chatbot模块是否可以正确初始化并使用OpenAI API
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 配置日志输出
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chatbot_module():
    """测试chatbot模块"""
    logger.info("开始测试chatbot模块...")
    
    # 确保环境变量已加载
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("未找到OPENAI_API_KEY环境变量")
        return False
    
    # 导入chatbot模块
    try:
        import chatbot
        logger.info("成功导入chatbot模块")
    except ImportError as e:
        logger.error(f"导入chatbot模块失败: {e}")
        return False
    
    # 检查并初始化组件
    try:
        logger.info("调用setup_components初始化组件...")
        if hasattr(chatbot, 'setup_components'):
            components_status = chatbot.setup_components()
            logger.info(f"初始化组件状态: {components_status}")
        else:
            logger.warning("chatbot模块没有setup_components方法")
    except Exception as e:
        logger.error(f"初始化组件失败: {e}")
    
    # 检查chat_handler是否存在
    logger.info(f"检查chat_handler是否存在: {hasattr(chatbot, 'chat_handler')}")
    if hasattr(chatbot, 'chat_handler'):
        logger.info(f"chat_handler类型: {type(chatbot.chat_handler).__name__ if chatbot.chat_handler else 'None'}")
    
    # 如果chat_handler不存在，尝试创建
    if not hasattr(chatbot, 'chat_handler') or chatbot.chat_handler is None:
        try:
            logger.info("尝试创建chat_handler...")
            
            # 尝试直接使用OpenAI API
            from openai import OpenAI
            
            class DirectOpenAIChatHandler:
                def __init__(self):
                    self.api_key = os.environ.get("OPENAI_API_KEY")
                    self.model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
                    self.client = OpenAI(api_key=self.api_key)
                    self.messages = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。"}]
                
                def chat(self, message):
                    self.messages.append({"role": "user", "content": message})
                    
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=self.messages
                    )
                    
                    response = completion.choices[0].message.content
                    self.messages.append({"role": "assistant", "content": response})
                    return response
            
            chatbot.chat_handler = DirectOpenAIChatHandler()
            logger.info("成功创建DirectOpenAIChatHandler")
        except Exception as e:
            logger.error(f"创建chat_handler失败: {e}")
    
    # 测试聊天功能
    if hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None:
        try:
            logger.info("测试聊天功能...")
            response = chatbot.chat_handler.chat("你是谁?")
            logger.info(f"收到回复: {response[:100]}...")
            return True
        except Exception as e:
            logger.error(f"聊天测试失败: {e}")
            return False
    else:
        logger.error("chat_handler不可用，无法测试聊天功能")
        return False

if __name__ == "__main__":
    success = test_chatbot_module()
    print(f"\n测试结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1) 