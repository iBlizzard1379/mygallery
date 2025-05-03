import os
import time
import sys
from dotenv import load_dotenv
import logging

# 配置日志 - 更详细的输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"Python版本: {sys.version}")

# 打印环境变量(隐藏部分密钥)
api_key = os.environ.get("OPENAI_API_KEY", "")
if api_key:
    masked_key = api_key[:5] + '*' * (len(api_key) - 10) + api_key[-5:] if len(api_key) > 10 else "***"
    logger.info(f"API Key: {masked_key}")
else:
    logger.warning("未设置API密钥")

model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
logger.info(f"使用模型: {model}")

def test_with_timeout():
    """使用更长的超时时间测试OpenAI API连接"""
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    
    if not api_key:
        logger.error("未设置OPENAI_API_KEY环境变量")
        return False
    
    try:
        # 使用openai库
        logger.info("导入OpenAI库...")
        from openai import OpenAI
        logger.info("OpenAI库导入成功")
        
        # 创建客户端，设置超时时间为60秒
        logger.info("创建OpenAI客户端...")
        client = OpenAI(
            api_key=api_key,
            timeout=120.0,  # 120秒超时
            max_retries=5  # 最多重试5次
        )
        logger.info("OpenAI客户端创建成功")
        
        # 测试简单请求
        logger.info(f"使用模型: {model}")
        logger.info("开始API请求...")
        start_time = time.time()
        
        try:
            logger.info("发送聊天请求...")
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个画廊中的智能助手。"},
                    {"role": "user", "content": "请简短介绍一下你自己。"}
                ]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            response = completion.choices[0].message.content
            logger.info(f"API请求耗时: {duration:.2f}秒")
            logger.info(f"API响应: {response}")
            return True
        except Exception as request_error:
            logger.error(f"API请求期间发生错误: {request_error}")
            return False
        
    except Exception as e:
        logger.error(f"OpenAI初始化过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    logger.info("====== 开始测试OpenAI API (增加超时时间) ======")
    success = test_with_timeout()
    logger.info(f"====== 测试结果: {'成功' if success else '失败'} ======") 