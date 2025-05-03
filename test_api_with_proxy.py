#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用代理的OpenAI API测试脚本
测试通过HTTP代理连接OpenAI API
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("api_proxy_test")

# 加载环境变量
load_dotenv()

# 代理配置 - 可以根据需要修改
# 常见代理格式: http://user:pass@host:port 或 http://host:port
HTTP_PROXY = os.environ.get("HTTP_PROXY", "")
HTTPS_PROXY = os.environ.get("HTTPS_PROXY", "")

def test_with_proxy(proxy_url=None, timeout=60):
    """使用指定代理测试OpenAI API"""
    if not proxy_url:
        logger.warning("未指定代理URL，将尝试使用环境变量中的代理设置")
        proxy_url = HTTPS_PROXY or HTTP_PROXY
    
    if not proxy_url:
        logger.warning("未找到任何代理设置，将直接连接")
    else:
        logger.info(f"使用代理: {proxy_url}")
    
    # 获取API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("未找到OPENAI_API_KEY环境变量")
        return False
    
    # 检查API Key格式
    masked_key = api_key[:6] + "***" + api_key[-4:] if len(api_key) > 10 else "***"
    logger.info(f"使用API Key: {masked_key}")
    
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    logger.info(f"使用模型: {model}")
    
    # 设置代理环境变量
    original_http_proxy = os.environ.get("HTTP_PROXY")
    original_https_proxy = os.environ.get("HTTPS_PROXY")
    
    if proxy_url:
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        logger.info("已设置环境变量代理")
    
    try:
        from openai import OpenAI
        import httpx
        logger.info("成功导入所需库")
        
        # 创建代理传输
        transport = None
        if proxy_url:
            try:
                transport = httpx.HTTPTransport(proxy=proxy_url)
                logger.info("已创建代理传输")
            except Exception as proxy_err:
                logger.error(f"代理传输创建失败: {proxy_err}")
        
        # 创建客户端选项
        client_args = {
            "api_key": api_key,
            "timeout": timeout,
            "max_retries": 3
        }
        
        # 如果有代理传输，则添加
        if transport:
            client_args["http_client"] = httpx.Client(transport=transport)
        
        # 创建OpenAI客户端
        client = OpenAI(**client_args)
        logger.info("成功创建OpenAI客户端")
        
        # 测试连接
        logger.info("发送测试请求...")
        start_time = time.time()
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个用于测试API连接的助手。"},
                    {"role": "user", "content": "请回复'通过代理连接OpenAI API成功'。"}
                ]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            text_response = response.choices[0].message.content
            logger.info(f"收到回复: {text_response}")
            logger.info(f"请求耗时: {duration:.2f}秒")
            logger.info("✅ 连接测试成功!")
            return True
            
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return False
            
    except ImportError as ie:
        logger.error(f"导入错误: {ie}")
        return False
    except Exception as e:
        logger.error(f"发生错误: {e}")
        return False
    finally:
        # 恢复原始代理设置
        if original_http_proxy:
            os.environ["HTTP_PROXY"] = original_http_proxy
        else:
            os.environ.pop("HTTP_PROXY", None)
            
        if original_https_proxy:
            os.environ["HTTPS_PROXY"] = original_https_proxy
        else:
            os.environ.pop("HTTPS_PROXY", None)
        
        logger.info("已恢复原始代理设置")

def run_tests():
    """运行多种代理测置的测试"""
    logger.info("==== 开始OpenAI API代理连接测试 ====")
    
    # 检查是否有环境变量代理
    env_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if env_proxy:
        logger.info(f"使用环境变量代理: {env_proxy}")
        success = test_with_proxy(env_proxy)
    else:
        # 直接连接
        logger.info("尝试直接连接 (无代理)")
        success = test_with_proxy(None)
        
        # 如果直接连接失败，可以尝试常见的代理设置
        if not success:
            logger.info("直接连接失败，请考虑以下选项:")
            logger.info("1. 设置HTTP_PROXY或HTTPS_PROXY环境变量")
            logger.info("2. 或手动编辑此脚本，在顶部设置HTTP_PROXY变量")
            logger.info("3. 或使用下面的命令指定代理:")
            logger.info("   python test_api_with_proxy.py http://your-proxy-host:port")
    
    logger.info("==== 测试完成 ====")
    return success

if __name__ == "__main__":
    # 检查是否有命令行代理参数
    proxy = None
    if len(sys.argv) > 1:
        proxy = sys.argv[1]
        logger.info(f"使用命令行指定代理: {proxy}")
    
    success = test_with_proxy(proxy)
    
    if not success:
        logger.warning("代理测试失败。请检查API Key和代理设置。")
        sys.exit(1)
    else:
        logger.info("代理测试成功!")
        sys.exit(0) 