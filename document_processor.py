"""
文档处理模块（兼容性包装器）
为了保持向后兼容性，现在使用增强的多格式文档处理器
"""

import logging
from typing import List, Tuple, Dict, Any
from langchain_core.documents import Document

# 导入增强的文档处理器
try:
    from document_processors.enhanced_document_processor import get_enhanced_document_processor
    from document_processors.enhanced_document_processor import EnhancedDocumentProcessor as _EnhancedDocumentProcessor
except ImportError:
    # 如果导入失败，创建一个简单的替代实现
    logger = logging.getLogger(__name__)
    logger.error("无法导入增强文档处理器，功能将受限")
    get_enhanced_document_processor = None
    _EnhancedDocumentProcessor = None

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    文档处理器（兼容性包装器）
    现在委托给增强的多格式文档处理器
    """
    
    def __init__(self, documents_dir: str = None, vector_db_path: str = None):
        """
        初始化文档处理器
        
        Args:
            documents_dir: 文档目录，默认为 'images'
            vector_db_path: 向量数据库路径
        """
        if get_enhanced_document_processor:
            # 使用增强的文档处理器
            self._enhanced_processor = get_enhanced_document_processor()
            
            # 如果指定了不同的参数，创建新实例
            if (documents_dir and documents_dir != self._enhanced_processor.documents_dir) or \
               (vector_db_path and vector_db_path != self._enhanced_processor.vector_db_path):
                self._enhanced_processor = _EnhancedDocumentProcessor(documents_dir, vector_db_path)
        else:
            raise ImportError("无法初始化增强文档处理器")
        
        # 保持向后兼容的属性
        self.documents_dir = self._enhanced_processor.documents_dir
        self.vector_db_path = self._enhanced_processor.vector_db_path
        self.chunk_size = self._enhanced_processor.chunk_size
        self.chunk_overlap = self._enhanced_processor.chunk_overlap
        self.embeddings = self._enhanced_processor.embeddings
        self.vectorstore = self._enhanced_processor.vectorstore
        self.document_metadata = self._enhanced_processor.document_metadata
    
    def process_document(self, file_path: str) -> bool:
        """
        处理单个文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            处理是否成功
        """
        return self._enhanced_processor.process_document(file_path)
    
    def process_all_documents(self) -> Tuple[int, int]:
        """
        处理目录中的所有文档
        
        Returns:
            Tuple[成功处理的文档数, 总文档数]
        """
        return self._enhanced_processor.process_all_documents()
    
    def get_vectorstore(self):
        """获取向量数据库实例"""
        return self._enhanced_processor.get_vectorstore()
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            k: 返回的结果数量
            
        Returns:
            相关文档列表
        """
        return self._enhanced_processor.search_documents(query, k)
    
    # 向后兼容的方法名
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """向后兼容的PDF文本提取方法"""
        try:
            from document_processors.pdf_processor import PDFProcessor
            pdf_processor = PDFProcessor()
            return pdf_processor.extract_text(file_path)
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
            return ""
    
    def _get_document_hash(self, file_path: str) -> str:
        """向后兼容的文档哈希计算方法"""
        try:
            from document_processors.pdf_processor import PDFProcessor
            pdf_processor = PDFProcessor()
            return pdf_processor.get_document_hash(file_path)
        except Exception as e:
            logger.error(f"计算文档哈希失败: {e}")
            return ""


# 单例模式
_document_processor_instance = None

def get_document_processor() -> DocumentProcessor:
    """
    获取文档处理器单例实例
    
    Returns:
        DocumentProcessor实例
    """
    global _document_processor_instance
    if _document_processor_instance is None:
        _document_processor_instance = DocumentProcessor()
    return _document_processor_instance

# 测试代码
if __name__ == "__main__":
    processor = get_document_processor()
    success_count, total_count = processor.process_all_documents()
    print(f"成功处理了 {success_count}/{total_count} 个文档") 