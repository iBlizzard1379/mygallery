import os
import logging
from dotenv import load_dotenv

# 导入自定义模块
try:
    from langchain_helper import create_chat_handler, get_available_models
    from document_processor import get_document_processor
    from file_watcher import get_file_watcher
    from rag_chain import get_rag_chain
    
    has_langchain = True
    has_document_processor = True
    has_file_watcher = True
    has_rag_chain = True
except ImportError as e:
    print(f"警告: 无法导入某些模块: {e}")
    has_langchain = 'langchain_helper' not in str(e)
    has_document_processor = 'document_processor' not in str(e)
    has_file_watcher = 'file_watcher' not in str(e)
    has_rag_chain = 'rag_chain' not in str(e)

# 导入环境变量管理器
try:
    from env_manager import get_env_manager
    env_manager = get_env_manager()
except ImportError:
    env_manager = None
    print("警告: 环境变量管理器不可用，使用默认配置")

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 全局变量
chat_handler = None
document_processor = None
file_watcher = None
rag_chain = None

def setup_components():
    """初始化组件"""
    global chat_handler, document_processor, file_watcher, rag_chain
    
    logger.info("开始初始化组件...")
    
    # 初始化聊天处理器
    if has_langchain:
        try:
            model_type = os.getenv("LLM_MODEL_TYPE", "openai")
            logger.info(f"正在创建聊天处理器，模型类型: {model_type}, API Key: {os.getenv('OPENAI_API_KEY')[:5]}***")
            chat_handler = create_chat_handler(model_type)
            logger.info(f"成功创建聊天处理器，使用模型类型: {model_type}")
        except Exception as e:
            logger.error(f"创建聊天处理器失败: {e}")
            chat_handler = None
    
    # 初始化文档处理器
    if has_document_processor:
        try:
            logger.info("正在创建文档处理器...")
            document_processor = get_document_processor()
            logger.info("成功创建文档处理器")
        except Exception as e:
            logger.error(f"创建文档处理器失败: {e}")
            document_processor = None
    
    # 初始化文件监听器
    if has_file_watcher and document_processor:
        try:
            logger.info("正在创建文件监听器...")
            file_watcher = get_file_watcher()
            logger.info("成功创建文件监听器")
            
            # 处理已存在的文档
            logger.info("处理已存在的文档...")
            file_watcher.process_existing_documents()
            
            # 启动文件监听
            logger.info("启动文件监听...")
            if file_watcher.start():
                logger.info("文件监听器已启动")
        except Exception as e:
            logger.error(f"创建或启动文件监听器失败: {e}")
            file_watcher = None
    
    # 初始化RAG链
    if has_rag_chain and document_processor:
        try:
            logger.info("正在创建RAG链...")
            rag_chain = get_rag_chain()
            logger.info("成功创建RAG链")
        except Exception as e:
            logger.error(f"创建RAG链失败: {e}")
            rag_chain = None
    
    # 返回组件状态
    return {
        "chat_handler": chat_handler is not None,
        "document_processor": document_processor is not None,
        "file_watcher": file_watcher is not None,
        "rag_chain": rag_chain is not None
    }

def cleanup():
    """清理资源"""
    global file_watcher
    
    if file_watcher:
        logger.info("停止文件监听器...")
        file_watcher.stop()
        logger.info("文件监听器已停止")

# 初始化组件
setup_components()

# 注册退出处理函数
import atexit
atexit.register(cleanup) 