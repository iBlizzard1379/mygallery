"""
搜索工具模块
提供基于互联网的搜索工具，包括Tavily和SerpAPI
"""

import os
import logging
from typing import List, Dict, Any, Optional
import json

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入环境变量管理器
try:
    from env_manager import get_env_manager
    env_manager = get_env_manager()
except ImportError:
    env_manager = None
    logger.warning("环境变量管理器不可用，将使用默认环境变量")

class TavilySearchTool:
    """基于Tavily的搜索工具"""
    
    def __init__(self):
        """初始化Tavily搜索工具"""
        # 获取API密钥
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        if not self.api_key and env_manager:
            self.api_key = env_manager.tavily_api_key
        
        if not self.api_key:
            logger.warning("未配置Tavily API Key，搜索功能将不可用")
            self.client = None
        else:
            try:
                # 尝试导入Tavily客户端
                from tavily import TavilyClient
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily搜索工具初始化成功")
            except ImportError:
                logger.error("无法导入tavily模块，请确保已安装: pip install tavily-python")
                self.client = None
            except Exception as e:
                logger.error(f"初始化Tavily客户端时出错: {e}")
                self.client = None
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用Tavily进行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            搜索结果列表
        """
        if not self.client:
            logger.error("Tavily客户端未初始化，无法进行搜索")
            return []
        
        try:
            logger.info(f"执行Tavily搜索: {query}")
            # 执行搜索
            search_response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            # 处理结果
            results = []
            if "results" in search_response:
                results = search_response["results"]
                logger.info(f"Tavily搜索返回 {len(results)} 个结果")
            
            return results
        
        except Exception as e:
            logger.error(f"Tavily搜索出错: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查Tavily搜索工具是否可用"""
        return self.client is not None

class SerpAPISearchTool:
    """基于SerpAPI的搜索工具"""
    
    def __init__(self):
        """初始化SerpAPI搜索工具"""
        # 获取API密钥
        self.api_key = os.getenv("SERPAPI_API_KEY", "")
        if not self.api_key and env_manager:
            self.api_key = env_manager.serpapi_api_key
        
        if not self.api_key:
            logger.warning("未配置SerpAPI API Key，搜索功能将不可用")
            self.client = None
        else:
            try:
                # 尝试导入SerpAPI客户端
                from serpapi import GoogleSearch
                self.client = GoogleSearch
                logger.info("SerpAPI搜索工具初始化成功")
            except ImportError:
                logger.error("无法导入serpapi模块，请确保已安装: pip install google-search-results")
                self.client = None
            except Exception as e:
                logger.error(f"初始化SerpAPI客户端时出错: {e}")
                self.client = None
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用SerpAPI进行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            搜索结果列表
        """
        if not self.client:
            logger.error("SerpAPI客户端未初始化，无法进行搜索")
            return []
        
        try:
            logger.info(f"执行SerpAPI搜索: {query}")
            # 执行搜索
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": max_results
            }
            
            search = self.client(params)
            search_response = search.get_dict()
            
            # 处理结果
            results = []
            if "organic_results" in search_response:
                for result in search_response["organic_results"][:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "content": result.get("snippet", "")
                    })
                logger.info(f"SerpAPI搜索返回 {len(results)} 个结果")
            
            return results
        
        except Exception as e:
            logger.error(f"SerpAPI搜索出错: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查SerpAPI搜索工具是否可用"""
        return self.client is not None

class SearchToolFactory:
    """搜索工具工厂，用于创建合适的搜索工具"""
    
    @staticmethod
    def create_search_tool() -> Optional[Any]:
        """
        创建搜索工具
        
        Returns:
            搜索工具实例
        """
        # 确定使用哪种搜索工具
        search_tool_type = os.getenv("SEARCH_TOOL", "tavily").lower()
        if env_manager:
            search_tool_type = env_manager.search_tool.lower()
        
        logger.info(f"使用搜索工具: {search_tool_type}")
        
        # 创建对应的搜索工具
        if search_tool_type == "tavily":
            tool = TavilySearchTool()
            if tool.is_available():
                return tool
            
            # 如果Tavily不可用，尝试SerpAPI
            logger.warning("Tavily搜索工具不可用，尝试使用SerpAPI")
            fallback_tool = SerpAPISearchTool()
            if fallback_tool.is_available():
                return fallback_tool
        
        elif search_tool_type == "serpapi":
            tool = SerpAPISearchTool()
            if tool.is_available():
                return tool
            
            # 如果SerpAPI不可用，尝试Tavily
            logger.warning("SerpAPI搜索工具不可用，尝试使用Tavily")
            fallback_tool = TavilySearchTool()
            if fallback_tool.is_available():
                return fallback_tool
        
        logger.error("所有搜索工具都不可用")
        return None

# 单例模式
_search_tool_instance = None

def get_search_tool():
    """
    获取搜索工具实例
    
    Returns:
        搜索工具实例
    """
    global _search_tool_instance
    if _search_tool_instance is None:
        _search_tool_instance = SearchToolFactory.create_search_tool()
    return _search_tool_instance

# 测试代码
if __name__ == "__main__":
    search_tool = get_search_tool()
    if search_tool:
        results = search_tool.search("人工智能的最新发展")
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("搜索工具不可用，请检查API配置") 