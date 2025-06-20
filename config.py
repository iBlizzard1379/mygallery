"""
项目配置常量
"""

# 默认配置
class DefaultConfig:
    # 服务器配置
    DEFAULT_PORT = 8000
    
    # 模型配置（仅支持OpenAI）
    DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
    
    # 向量数据库配置
    DEFAULT_VECTOR_DB_PATH = "./vector_db"
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_VECTOR_DB = "faiss"
    
    # 搜索工具配置
    DEFAULT_SEARCH_TOOL = "tavily"

# 支持的选项
class SupportedOptions:
    MODEL_TYPES = ["openai"]  # 仅支持OpenAI
    VECTOR_DBS = ["faiss"]  # 仅保留实际使用的FAISS
    SEARCH_TOOLS = ["tavily", "serpapi"]
    
    # OpenAI模型列表
    OPENAI_MODELS = [
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo-preview",
        "gpt-4o"
    ]
    
    # 保持向后兼容性（虽然不再使用HuggingFace）
    HUGGINGFACE_MODELS = [] 