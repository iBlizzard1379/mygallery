#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix OpenAI API Key脚本
检查并修复.env文件中的API Key格式问题
"""

import os
import re
import sys
import logging
from dotenv import load_dotenv, set_key, find_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("fix_api_key")

def check_env_file():
    """检查.env文件是否存在"""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        logger.error("未找到.env文件，将创建一个新的.env文件")
        dotenv_path = os.path.join(os.getcwd(), '.env')
        with open(dotenv_path, 'w') as f:
            f.write("# OpenAI API设置\n")
        logger.info(f"已创建新的.env文件: {dotenv_path}")
    else:
        logger.info(f"找到.env文件: {dotenv_path}")
    
    return dotenv_path

def read_env_content(dotenv_path):
    """读取.env文件内容"""
    try:
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"读取.env文件失败: {e}")
        return ""

def check_api_key(content):
    """检查API Key格式"""
    api_key_match = re.search(r'OPENAI_API_KEY=([^\n]+)', content)
    if not api_key_match:
        logger.warning("未找到OPENAI_API_KEY设置")
        return None
    
    api_key = api_key_match.group(1).strip()
    
    # 检查API Key是否有换行或空格
    if '\n' in api_key or ' ' in api_key:
        logger.warning("API Key包含换行符或空格，需要修复")
        # 移除所有空白字符
        clean_key = re.sub(r'\s+', '', api_key)
        return clean_key
    
    # 检查API Key格式
    if api_key.startswith('sk-'):
        logger.info("API Key格式正确 (以sk-开头)")
        # 打印API Key的部分内容（仅用于调试）
        masked_key = api_key[:8] + '*' * 5 + api_key[-4:] if len(api_key) > 12 else api_key[:3] + '***'
        logger.info(f"当前API Key: {masked_key}")
        logger.info(f"API Key长度: {len(api_key)}字符")
        return api_key
    else:
        logger.warning(f"API Key格式异常 (以{api_key[:6]}开头，不是标准的sk-格式)")
        return api_key

def fix_api_key(dotenv_path, content):
    """修复API Key问题"""
    current_key = check_api_key(content)
    
    if current_key is None:
        # 提示用户输入新的API Key
        logger.info("请输入您的OpenAI API Key:")
        new_key = input("OPENAI_API_KEY=").strip()
        
        if not new_key:
            logger.error("未输入API Key，操作取消")
            return False
        
        # 设置新的API Key
        set_key(dotenv_path, "OPENAI_API_KEY", new_key)
        logger.info("已添加新的API Key")
        return True
    
    # 检查API Key是否需要修复
    if '\n' in current_key or ' ' in current_key:
        # 修复API Key
        clean_key = re.sub(r'\s+', '', current_key)
        logger.info("修复后的API Key:")
        masked_key = clean_key[:8] + '*' * 5 + clean_key[-4:] if len(clean_key) > 12 else clean_key[:3] + '***'
        logger.info(f"- 长度: {len(clean_key)}字符")
        logger.info(f"- 格式: {masked_key}")
        
        # 确认修复
        logger.info("是否使用这个修复后的API Key? (y/n)")
        confirm = input().strip().lower()
        
        if confirm == 'y':
            # 使用修复后的API Key
            set_key(dotenv_path, "OPENAI_API_KEY", clean_key)
            logger.info("已更新API Key")
            return True
        else:
            logger.info("操作取消")
            return False
    
    # 提示是否要更换API Key
    logger.info("当前API Key看起来格式正确。是否要更换为新的API Key? (y/n)")
    change = input().strip().lower()
    
    if change == 'y':
        logger.info("请输入新的OpenAI API Key:")
        new_key = input("OPENAI_API_KEY=").strip()
        
        if not new_key:
            logger.error("未输入API Key，操作取消")
            return False
        
        # 设置新的API Key
        set_key(dotenv_path, "OPENAI_API_KEY", new_key)
        logger.info("已更新为新的API Key")
        return True
    else:
        logger.info("保留当前API Key")
        return False

def check_other_settings(dotenv_path):
    """检查其他必要的设置"""
    # 加载当前的.env文件
    load_dotenv(dotenv_path)
    
    # 检查必要的设置
    settings = {
        "PORT": os.getenv("PORT", "8000"),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "VECTOR_DB": os.getenv("VECTOR_DB", "faiss"),
        "VECTOR_DB_PATH": os.getenv("VECTOR_DB_PATH", "./vector_db"),
        "LLM_MODEL_TYPE": os.getenv("LLM_MODEL_TYPE", "openai")
    }
    
    # 更新缺失的设置
    updated = False
    for key, default_value in settings.items():
        if not os.getenv(key):
            set_key(dotenv_path, key, default_value)
            logger.info(f"添加了缺失的设置: {key}={default_value}")
            updated = True
    
    if updated:
        logger.info("已更新所有必要的设置")
    else:
        logger.info("所有必要的设置已存在")

def main():
    """主函数"""
    logger.info("==== OpenAI API Key检查和修复工具 ====")
    
    # 检查.env文件
    dotenv_path = check_env_file()
    
    # 读取.env内容
    content = read_env_content(dotenv_path)
    
    # 修复API Key
    api_key_updated = fix_api_key(dotenv_path, content)
    
    # 检查其他设置
    check_other_settings(dotenv_path)
    
    # 总结
    logger.info("\n==== 操作完成 ====")
    if api_key_updated:
        logger.info("API Key已更新。请运行test_api_key.py测试API连接。")
    else:
        logger.info("API Key未更改。如果您遇到API连接问题，请运行test_api_key.py进行测试。")

if __name__ == "__main__":
    main() 