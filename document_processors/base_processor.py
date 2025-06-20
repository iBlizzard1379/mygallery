"""
文档处理器基类
定义所有文档处理器的通用接口
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import hashlib

from langchain_core.documents import Document

# 日志配置
logger = logging.getLogger(__name__)

class BaseDocumentProcessor(ABC):
    """文档处理器基类"""
    
    def __init__(self):
        """初始化基础处理器"""
        self.name = self.__class__.__name__
        logger.debug(f"初始化 {self.name}")
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """
        判断是否可以处理该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否可以处理
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        提取文档文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本内容
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取文档元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档元数据字典
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            支持的文件扩展名列表
        """
        pass
    
    def get_document_hash(self, file_path: str) -> str:
        """
        计算文档的哈希值（用于检测更改）
        
        Args:
            file_path: 文档路径
        
        Returns:
            文档的MD5哈希值
        """
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                # 读取文件的前10KB用于计算哈希值（对大文件足够，且更快）
                data = f.read(10240)
                hasher.update(data)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"计算文档哈希值失败: {file_path} - {e}")
            # 如果计算失败，返回一个基于当前时间的唯一字符串
            return f"error-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件基本信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件基本信息字典
        """
        try:
            stat = os.stat(file_path)
            return {
                'filename': os.path.basename(file_path),
                'filepath': file_path,
                'filesize': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'processor': self.name
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path} - {e}")
            return {
                'filename': os.path.basename(file_path),
                'filepath': file_path,
                'filesize': 0,
                'modified_time': datetime.now().isoformat(),
                'processor': self.name,
                'error': str(e)
            }
    
    def process_document(self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Tuple[List[Document], Dict[str, Any]]:
        """
        处理文档的完整流程
        
        Args:
            file_path: 文件路径
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            
        Returns:
            Tuple[文档块列表, 处理结果信息]
        """
        if not self.can_process(file_path):
            return [], {'success': False, 'error': f'{self.name} 无法处理该文件类型'}
        
        try:
            # 提取文本
            logger.info(f"{self.name} 开始处理文档: {file_path}")
            text = self.extract_text(file_path)
            
            if not text:
                logger.warning(f"{self.name} 未提取到文本: {file_path}")
                return [], {'success': False, 'error': '未提取到文本内容'}
            
            # 提取元数据
            metadata = self.extract_metadata(file_path)
            file_stats = self.get_file_stats(file_path)
            
            # 合并元数据
            combined_metadata = {**metadata, **file_stats}
            combined_metadata['hash'] = self.get_document_hash(file_path)
            combined_metadata['processed_at'] = datetime.now().isoformat()
            
            # 分块文本
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_text(text)
            
            # 创建文档对象
            documents = []
            rel_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
            
            for i, chunk in enumerate(chunks):
                doc_metadata = combined_metadata.copy()
                doc_metadata['chunk'] = i
                doc_metadata['source'] = rel_path
                
                doc = Document(
                    page_content=chunk,
                    metadata=doc_metadata
                )
                documents.append(doc)
            
            result_info = {
                'success': True,
                'processor': self.name,
                'chunks': len(chunks),
                'text_length': len(text),
                'metadata': combined_metadata
            }
            
            logger.info(f"{self.name} 处理完成: {file_path} ({len(documents)} 个块)")
            return documents, result_info
            
        except Exception as e:
            logger.error(f"{self.name} 处理文档失败: {file_path} - {e}")
            return [], {'success': False, 'error': str(e), 'processor': self.name}
    
    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否有效
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False
            
            # 检查文件大小
            if os.path.getsize(file_path) == 0:
                return False
            
            # 检查文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.get_supported_extensions():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证文件失败: {file_path} - {e}")
            return False 