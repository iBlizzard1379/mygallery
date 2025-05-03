"""
RAG链模块
整合文档检索和聊天功能，实现基于检索的问答
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

# LangChain导入
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
# 修改导入方式，避免vectorstores.base导入错误
try:
    from langchain_community.vectorstores.base import VectorStore
except ImportError:
    # 定义一个替代基类
    from typing import Protocol, runtime_checkable
    
    @runtime_checkable
    class VectorStore(Protocol):
        """用于替代向量存储的协议类"""
        def as_retriever(self, **kwargs):
            """获取检索器"""
            ...
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

# 导入自定义模块
try:
    from document_processor import get_document_processor
    from langchain_helper import create_chat_handler
    from env_manager import get_env_manager
    
    has_dependencies = True
    document_processor = get_document_processor()
    env_manager = get_env_manager()
except ImportError as e:
    print(f"警告: 无法导入必要的模块: {e}")
    has_dependencies = False
    document_processor = None
    env_manager = None

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 默认提示模板
DEFAULT_CONDENSE_QUESTION_TEMPLATE = """
根据对话历史和最新问题，生成一个独立的问题。

对话历史:
{chat_history}

最新问题: {question}

独立问题:
"""

DEFAULT_QA_TEMPLATE = """
你是画廊中的智能助手，能够回答关于PDF文档的问题。请基于以下上下文回答问题。
如果上下文中没有足够的信息回答问题，请明确说明你不知道，不要编造答案。

上下文:
{context}

问题: {question}

回答:
"""

class RAGChain:
    """
    RAG链，整合文档检索和聊天功能
    """
    
    def __init__(self, vectorstore: Optional[VectorStore] = None, model_type: str = "openai"):
        """
        初始化RAG链
        
        Args:
            vectorstore: 向量数据库实例
            model_type: 使用的模型类型 ("openai" 或 "huggingface")
        """
        # 设置向量数据库
        self.vectorstore = vectorstore
        
        # 模型类型
        if env_manager and env_manager.model_type:
            self.model_type = env_manager.model_type
        else:
            self.model_type = model_type
        
        # 初始化聊天处理器
        try:
            self.chat_handler = create_chat_handler(self.model_type)
            self.llm = self.chat_handler.llm
            logger.info(f"已初始化聊天处理器，使用模型类型: {self.model_type}")
        except Exception as e:
            self.chat_handler = None
            self.llm = None
            logger.error(f"初始化聊天处理器失败: {e}")
        
        # 对话历史
        self.chat_history = []
        
        # 提示模板
        self.condense_question_prompt = PromptTemplate.from_template(
            DEFAULT_CONDENSE_QUESTION_TEMPLATE
        )
        self.qa_prompt = PromptTemplate.from_template(
            DEFAULT_QA_TEMPLATE
        )
        
        # 初始化RAG链
        self.chain = self._init_chain()
    
    def _init_chain(self) -> Optional[ConversationalRetrievalChain]:
        """
        初始化RAG链
        
        Returns:
            RAG链实例
        """
        if not self.llm:
            logger.error("LLM未初始化，无法创建RAG链")
            return None
        
        if not self.vectorstore:
            # 尝试从文档处理器获取向量数据库
            if document_processor:
                self.vectorstore = document_processor.get_vectorstore()
            
            if not self.vectorstore:
                logger.error("向量数据库未初始化，无法创建RAG链")
                return None
        
        try:
            # 创建检索器
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            # 创建RAG链
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                condense_question_prompt=self.condense_question_prompt,
                combine_docs_chain_kwargs={"prompt": self.qa_prompt},
                return_source_documents=True
            )
            
            logger.info("RAG链初始化成功")
            return chain
        
        except Exception as e:
            logger.error(f"初始化RAG链失败: {e}")
            return None
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        执行查询
        
        Args:
            query: 查询文本
        
        Returns:
            包含回答和相关文档的字典
        """
        if not self.chain:
            error_msg = "RAG链未初始化，无法执行查询"
            logger.error(error_msg)
            return {
                "answer": f"抱歉，{error_msg}",
                "source_documents": [],
                "success": False
            }
        
        try:
            # 准备聊天历史
            formatted_history = self._format_chat_history()
            
            # 执行查询
            result = self.chain({"question": query, "chat_history": formatted_history})
            
            # 更新聊天历史
            self.chat_history.append(HumanMessage(content=query))
            self.chat_history.append(AIMessage(content=result["answer"]))
            
            # 返回结果
            return {
                "answer": result["answer"],
                "source_documents": result.get("source_documents", []),
                "success": True
            }
            
        except Exception as e:
            error_msg = f"执行查询时出错: {e}"
            logger.error(error_msg)
            return {
                "answer": f"抱歉，处理您的请求时出现问题: {str(e)}",
                "source_documents": [],
                "success": False
            }
    
    def _format_chat_history(self) -> List[Tuple[str, str]]:
        """
        格式化聊天历史，用于RAG链
        
        Returns:
            聊天历史列表，格式为 [(human_message, ai_message), ...]
        """
        formatted_history = []
        
        # 成对获取历史消息（人类+AI）
        for i in range(0, len(self.chat_history) - 1, 2):
            if i + 1 < len(self.chat_history):
                if isinstance(self.chat_history[i], HumanMessage) and \
                   isinstance(self.chat_history[i+1], AIMessage):
                    human_msg = self.chat_history[i].content
                    ai_msg = self.chat_history[i+1].content
                    formatted_history.append((human_msg, ai_msg))
        
        return formatted_history
    
    def add_message(self, message: Union[str, BaseMessage], role: str = "human") -> None:
        """
        添加消息到历史
        
        Args:
            message: 消息内容或消息对象
            role: 角色 ("human", "ai", "system")
        """
        if isinstance(message, BaseMessage):
            self.chat_history.append(message)
        else:
            if role.lower() == "human":
                self.chat_history.append(HumanMessage(content=message))
            elif role.lower() == "ai":
                self.chat_history.append(AIMessage(content=message))
            elif role.lower() == "system":
                self.chat_history.append(SystemMessage(content=message))
    
    def clear_history(self) -> None:
        """清空聊天历史"""
        self.chat_history = []
    
    def get_chat_history(self) -> List[BaseMessage]:
        """
        获取聊天历史
        
        Returns:
            聊天历史消息列表
        """
        return self.chat_history
    
    def get_formatted_history(self) -> List[Dict[str, str]]:
        """
        获取格式化的聊天历史
        
        Returns:
            聊天历史列表，格式为 [{"role": "human", "content": "..."}, {"role": "ai", "content": "..."}]
        """
        formatted_history = []
        
        for message in self.chat_history:
            if isinstance(message, HumanMessage):
                formatted_history.append({"role": "human", "content": message.content})
            elif isinstance(message, AIMessage):
                formatted_history.append({"role": "ai", "content": message.content})
            elif isinstance(message, SystemMessage):
                formatted_history.append({"role": "system", "content": message.content})
        
        return formatted_history

# 单例模式
_rag_chain_instance = None

def get_rag_chain() -> RAGChain:
    """
    获取RAG链单例实例
    
    Returns:
        RAGChain实例
    """
    global _rag_chain_instance
    if _rag_chain_instance is None:
        # 尝试获取向量数据库
        vectorstore = None
        if document_processor:
            vectorstore = document_processor.get_vectorstore()
        
        # 创建RAG链实例
        _rag_chain_instance = RAGChain(vectorstore=vectorstore)
    
    return _rag_chain_instance

# 测试代码
if __name__ == "__main__":
    rag_chain = get_rag_chain()
    
    # 确保文档已处理
    if document_processor:
        document_processor.process_all_documents()
    
    # 测试查询
    query = "PDF文档主要讲了什么内容？"
    print(f"查询: {query}")
    result = rag_chain.query(query)
    
    # 打印结果
    print("\n回答:")
    print(result["answer"])
    
    if result["source_documents"]:
        print("\n参考来源:")
        for i, doc in enumerate(result["source_documents"][:2]):
            print(f"------- 文档 {i+1} -------")
            print(f"来源: {doc.metadata.get('filename', '未知')}")
            print(f"内容: {doc.page_content[:150]}...") 