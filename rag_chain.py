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
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.tools import tool
# 修正导入路径
from langchain_community.tools.tavily_search.tool import TavilySearchResults
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
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入自定义模块
try:
    from document_processor import get_document_processor
    from langchain_helper import create_chat_handler
    from env_manager import get_env_manager
    from search_tools import get_search_tool
    
    has_dependencies = True
    document_processor = get_document_processor()
    env_manager = get_env_manager()
    search_tool = get_search_tool()
except ImportError as e:
    print(f"警告: 无法导入必要的模块: {e}")
    has_dependencies = False
    document_processor = None
    env_manager = None
    search_tool = None

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
如果上下文中没有足够的信息回答问题，请使用搜索工具来获取最新信息。

上下文:
{context}

问题: {question}

回答:
"""

# 新的系统提示模板
SYSTEM_PROMPT = """你是画廊中的智能助手，能够回答关于PDF文档和互联网信息的问题。

**重要原则：始终优先使用本地文档数据库！**

工作流程：
1. **第一步：必须先使用document_search工具搜索本地文档数据库**
2. **第二步：如果本地文档中确实没有相关信息或信息不够完整，才考虑使用internet_search工具**

你有两个信息来源：
1. 本地文档数据库 - 包含已上传的PDF文档（优先使用）
2. 互联网搜索 - 获取最新网络信息（仅在本地文档无法回答时使用）

使用internet_search工具的条件（必须同时满足）：
- 已经使用document_search工具搜索过本地文档
- 本地文档中确实没有相关信息
- 用户问题涉及最新信息、实时数据、当前新闻等

回答时，请明确说明你的信息来源。
"""

# 工具调用代理模板 - 修复缺少的agent_scratchpad变量
AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

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
        
        # 初始化向量数据库
        if not self.vectorstore and document_processor:
            self.vectorstore = document_processor.get_vectorstore()
        
        # 初始化工具和代理
        self.tools = self._init_tools()
        self.agent_executor = self._init_agent()
        
        # 备用RAG链 (如果工具调用不可用)
        self.chain = self._init_chain()
    
    def _init_tools(self) -> List[Tool]:
        """初始化工具集合"""
        tools = []
        
        # 添加文档检索工具
        if self.vectorstore:
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            retriever_tool = create_retriever_tool(
                retriever=retriever,
                name="document_search",
                description="""【优先使用】搜索本地PDF文档库。这是主要的信息来源，包含所有已上传的PDF文档内容。
                对于任何问题，都应该首先使用此工具搜索本地文档数据库，包括但不限于：
                - 文档内容、概念解释
                - 技术规格、产品信息  
                - 历史信息、背景资料
                - 任何可能在文档中出现的信息
                务必优先使用此工具！"""
            )
            tools.append(retriever_tool)
        
        # 添加网络搜索工具
        try:
            # 获取API密钥
            tavily_api_key = os.getenv("TAVILY_API_KEY", "")
            if env_manager:
                tavily_api_key = env_manager.tavily_api_key or tavily_api_key
            
            if tavily_api_key:
                search_tool = TavilySearchResults(api_key=tavily_api_key)
                tools.append(
                    Tool(
                        name="internet_search",
                        func=search_tool.invoke,
                        description="""【备用工具】搜索互联网获取最新信息。
                        ⚠️ 使用前提：必须先使用document_search工具搜索本地文档，且确认本地文档无相关信息！
                        
                        仅在以下情况使用：
                        - 已经使用document_search搜索过本地文档
                        - 本地文档确实没有相关信息
                        - 问题涉及最新信息：当前新闻、实时数据、市场趋势等
                        
                        绝不可直接使用此工具，必须先搜索本地文档！""",
                        return_direct=False
                    )
                )
                logger.info("成功创建Tavily搜索工具")
            else:
                logger.warning("未配置Tavily API Key，无法创建互联网搜索工具")
        except Exception as e:
            logger.error(f"创建Tavily搜索工具失败: {e}")
        
        return tools
    
    def _init_agent(self) -> Optional[AgentExecutor]:
        """初始化代理执行器"""
        if not self.llm:
            logger.error("LLM未初始化，无法创建代理")
            return None
        
        if not self.tools:
            logger.error("没有可用工具，无法创建代理")
            return None
        
        try:
            # 创建代理
            agent = create_tool_calling_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=AGENT_PROMPT
            )
            
            # 创建代理执行器
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info("成功创建工具调用代理")
            return agent_executor
        except Exception as e:
            logger.error(f"创建代理执行器失败: {e}")
            return None
    
    def _init_chain(self) -> Optional[ConversationalRetrievalChain]:
        """
        初始化传统RAG链 (作为备用)
        
        Returns:
            RAG链实例
        """
        if not self.llm:
            logger.error("LLM未初始化，无法创建RAG链")
            return None
        
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
            
            logger.info("备用RAG链初始化成功")
            return chain
        
        except Exception as e:
            logger.error(f"初始化备用RAG链失败: {e}")
            return None
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        执行查询，严格按照优先级：先本地文档，后互联网搜索
        
        Args:
            query: 查询文本
        
        Returns:
            包含回答和相关文档的字典
        """
        logger.info(f"收到查询: {query}")
        
        # 使用代理执行器处理查询
        if self.agent_executor:
            try:
                logger.info("使用工具调用代理处理查询，优先本地文档检索")
                # 构建带有历史的输入，并强调必须先搜索本地文档
                history_str = ""
                if self.chat_history:
                    for i in range(0, len(self.chat_history) - 1, 2):
                        if i + 1 < len(self.chat_history):
                            human_msg = self.chat_history[i]
                            ai_msg = self.chat_history[i + 1]
                            
                            if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                                history_str += f"用户: {human_msg.content}\n助手: {ai_msg.content}\n\n"
                
                # 修改输入格式，强调优先级
                enhanced_input = f"""聊天历史:
{history_str}

用户问题: {query}

请注意：必须首先使用document_search工具搜索本地文档数据库！只有在本地文档确实没有相关信息时，才可以考虑使用internet_search工具。"""
                
                # 执行代理
                result = self.agent_executor.invoke({"input": enhanced_input})
                response = result.get("output", "")
                
                # 更新聊天历史
                self.chat_history.append(HumanMessage(content=query))
                self.chat_history.append(AIMessage(content=response))
                
                # 构建结果对象 (与传统RAG结果格式保持一致)
                source_docs = []
                search_type = "agent"
                
                # 分析工具使用情况
                intermediate_steps = result.get("intermediate_steps", [])
                used_document_search = False
                used_internet_search = False
                
                for step in intermediate_steps:
                    if len(step) >= 2:
                        action, output = step[0], step[1]
                        # 检查action对象的工具名称
                        tool_name = getattr(action, 'tool', '') or getattr(action, 'name', '')
                        
                        if tool_name == "document_search":
                            used_document_search = True
                            if isinstance(output, list):
                                source_docs.extend(output)
                            elif isinstance(output, str) and "第" in output and "页" in output:
                                # 如果输出是文档内容字符串，创建Document对象
                                from langchain_core.documents import Document
                                doc = Document(page_content=output, metadata={"source": "document_search"})
                                source_docs.append(doc)
                        elif tool_name == "internet_search":
                            used_internet_search = True
                
                # 记录工具使用情况
                if used_document_search and used_internet_search:
                    search_type = "document+internet"
                    logger.info("使用了本地文档检索和互联网搜索")
                elif used_document_search:
                    search_type = "document_only"
                    logger.info("仅使用了本地文档检索")
                elif used_internet_search:
                    search_type = "internet_only"
                    logger.warning("⚠️ 仅使用了互联网搜索，未优先检索本地文档")
                
                return {
                    "answer": response,
                    "source_documents": source_docs,
                    "success": True,
                    "search_type": search_type,
                    "used_document_search": used_document_search,
                    "used_internet_search": used_internet_search
                }
                
            except Exception as e:
                logger.error(f"代理执行器处理查询失败: {e}")
                # 回退到传统RAG链
                logger.info("回退到传统RAG链处理查询")
                return self._rag_query(query)
        
        # 如果代理执行器不可用，使用传统RAG链
        logger.info("使用传统RAG链处理查询（代理执行器不可用）")
        return self._rag_query(query)
    
    def _rag_query(self, query: str) -> Dict[str, Any]:
        """
        使用传统RAG链执行查询 (备用方法)
        
        Args:
            query: 用户查询
        
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
                "success": True,
                "search_type": "rag"
            }
            
        except Exception as e:
            error_msg = f"执行RAG查询时出错: {e}"
            logger.error(error_msg)
            return {
                "answer": f"抱歉，处理您的问题时出错: {str(e)}",
                "source_documents": [],
                "success": False
            }
    
    def _format_chat_history(self) -> List[Tuple[str, str]]:
        """
        格式化聊天历史
        
        Returns:
            元组列表，每个元组包含一个用户消息和对应的AI回复
        """
        formatted_history = []
        
        # 必须成对出现，一个人类消息对应一个AI消息
        for i in range(0, len(self.chat_history) - 1, 2):
            if i + 1 < len(self.chat_history):
                human_msg = self.chat_history[i]
                ai_msg = self.chat_history[i + 1]
                
                if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                    formatted_history.append((human_msg.content, ai_msg.content))
        
        return formatted_history
    
    def add_message(self, message: Union[str, BaseMessage], role: str = "human") -> None:
        """
        添加消息到聊天历史
        
        Args:
            message: 消息内容
            role: 消息角色 ('human' 或 'ai')
        """
        if isinstance(message, BaseMessage):
            self.chat_history.append(message)
        else:
            if role.lower() == "human":
                self.chat_history.append(HumanMessage(content=message))
            elif role.lower() == "ai":
                self.chat_history.append(AIMessage(content=message))
            else:
                logger.warning(f"未知角色: {role}，使用'human'")
                self.chat_history.append(HumanMessage(content=message))
    
    def clear_history(self) -> None:
        """清空聊天历史"""
        self.chat_history = []
        logger.info("已清空聊天历史")
    
    def get_chat_history(self) -> List[BaseMessage]:
        """获取聊天历史"""
        return self.chat_history
    
    def get_formatted_history(self) -> List[Dict[str, str]]:
        """
        获取格式化的聊天历史
        
        Returns:
            字典列表，每个字典包含角色和内容
        """
        formatted = []
        
        for message in self.chat_history:
            if isinstance(message, HumanMessage):
                formatted.append({
                    "role": "user",
                    "content": message.content
                })
            elif isinstance(message, AIMessage):
                formatted.append({
                    "role": "assistant",
                    "content": message.content
                })
            elif isinstance(message, SystemMessage):
                formatted.append({
                    "role": "system",
                    "content": message.content
                })
            else:
                formatted.append({
                    "role": "unknown",
                    "content": str(message)
                })
        
        return formatted

# 单例模式
_rag_chain_instance = None

def get_rag_chain() -> RAGChain:
    """
    获取RAG链实例
    
    Returns:
        RAG链实例
    """
    global _rag_chain_instance
    if _rag_chain_instance is None:
        _rag_chain_instance = RAGChain()
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