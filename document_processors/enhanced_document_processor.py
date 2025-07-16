"""
增强的文档处理器
支持多种格式文档的智能处理和向量化
"""

import os
import logging
import glob
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from langchain_core.documents import Document

# 导入各种处理器
from .base_processor import BaseDocumentProcessor
from .pdf_processor import PDFProcessor
from .word_processor import WordProcessor
from .powerpoint_processor import PowerPointProcessor
from .excel_processor import ExcelProcessor
from .image_processor import ImageProcessor

# 向量数据库依赖
try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    class FAISS:
        @classmethod
        def from_documents(cls, *args, **kwargs):
            raise ImportError("无法导入FAISS向量数据库")
        @classmethod
        def load_local(cls, *args, **kwargs):
            raise ImportError("无法导入FAISS向量数据库")
        def save_local(self, *args, **kwargs):
            raise ImportError("无法导入FAISS向量数据库")

from langchain_openai import OpenAIEmbeddings

# 导入环境变量管理器
try:
    from env_manager import get_env_manager
    env_manager = get_env_manager()
except ImportError:
    env_manager = None
    print("警告: 环境变量管理器不可用，使用默认配置")

# 日志配置
logger = logging.getLogger(__name__)

class EnhancedDocumentProcessor:
    """增强的文档处理器，支持多种格式"""
    
    def __init__(self, documents_dir: str = None, vector_db_path: str = None):
        """
        初始化增强文档处理器
        
        Args:
            documents_dir: 文档目录，默认为 'images'
            vector_db_path: 向量数据库路径
        """
        # 设置目录路径
        self.documents_dir = documents_dir or 'images'
        
        # 使用环境变量或默认值
        if env_manager:
            self.vector_db_path = vector_db_path or env_manager.vector_db_path
            self.chunk_size = env_manager.chunk_size
            self.chunk_overlap = env_manager.chunk_overlap
        else:
            self.vector_db_path = vector_db_path or './vector_db'
            self.chunk_size = 1000
            self.chunk_overlap = 200
        
        # 创建向量数据库目录
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # 初始化所有处理器
        self.processors = [
            PDFProcessor(),
            WordProcessor(),
            PowerPointProcessor(),
            ExcelProcessor(),
            ImageProcessor()
        ]
        
        # 构建文件扩展名到处理器的映射
        self.extension_map = {}
        self.supported_extensions = set()
        
        for processor in self.processors:
            for ext in processor.get_supported_extensions():
                self.extension_map[ext] = processor
                self.supported_extensions.add(ext)
        
        logger.info(f"支持的文件格式: {', '.join(sorted(self.supported_extensions))}")
        
        # 初始化嵌入模型和向量数据库
        self.embeddings = self._init_embeddings()
        self.vectorstore = self._init_vectorstore()
        
        # 文档元数据缓存
        self.document_metadata = self._load_document_metadata()
    
    def _init_embeddings(self):
        """初始化嵌入模型"""
        try:
            if env_manager and env_manager.openai_api_key:
                logger.info("使用OpenAI嵌入模型")
                return OpenAIEmbeddings(openai_api_key=env_manager.openai_api_key)
            else:
                logger.warning("未配置OpenAI API Key，使用默认OpenAI嵌入模型")
                return OpenAIEmbeddings()
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")
            raise
    
    def _init_vectorstore(self):
        """初始化向量数据库"""
        try:
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            faiss_index_path = os.path.join(self.vector_db_path, "faiss_index")
            if os.path.exists(f"{faiss_index_path}.faiss"):
                logger.info(f"加载已有FAISS向量数据库: {faiss_index_path}")
                return FAISS.load_local(
                    folder_path=self.vector_db_path,
                    embeddings=self.embeddings,
                    index_name="faiss_index",
                    allow_dangerous_deserialization=True
                )
            else:
                logger.info("创建新的FAISS向量数据库")
                from langchain_core.documents import Document
                empty_docs = [Document(page_content="初始化文档", metadata={"source": "初始化"})]
                vectorstore = FAISS.from_documents(empty_docs, self.embeddings)
                vectorstore.save_local(self.vector_db_path, index_name="faiss_index")
                return vectorstore
                
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {e}")
            return None
    
    def _load_document_metadata(self) -> Dict[str, Dict[str, Any]]:
        """加载文档元数据"""
        metadata_path = os.path.join(self.vector_db_path, "document_metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载文档元数据失败: {e}")
                return {}
        
        return {}
    
    def _save_document_metadata(self) -> None:
        """保存文档元数据"""
        metadata_path = os.path.join(self.vector_db_path, "document_metadata.json")
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文档元数据失败: {e}")
    
    def _get_processor(self, file_path: str) -> Optional[BaseDocumentProcessor]:
        """根据文件路径获取对应的处理器"""
        file_ext = os.path.splitext(file_path)[1].lower()
        return self.extension_map.get(file_ext)
    
    def can_process(self, file_path: str) -> bool:
        """判断是否可以处理该文件"""
        processor = self._get_processor(file_path)
        return processor is not None and processor.validate_file(file_path)
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文件格式信息"""
        formats = {}
        for processor in self.processors:
            processor_name = processor.name.replace('Processor', '')
            formats[processor_name] = processor.get_supported_extensions()
        return formats
    
    def process_document(self, file_path: str) -> bool:
        """
        处理单个文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            处理是否成功
        """
        # 获取对应的处理器
        processor = self._get_processor(file_path)
        if not processor:
            logger.warning(f"不支持的文档类型: {file_path}")
            return False
        
        # 检查向量数据库是否可用
        if self.vectorstore is None:
            logger.error("向量数据库未初始化，无法处理文档")
            return False
        
        try:
            # 检查文档是否需要重新处理
            doc_hash = processor.get_document_hash(file_path)
            
            if file_path in self.document_metadata:
                if self.document_metadata[file_path].get("hash") == doc_hash:
                    logger.info(f"文档未更改，跳过处理: {file_path}")
                    return True
                else:
                    logger.info(f"文档已更改，重新处理: {file_path}")
            
            # 使用对应的处理器处理文档
            documents, result_info = processor.process_document(
                file_path, 
                chunk_size=self.chunk_size, 
                chunk_overlap=self.chunk_overlap
            )
            
            if not result_info.get('success', False):
                logger.error(f"文档处理失败: {file_path} - {result_info.get('error', '未知错误')}")
                return False
            
            if not documents:
                logger.warning(f"文档未提取到内容: {file_path}")
                return False
            
            # 添加到向量数据库
            logger.info(f"向量化并添加到数据库: {file_path} ({len(documents)} 个块)")
            self.vectorstore.add_documents(documents)
            self.vectorstore.save_local(self.vector_db_path, index_name="faiss_index")
            
            # 更新元数据
            self.document_metadata[file_path] = {
                **result_info.get('metadata', {}),
                'hash': doc_hash,
                'last_processed': datetime.now().isoformat(),
                'chunks': len(documents),
                'processor_used': processor.name,
                'success': True
            }
            
            self._save_document_metadata()
            
            logger.info(f"文档处理完成: {file_path} (使用 {processor.name})")
            return True
            
        except Exception as e:
            logger.error(f"处理文档时出错: {file_path} - {e}")
            return False
    
    def process_all_documents(self) -> Tuple[int, int]:
        """
        处理目录中的所有支持的文档
        
        Returns:
            Tuple[成功处理的文档数, 总文档数]
        """
        # 获取所有支持的文件
        all_files = []
        
        for ext in self.supported_extensions:
            pattern = os.path.join(self.documents_dir, "**", f"*{ext}")
            files = glob.glob(pattern, recursive=True)
            all_files.extend(files)
        
        success_count = 0
        total_count = len(all_files)
        
        logger.info(f"发现 {total_count} 个支持的文档")
        
        # 按格式分组统计
        format_stats = {}
        for file_path in all_files:
            ext = os.path.splitext(file_path)[1].lower()
            format_stats[ext] = format_stats.get(ext, 0) + 1
        
        logger.info(f"文档格式分布: {format_stats}")
        
        # 处理每个文档
        for file_path in all_files:
            try:
                if self.process_document(file_path):
                    success_count += 1
            except Exception as e:
                logger.error(f"处理文档异常: {file_path} - {e}")
        
        # 记录处理结果
        logger.info(f"文档处理完成。成功: {success_count}/{total_count}")
        
        # 按处理器统计成功率
        processor_stats = {}
        for file_path, metadata in self.document_metadata.items():
            if metadata.get('success', False):
                processor_name = metadata.get('processor_used', 'Unknown')
                processor_stats[processor_name] = processor_stats.get(processor_name, 0) + 1
        
        logger.info(f"处理器使用统计: {processor_stats}")
        
        return success_count, total_count
    
    def get_document_stats(self) -> Dict[str, Any]:
        """获取文档处理统计信息"""
        stats = {
            'total_documents': len(self.document_metadata),
            'supported_formats': list(self.supported_extensions),
            'processors_available': len(self.processors),
            'vector_db_available': self.vectorstore is not None
        }
        
        # 按格式统计
        format_counts = {}
        processor_counts = {}
        
        for file_path, metadata in self.document_metadata.items():
            if metadata.get('success', False):
                # 格式统计
                ext = os.path.splitext(file_path)[1].lower()
                format_counts[ext] = format_counts.get(ext, 0) + 1
                
                # 处理器统计
                processor = metadata.get('processor_used', 'Unknown')
                processor_counts[processor] = processor_counts.get(processor, 0) + 1
        
        stats.update({
            'documents_by_format': format_counts,
            'documents_by_processor': processor_counts
        })
        
        return stats
    
    def get_vectorstore(self):
        """获取向量数据库实例"""
        return self.vectorstore
    
    def is_initialized(self) -> bool:
        """
        检查文档处理器是否已完成初始化
        
        Returns:
            是否已完成初始化
        """
        return (
            self.vectorstore is not None and 
            self.embeddings is not None and 
            len(self.processors) > 0
        )
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            k: 返回的结果数量
            
        Returns:
            相关文档列表
        """
        if self.vectorstore is None:
            logger.error("向量数据库未初始化，无法搜索")
            return []
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"查询 '{query}' 返回 {len(docs)} 个结果")
            return docs
        except Exception as e:
            logger.error(f"搜索文档时出错: {e}")
            return []


# 单例模式
_enhanced_document_processor_instance = None

def get_enhanced_document_processor() -> EnhancedDocumentProcessor:
    """
    获取增强文档处理器单例实例
    
    Returns:
        EnhancedDocumentProcessor实例
    """
    global _enhanced_document_processor_instance
    if _enhanced_document_processor_instance is None:
        _enhanced_document_processor_instance = EnhancedDocumentProcessor()
    return _enhanced_document_processor_instance 