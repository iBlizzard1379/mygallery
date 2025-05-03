"""
文档处理模块
负责PDF文档的加载、文本提取、分块和向量化处理
"""

import os
import logging
import glob
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

# 文档处理依赖
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.documents import Document

# 向量数据库依赖
try:
    from langchain_community.vectorstores import Chroma, FAISS
except ImportError:
    # 如果无法导入，创建替代类
    class Chroma:
        @classmethod
        def from_documents(cls, *args, **kwargs):
            raise ImportError("无法导入Chroma向量数据库")
            
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
from langchain_community.embeddings import HuggingFaceEmbeddings

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

class DocumentProcessor:
    """
    文档处理器，负责PDF文档的加载、文本提取、分块和向量化处理
    """
    
    def __init__(self, documents_dir: str = None, vector_db_path: str = None):
        """
        初始化文档处理器
        
        Args:
            documents_dir: 文档目录，默认为 'images'
            vector_db_path: 向量数据库路径，默认从环境变量读取
        """
        # 设置目录路径
        self.documents_dir = documents_dir or 'images'
        
        # 使用环境变量或默认值设置向量数据库路径
        if env_manager:
            self.vector_db_path = vector_db_path or env_manager.vector_db_path
            self.chunk_size = env_manager.chunk_size
            self.chunk_overlap = env_manager.chunk_overlap
            self.vector_db_type = env_manager.vector_db
        else:
            self.vector_db_path = vector_db_path or './vector_db'
            self.chunk_size = 1000
            self.chunk_overlap = 200
            self.vector_db_type = 'chroma'
        
        # 创建向量数据库目录（如果不存在）
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # 初始化嵌入模型和分块器
        self.embeddings = self._init_embeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 初始化向量数据库
        self.vectorstore = self._init_vectorstore()
        
        # 文档元数据缓存
        self.document_metadata = self._load_document_metadata()
    
    def _init_embeddings(self):
        """
        初始化嵌入模型
        
        Returns:
            配置好的嵌入模型
        """
        try:
            # 尝试使用OpenAI的嵌入模型
            if env_manager and env_manager.openai_api_key:
                logger.info("使用OpenAI嵌入模型")
                return OpenAIEmbeddings(openai_api_key=env_manager.openai_api_key)
            
            # 如果没有OpenAI API Key，尝试使用HuggingFace的嵌入模型
            elif env_manager and env_manager.huggingface_api_key:
                logger.info("使用HuggingFace嵌入模型")
                return HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    huggingfacehub_api_token=env_manager.huggingface_api_key
                )
            
            # 如果都没有配置，使用OpenAI的嵌入模型（需要在环境变量中设置API Key）
            else:
                logger.warning("未配置API Key，使用OpenAI嵌入模型（需在环境中设置OPENAI_API_KEY）")
                return OpenAIEmbeddings()
        
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")
            raise
    
    def _init_vectorstore(self):
        """
        初始化向量数据库
        
        Returns:
            配置好的向量数据库
        """
        try:
            # 确保向量数据库目录存在
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # 根据配置选择向量数据库类型
            if self.vector_db_type.lower() == 'chroma':
                # 使用Chroma向量数据库
                if os.path.exists(self.vector_db_path) and any(os.scandir(self.vector_db_path)):
                    # 如果向量数据库已存在，加载它
                    logger.info(f"加载已有Chroma向量数据库: {self.vector_db_path}")
                    return Chroma(
                        persist_directory=self.vector_db_path,
                        embedding_function=self.embeddings
                    )
                else:
                    # 创建新的向量数据库
                    logger.info(f"创建新的Chroma向量数据库: {self.vector_db_path}")
                    return Chroma(
                        persist_directory=self.vector_db_path,
                        embedding_function=self.embeddings
                    )
            
            elif self.vector_db_type.lower() == 'faiss':
                # 使用FAISS向量数据库
                faiss_index_path = os.path.join(self.vector_db_path, "faiss_index")
                if os.path.exists(f"{faiss_index_path}.faiss"):
                    # 如果向量数据库已存在，加载它
                    logger.info(f"加载已有FAISS向量数据库: {faiss_index_path}")
                    return FAISS.load_local(
                        folder_path=self.vector_db_path,
                        embeddings=self.embeddings,
                        index_name="faiss_index",
                        allow_dangerous_deserialization=True
                    )
                else:
                    # 创建新的向量数据库（初始为空）
                    logger.info(f"创建新的FAISS向量数据库，将在添加文档后保存")
                    from langchain_core.documents import Document
                    empty_docs = [Document(page_content="初始化文档", metadata={"source": "初始化"})]
                    vectorstore = FAISS.from_documents(empty_docs, self.embeddings)
                    
                    # 保存向量数据库
                    vectorstore.save_local(self.vector_db_path, index_name="faiss_index")
                    return vectorstore
            
            else:
                # 默认使用Chroma
                logger.warning(f"未知向量数据库类型: {self.vector_db_type}，使用Chroma")
                return Chroma(
                    persist_directory=self.vector_db_path,
                    embedding_function=self.embeddings
                )
        
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {e}")
            # 在出现异常时，我们仍然返回None，以便能初始化对象，但后续要检查
            return None
    
    def _load_document_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        加载文档元数据（用于跟踪更新）
        
        Returns:
            文档元数据字典，键为文档路径，值为元数据字典
        """
        metadata_path = os.path.join(self.vector_db_path, "document_metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                import json
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
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文档元数据失败: {e}")
    
    def _get_document_hash(self, file_path: str) -> str:
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
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
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
                text += f"标题: {metadata.title or '未知'}\n"
                text += f"作者: {metadata.author or '未知'}\n"
                text += f"主题: {metadata.subject or '未知'}\n\n"
            
            # 提取每一页的文本
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"第 {i+1} 页:\n{page_text}\n\n"
            
            return text
        
        except Exception as e:
            logger.error(f"从PDF提取文本失败: {file_path} - {e}")
            return ""
    
    def process_document(self, file_path: str) -> bool:
        """
        处理单个文档，包括文本提取、分块和向量化
        
        Args:
            file_path: 文档路径
        
        Returns:
            处理是否成功
        """
        if not file_path.lower().endswith('.pdf'):
            logger.warning(f"不支持的文档类型: {file_path}")
            return False
        
        # 检查向量数据库是否成功初始化
        if self.vectorstore is None:
            logger.error("向量数据库未初始化，无法处理文档")
            return False
        
        try:
            # 计算文档哈希值
            doc_hash = self._get_document_hash(file_path)
            
            # 检查文档是否已处理且未更改
            if file_path in self.document_metadata:
                if self.document_metadata[file_path]["hash"] == doc_hash:
                    logger.info(f"文档未更改，跳过处理: {file_path}")
                    return True
                else:
                    logger.info(f"文档已更改，重新处理: {file_path}")
                    # 删除旧的向量（如果可能）
                    # 注意：这里只能标记为删除，实际删除由数据库实现决定
                    doc_id = self.document_metadata[file_path].get("id")
                    if doc_id and hasattr(self.vectorstore, 'delete'):
                        try:
                            self.vectorstore.delete([doc_id])
                        except:
                            pass
            
            # 提取文本
            logger.info(f"从文档提取文本: {file_path}")
            text = self._extract_text_from_pdf(file_path)
            
            if not text:
                logger.warning(f"文档未提取到文本: {file_path}")
                return False
            
            # 分块文本
            logger.info(f"分块文本: {file_path}")
            chunks = self.text_splitter.split_text(text)
            
            # 准备文档对象和元数据
            rel_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": rel_path,
                        "chunk": i,
                        "filename": os.path.basename(file_path),
                        "filepath": file_path,
                        "hash": doc_hash,
                        "processed_at": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            # 向量化并添加到向量数据库
            logger.info(f"向量化并添加到数据库: {file_path} ({len(documents)} 个块)")
            
            if self.vector_db_type.lower() == 'faiss':
                # FAISS需要不同的处理方式
                if not hasattr(self.vectorstore, 'docstore') or not self.vectorstore.docstore._dict:
                    # 如果FAISS是空的，直接从文档创建
                    self.vectorstore = FAISS.from_documents(documents, self.embeddings)
                    # 保存FAISS索引
                    self.vectorstore.save_local(self.vector_db_path, index_name="faiss_index")
                else:
                    # 如果FAISS已有数据，添加新文档
                    self.vectorstore.add_documents(documents)
                    # 保存更新后的索引
                    self.vectorstore.save_local(self.vector_db_path, index_name="faiss_index")
            else:
                # Chroma直接添加文档
                ids = self.vectorstore.add_documents(documents)
                # 持久化Chroma数据库
                if hasattr(self.vectorstore, 'persist'):
                    self.vectorstore.persist()
            
            # 更新文档元数据
            self.document_metadata[file_path] = {
                "hash": doc_hash,
                "last_processed": datetime.now().isoformat(),
                "chunks": len(chunks),
                "filesize": os.path.getsize(file_path),
                "filename": os.path.basename(file_path)
            }
            
            # 保存元数据
            self._save_document_metadata()
            
            logger.info(f"文档处理完成: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"处理文档时出错: {file_path} - {e}")
            return False
    
    def process_all_documents(self) -> Tuple[int, int]:
        """
        处理目录中的所有PDF文档
        
        Returns:
            Tuple[成功处理的文档数, 总文档数]
        """
        # 获取所有PDF文件
        pdf_pattern = os.path.join(self.documents_dir, "**", "*.pdf")
        pdf_files = glob.glob(pdf_pattern, recursive=True)
        
        success_count = 0
        total_count = len(pdf_files)
        
        logger.info(f"发现 {total_count} 个PDF文档")
        
        # 处理每个文档
        for file_path in pdf_files:
            if self.process_document(file_path):
                success_count += 1
        
        # 日志记录处理结果
        logger.info(f"文档处理完成。成功: {success_count}/{total_count}")
        
        return success_count, total_count
    
    def get_vectorstore(self):
        """
        获取向量数据库实例
        
        Returns:
            向量数据库实例
        """
        return self.vectorstore
    
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
            # 执行相似度搜索
            docs = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"查询 '{query}' 返回 {len(docs)} 个结果")
            return docs
        except Exception as e:
            logger.error(f"搜索文档时出错: {e}")
            return []

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