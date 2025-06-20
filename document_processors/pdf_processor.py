"""
PDF文档处理器
处理PDF格式文档的文本提取和元数据提取
"""

import logging
from typing import List, Dict, Any
from pypdf import PdfReader

from .base_processor import BaseDocumentProcessor

# 日志配置
logger = logging.getLogger(__name__)

class PDFProcessor(BaseDocumentProcessor):
    """PDF文档处理器"""
    
    def __init__(self):
        """初始化PDF处理器"""
        super().__init__()
    
    def can_process(self, file_path: str) -> bool:
        """判断是否可以处理PDF文件"""
        return file_path.lower().endswith('.pdf')
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.pdf']
    
    def extract_text(self, file_path: str) -> str:
        """
        从PDF文件中提取文本
        
        Args:
            file_path: PDF文件路径
        
        Returns:
            提取的文本内容
        """
        try:
            # 使用PyPDF提取文本
            reader = PdfReader(file_path)
            text = ""
            
            # 提取元数据
            metadata = reader.metadata
            if metadata:
                text += f"文档标题: {metadata.title or '未知'}\n"
                text += f"文档作者: {metadata.author or '未知'}\n"
                text += f"文档主题: {metadata.subject or '未知'}\n"
                if metadata.creator:
                    text += f"创建工具: {metadata.creator}\n"
                text += "\n" + "="*50 + "\n\n"
            
            # 提取每一页的文本
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"=== 第 {i+1} 页 ===\n{page_text.strip()}\n\n"
            
            return text
        
        except Exception as e:
            logger.error(f"从PDF提取文本失败: {file_path} - {e}")
            return ""
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取PDF文档元数据
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            PDF元数据字典
        """
        try:
            reader = PdfReader(file_path)
            metadata_dict = {
                'document_type': 'PDF',
                'total_pages': len(reader.pages)
            }
            
            # 提取PDF元数据
            if reader.metadata:
                pdf_meta = reader.metadata
                metadata_dict.update({
                    'title': pdf_meta.title or '',
                    'author': pdf_meta.author or '',
                    'subject': pdf_meta.subject or '',
                    'creator': pdf_meta.creator or '',
                    'producer': pdf_meta.producer or '',
                    'creation_date': str(pdf_meta.creation_date) if pdf_meta.creation_date else '',
                    'modification_date': str(pdf_meta.modification_date) if pdf_meta.modification_date else ''
                })
            
            # 分析页面特征
            if reader.pages:
                # 统计非空页面数
                non_empty_pages = 0
                total_text_length = 0
                
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        non_empty_pages += 1
                        total_text_length += len(page_text)
                
                metadata_dict.update({
                    'non_empty_pages': non_empty_pages,
                    'avg_text_per_page': total_text_length // max(non_empty_pages, 1),
                    'total_text_length': total_text_length
                })
            
            return metadata_dict
            
        except Exception as e:
            logger.error(f"提取PDF元数据失败: {file_path} - {e}")
            return {
                'document_type': 'PDF',
                'error': str(e)
            } 