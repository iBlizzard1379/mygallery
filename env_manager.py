"""
环境变量管理器
负责加载、验证和提供环境变量
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv, find_dotenv

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
dotenv_path = find_dotenv(filename='.env', raise_error_if_not_found=False)
if dotenv_path:
    logger.info(f"从 {dotenv_path} 加载环境变量")
    load_dotenv(dotenv_path)
else:
    logger.warning("未找到.env文件，仅使用系统环境变量")


class EnvManager:
    """环境变量管理器类"""
    
    def __init__(self):
        """初始化环境变量管理器"""
        # 服务器配置
        self.server_port = int(os.getenv("PORT", 8000))
        self.gradio_port = int(os.getenv("GRADIO_PORT", 7860))
        
        # 大模型配置
        self.model_type = os.getenv("LLM_MODEL_TYPE", "openai")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.huggingface_model = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-2-7b-chat-hf")
        
        # 向量数据库配置
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))
        self.vector_db = os.getenv("VECTOR_DB", "chroma")
        
        # 搜索工具配置
        self.search_tool = os.getenv("SEARCH_TOOL", "tavily")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        
        # 调试配置
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 初始化验证结果
        self.validation_results = self._validate_env()
    
    def _validate_env(self) -> Dict[str, bool]:
        """
        验证环境变量配置
        
        Returns:
            验证结果字典，键为配置类别，值为是否通过验证
        """
        results = {}
        
        # 验证模型配置
        if self.model_type.lower() == "openai":
            results["model"] = bool(self.openai_api_key) and bool(self.openai_model)
        elif self.model_type.lower() == "huggingface":
            results["model"] = bool(self.huggingface_api_key) and bool(self.huggingface_model)
        else:
            results["model"] = False
        
        # 验证向量数据库配置
        results["vector_db"] = bool(self.vector_db) and self.vector_db.lower() in ["chroma", "faiss"]
        
        # 验证搜索工具配置
        if self.search_tool.lower() == "tavily":
            results["search_tool"] = bool(self.tavily_api_key)
        elif self.search_tool.lower() == "serpapi":
            results["search_tool"] = bool(self.serpapi_api_key)
        else:
            results["search_tool"] = False
        
        return results
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            包含所有配置的字典
        """
        configs = {
            "server": {
                "port": self.server_port,
                "gradio_port": self.gradio_port
            },
            "model": {
                "type": self.model_type,
                "openai_model": self.openai_model,
                "huggingface_model": self.huggingface_model
            },
            "vector_db": {
                "type": self.vector_db,
                "path": self.vector_db_path,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            },
            "search_tool": {
                "type": self.search_tool
            },
            "debug": self.debug,
            "validation": self.validation_results
        }
        
        return configs
    
    def is_valid_config(self, config_type: str) -> bool:
        """
        检查特定配置是否有效
        
        Args:
            config_type: 配置类型，如"model", "vector_db", "search_tool"
        
        Returns:
            配置是否有效
        """
        return self.validation_results.get(config_type, False)
    
    def get_missing_configs(self) -> List[str]:
        """
        获取缺失或无效的配置列表
        
        Returns:
            缺失或无效的配置名称列表
        """
        missing = []
        
        for key, valid in self.validation_results.items():
            if not valid:
                missing.append(key)
        
        return missing
    
    def print_status(self) -> None:
        """打印环境变量配置状态"""
        logger.info("环境变量配置状态:")
        
        # 从不打印敏感信息
        logger.info(f"- 服务器端口: {self.server_port}")
        logger.info(f"- Gradio端口: {self.gradio_port}")
        logger.info(f"- 模型类型: {self.model_type}")
        
        if self.model_type.lower() == "openai":
            logger.info(f"- OpenAI模型: {self.openai_model}")
            logger.info(f"- OpenAI API Key: {'已设置' if self.openai_api_key else '未设置'}")
        elif self.model_type.lower() == "huggingface":
            logger.info(f"- HuggingFace模型: {self.huggingface_model}")
            logger.info(f"- HuggingFace API Key: {'已设置' if self.huggingface_api_key else '未设置'}")
        
        logger.info(f"- 向量数据库类型: {self.vector_db}")
        logger.info(f"- 向量数据库路径: {self.vector_db_path}")
        logger.info(f"- 搜索工具: {self.search_tool}")
        
        # 打印验证结果
        logger.info("验证结果:")
        for key, valid in self.validation_results.items():
            status = "通过" if valid else "失败"
            logger.info(f"- {key}: {status}")
        
        # 打印缺失配置
        missing = self.get_missing_configs()
        if missing:
            logger.warning("以下配置缺失或无效:")
            for item in missing:
                logger.warning(f"- {item}")
        else:
            logger.info("所有必要配置均已设置")

# 创建全局环境变量管理器实例
env_manager = EnvManager()

def get_env_manager() -> EnvManager:
    """
    获取环境变量管理器实例
    
    Returns:
        EnvManager实例
    """
    return env_manager

# 在模块导入时输出配置状态
if __name__ == "__main__":
    env_manager.print_status() 