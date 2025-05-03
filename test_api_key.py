#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenAI API Key测试脚本
测试API Key是否可正常连接OpenAI API服务
"""

import os
import sys
import time
import json
import logging
from dotenv import load_dotenv

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("api_test")

def load_api_key():
    """从.env文件或环境变量加载API Key"""
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("未找到OPENAI_API_KEY环境变量")
        return None
        
    # 打印API Key的部分内容（仅用于调试）
    masked_key = api_key[:8] + '*' * 5 + api_key[-4:] if len(api_key) > 12 else api_key[:3] + '***'
    logger.info(f"找到API Key: {masked_key}")
    logger.info(f"API Key长度: {len(api_key)}字符")
    
    # 检查API Key格式
    if api_key.startswith("sk-"):
        logger.info("API Key格式正确 (以sk-开头)")
    else:
        logger.warning(f"API Key格式异常 (以{api_key[:6]}开头，不是标准的sk-格式)")
    
    return api_key

def test_direct_api(api_key, model="gpt-3.5-turbo", timeout=30, retries=3):
    """直接使用OpenAI客户端库测试API Key"""
    logger.info(f"测试方法1: 直接OpenAI API调用 (timeout={timeout}s, retries={retries})")
    
    try:
        from openai import OpenAI
        logger.info("成功导入OpenAI客户端库")
        
        # 创建OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            timeout=timeout,  # 设置超时时间
            max_retries=retries  # 设置重试次数
        )
        logger.info("成功创建OpenAI客户端")
        
        # 发送简单的聊天请求
        logger.info(f"向OpenAI发送测试请求 (模型: {model})...")
        start_time = time.time()
        
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个帮助测试API连接的助手。"},
                    {"role": "user", "content": "如果你收到这条消息，请简短回复'API连接成功'。"}
                ]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            response = completion.choices[0].message.content
            logger.info(f"收到回复: '{response}'")
            logger.info(f"请求耗时: {duration:.2f}秒")
            
            return {
                "success": True,
                "method": "direct_api",
                "duration": duration,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"API请求失败: {str(e)}")
            return {
                "success": False,
                "method": "direct_api",
                "error": str(e)
            }
    
    except ImportError as e:
        logger.error(f"导入错误: {str(e)}")
        return {
            "success": False,
            "method": "direct_api",
            "error": f"导入错误: {str(e)}"
        }
    except Exception as e:
        logger.error(f"初始化客户端时出错: {str(e)}")
        return {
            "success": False, 
            "method": "direct_api",
            "error": str(e)
        }

def test_langchain_api(api_key, model="gpt-3.5-turbo", timeout=30):
    """使用LangChain库测试API Key"""
    logger.info(f"测试方法2: 通过LangChain调用 (timeout={timeout}s)")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        logger.info("成功导入LangChain库")
        
        # 创建LangChain聊天模型
        chat = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model,
            request_timeout=timeout,
            max_retries=3,
            streaming=False
        )
        logger.info("成功创建LangChain ChatOpenAI模型")
        
        # 发送简单的聊天请求
        logger.info(f"通过LangChain发送测试请求 (模型: {model})...")
        start_time = time.time()
        
        try:
            messages = [
                SystemMessage(content="你是一个帮助测试API连接的助手。"),
                HumanMessage(content="如果你收到这条消息，请简短回复'LangChain API连接成功'。")
            ]
            
            response = chat.invoke(messages)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"收到回复: '{response.content}'")
            logger.info(f"请求耗时: {duration:.2f}秒")
            
            return {
                "success": True,
                "method": "langchain",
                "duration": duration,
                "response": response.content
            }
            
        except Exception as e:
            logger.error(f"LangChain请求失败: {str(e)}")
            return {
                "success": False,
                "method": "langchain",
                "error": str(e)
            }
    
    except ImportError as e:
        logger.error(f"导入LangChain错误: {str(e)}")
        return {
            "success": False,
            "method": "langchain",
            "error": f"导入错误: {str(e)}"
        }
    except Exception as e:
        logger.error(f"初始化LangChain模型时出错: {str(e)}")
        return {
            "success": False,
            "method": "langchain",
            "error": str(e)
        }

def run_tests():
    """运行所有API测试"""
    logger.info("==== 开始OpenAI API Key测试 ====")
    
    # 加载API Key
    api_key = load_api_key()
    if not api_key:
        logger.error("测试失败: 未找到有效的API Key")
        return
    
    # 获取API模型
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    logger.info(f"使用模型: {model}")
    
    # 运行测试
    results = {}
    
    # 测试1: 短超时直接API调用
    results["test1"] = test_direct_api(api_key, model, timeout=10, retries=1)
    
    # 测试2: 长超时直接API调用
    if not results["test1"]["success"]:
        logger.info("第一次测试失败，尝试增加超时时间...")
        results["test2"] = test_direct_api(api_key, model, timeout=60, retries=3)
    
    # 测试3: LangChain测试
    results["test3"] = test_langchain_api(api_key, model, timeout=30)
    
    # 分析结果
    success_count = sum(1 for test in results.values() if test["success"])
    
    logger.info("\n==== API测试结果摘要 ====")
    logger.info(f"完成测试数: {len(results)}")
    logger.info(f"成功测试数: {success_count}")
    logger.info(f"失败测试数: {len(results) - success_count}")
    
    # 如果所有测试都失败，尝试提供诊断信息
    if success_count == 0:
        logger.warning("\n==== API连接问题诊断 ====")
        logger.warning("所有测试均失败，可能原因:")
        
        # 检查API Key格式
        if not api_key.startswith("sk-"):
            logger.warning("1. API Key格式异常: 不是以'sk-'开头的标准格式。")
        
        # 收集错误信息
        error_messages = set(test["error"] for test in results.values() if not test["success"])
        for i, error in enumerate(error_messages, 1):
            logger.warning(f"{i+1}. 错误信息: {error}")
        
        logger.warning("\n建议解决方案:")
        logger.warning("1. 检查API Key是否正确且完整")
        logger.warning("2. 检查网络连接，可能需要VPN或代理")
        logger.warning("3. 检查API Key的余额和使用限制")
        logger.warning("4. 尝试创建新的API Key")
    else:
        logger.info("\n✅ 至少有一个测试成功，API Key可以正常使用!")
    
    logger.info("\n==== 测试完成 ====")

if __name__ == "__main__":
    run_tests() 