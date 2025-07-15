"""
资源管理器 - 管理共享资源如向量数据库连接
确保多用户并发访问时的线程安全
"""
import threading
import logging
from typing import Optional, List, Dict, Any
import os
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class ResourceManager:
    """资源管理器 - 单例模式，管理共享资源"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._init_resources()
            self.initialized = True
    
    def _init_resources(self):
        """初始化共享资源"""
        try:
            # 初始化文档处理器
            from document_processor import get_document_processor
            self.document_processor = get_document_processor()
            logger.info("文档处理器初始化成功")
            
            # 创建向量数据库访问锁
            self.vectorstore_lock = threading.Lock()
            
            # 创建文档搜索锁
            self.search_lock = threading.Lock()
            
            # 缓存向量数据库实例
            self._vectorstore_cache = None
            self._vectorstore_cache_lock = threading.Lock()
            
            # 资源统计
            self._access_count = 0
            self._error_count = 0
            self._stats_lock = threading.Lock()
            
            logger.info("资源管理器初始化完成")
            
        except Exception as e:
            logger.error(f"资源管理器初始化失败: {e}")
            raise
    
    def get_vectorstore(self):
        """线程安全地获取向量数据库"""
        with self._vectorstore_cache_lock:
            if self._vectorstore_cache is None:
                try:
                    self._vectorstore_cache = self.document_processor.get_vectorstore()
                    logger.info("向量数据库缓存已更新")
                except Exception as e:
                    logger.error(f"获取向量数据库失败: {e}")
                    self._increment_error_count()
                    raise
            
            self._increment_access_count()
            return self._vectorstore_cache
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """线程安全地搜索文档"""
        with self.search_lock:
            try:
                self._increment_access_count()
                vectorstore = self.get_vectorstore()
                if vectorstore is None:
                    logger.warning("向量数据库不可用，返回空结果")
                    return []
                
                # 执行搜索
                results = vectorstore.similarity_search(query, k=k)
                logger.info(f"文档搜索完成: 查询='{query}', 结果数={len(results)}")
                return results
                
            except Exception as e:
                logger.error(f"文档搜索失败: {e}")
                self._increment_error_count()
                return []
    
    def search_documents_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """线程安全地搜索文档（带相似度分数）"""
        with self.search_lock:
            try:
                self._increment_access_count()
                vectorstore = self.get_vectorstore()
                if vectorstore is None:
                    logger.warning("向量数据库不可用，返回空结果")
                    return []
                
                # 执行带分数的搜索
                results = vectorstore.similarity_search_with_score(query, k=k)
                logger.info(f"文档搜索（带分数）完成: 查询='{query}', 结果数={len(results)}")
                return results
                
            except Exception as e:
                logger.error(f"文档搜索（带分数）失败: {e}")
                self._increment_error_count()
                return []
    
    def process_document(self, file_path: str) -> bool:
        """线程安全地处理文档"""
        try:
            self._increment_access_count()
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 处理文档
            success = self.document_processor.process_document(file_path)
            
            if success:
                # 清除向量数据库缓存，强制重新加载
                with self._vectorstore_cache_lock:
                    self._vectorstore_cache = None
                    logger.info("向量数据库缓存已清除，将在下次访问时重新加载")
            
            return success
            
        except Exception as e:
            logger.error(f"处理文档失败: {file_path} - {e}")
            self._increment_error_count()
            return False
    
    def get_document_metadata(self) -> Dict[str, Any]:
        """获取文档元数据"""
        try:
            return self.document_processor.document_metadata
        except Exception as e:
            logger.error(f"获取文档元数据失败: {e}")
            return {}
    
    def refresh_vectorstore(self) -> bool:
        """刷新向量数据库缓存"""
        try:
            with self._vectorstore_cache_lock:
                self._vectorstore_cache = None
                logger.info("向量数据库缓存已手动清除")
            
            # 立即重新加载
            self.get_vectorstore()
            return True
            
        except Exception as e:
            logger.error(f"刷新向量数据库失败: {e}")
            self._increment_error_count()
            return False
    
    def _increment_access_count(self):
        """增加访问计数"""
        with self._stats_lock:
            self._access_count += 1
    
    def _increment_error_count(self):
        """增加错误计数"""
        with self._stats_lock:
            self._error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取资源使用统计"""
        with self._stats_lock:
            stats = {
                "access_count": self._access_count,
                "error_count": self._error_count,
                "error_rate": self._error_count / max(self._access_count, 1) * 100,
                "vectorstore_cached": self._vectorstore_cache is not None
            }
        
        # 添加文档处理器统计
        try:
            doc_metadata = self.get_document_metadata()
            stats.update({
                "processed_documents": len(doc_metadata),
                "document_files": list(doc_metadata.keys()) if doc_metadata else []
            })
        except Exception as e:
            logger.warning(f"获取文档统计失败: {e}")
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": threading.current_thread().ident
        }
        
        # 检查文档处理器
        try:
            if self.document_processor:
                health_status["checks"]["document_processor"] = "ok"
            else:
                health_status["checks"]["document_processor"] = "error"
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["document_processor"] = f"error: {e}"
            health_status["status"] = "unhealthy"
        
        # 检查向量数据库
        try:
            vectorstore = self.get_vectorstore()
            if vectorstore:
                health_status["checks"]["vectorstore"] = "ok"
            else:
                health_status["checks"]["vectorstore"] = "error"
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["vectorstore"] = f"error: {e}"
            health_status["status"] = "unhealthy"
        
        # 检查搜索功能
        try:
            # 执行一个简单的搜索测试
            test_results = self.search_documents("test", k=1)
            health_status["checks"]["search"] = "ok"
        except Exception as e:
            health_status["checks"]["search"] = f"error: {e}"
            health_status["status"] = "unhealthy"
        
        return health_status
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info("开始清理资源管理器...")
            
            with self._vectorstore_cache_lock:
                self._vectorstore_cache = None
            
            logger.info("资源管理器清理完成")
            
        except Exception as e:
            logger.error(f"清理资源管理器失败: {e}")

# 全局资源管理器实例
resource_manager = ResourceManager()

def get_resource_manager() -> ResourceManager:
    """获取全局资源管理器实例"""
    return resource_manager

# 便捷函数
def search_documents(query: str, k: int = 5) -> List[Document]:
    """便捷的文档搜索函数"""
    return resource_manager.search_documents(query, k)

def get_vectorstore():
    """便捷的向量数据库获取函数"""
    return resource_manager.get_vectorstore()

def process_document(file_path: str) -> bool:
    """便捷的文档处理函数"""
    return resource_manager.process_document(file_path) 