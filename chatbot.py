import os
import gradio as gr
from dotenv import load_dotenv
import threading
import time
import logging

# 导入自定义模块
try:
    from langchain_helper import create_chat_handler, get_available_models
    from document_processor import get_document_processor
    from file_watcher import get_file_watcher
    from rag_chain import get_rag_chain
    
    has_langchain = True
    has_document_processor = True
    has_file_watcher = True
    has_rag_chain = True
except ImportError as e:
    print(f"警告: 无法导入某些模块: {e}")
    has_langchain = 'langchain_helper' not in str(e)
    has_document_processor = 'document_processor' not in str(e)
    has_file_watcher = 'file_watcher' not in str(e)
    has_rag_chain = 'rag_chain' not in str(e)

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

# 加载环境变量
load_dotenv()

# 全局变量
gradio_app = None
gradio_thread = None
chat_handler = None
document_processor = None
file_watcher = None
rag_chain = None

def setup_components():
    """初始化组件"""
    global chat_handler, document_processor, file_watcher, rag_chain
    
    logger.info("开始初始化组件...")
    
    # 初始化聊天处理器
    if has_langchain:
        try:
            model_type = os.getenv("LLM_MODEL_TYPE", "openai")
            logger.info(f"正在创建聊天处理器，模型类型: {model_type}, API Key: {os.getenv('OPENAI_API_KEY')[:5]}***")
            chat_handler = create_chat_handler(model_type)
            logger.info(f"成功创建聊天处理器，使用模型类型: {model_type}")
        except Exception as e:
            logger.error(f"创建聊天处理器失败: {e}")
            chat_handler = None
    
    # 初始化文档处理器
    if has_document_processor:
        try:
            logger.info("正在创建文档处理器...")
            document_processor = get_document_processor()
            logger.info("成功创建文档处理器")
        except Exception as e:
            logger.error(f"创建文档处理器失败: {e}")
            document_processor = None
    
    # 初始化文件监听器
    if has_file_watcher and document_processor:
        try:
            logger.info("正在创建文件监听器...")
            file_watcher = get_file_watcher()
            logger.info("成功创建文件监听器")
            
            # 处理已存在的文档
            logger.info("处理已存在的文档...")
            file_watcher.process_existing_documents()
            
            # 启动文件监听
            logger.info("启动文件监听...")
            if file_watcher.start():
                logger.info("文件监听器已启动")
        except Exception as e:
            logger.error(f"创建或启动文件监听器失败: {e}")
            file_watcher = None
    
    # 初始化RAG链
    if has_rag_chain and document_processor:
        try:
            logger.info("正在创建RAG链...")
            rag_chain = get_rag_chain()
            logger.info("成功创建RAG链")
        except Exception as e:
            logger.error(f"创建RAG链失败: {e}")
            rag_chain = None
    
    # 返回组件状态
    return {
        "chat_handler": chat_handler is not None,
        "document_processor": document_processor is not None,
        "file_watcher": file_watcher is not None,
        "rag_chain": rag_chain is not None
    }

def create_chatbot_ui():
    """
    创建Gradio聊天界面
    """
    # 确保gradio可用
    try:
        import gradio as gr
    except ImportError:
        logger.error("无法导入gradio模块，请确保已安装")
        return None
        
    # 初始化组件
    components_status = setup_components()
    
    # 获取模型信息
    model_type = os.getenv("LLM_MODEL_TYPE", "openai")
    model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo") if model_type == "openai" else os.getenv("HUGGINGFACE_MODEL", "模型未设置")
    
    try:
        with gr.Blocks(
            title="画廊智能助手",
            css="""
            .gradio-container {background-color: transparent !important}
            .chat-message {margin-bottom: 10px; padding: 8px 12px; border-radius: 15px;}
            .user-message {background-color: #e1f5fe; align-self: flex-end;}
            .bot-message {background-color: #f5f5f5; align-self: flex-start;}
            #component-0 {min-height: 400px; height: 100%;}
            .footer {font-size: 0.85em; color: #666; text-align: center; margin-top: 5px;}
            .status-badge {display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-right: 5px;}
            .status-success {background-color: #e8f5e9; color: #2e7d32;}
            .status-error {background-color: #ffebee; color: #c62828;}
            .source-documents {font-size: 0.85em; color: #555; margin-top: 5px; padding: 5px; background-color: #f5f5f5; border-radius: 4px;}
            """
        ) as demo:
            # 状态变量
            chatbot = gr.State([])
            
            with gr.Column():
                # 组件状态显示
                status_html = ""
                if components_status["chat_handler"]:
                    status_html += "<span class='status-badge status-success'>LLM ✓</span>"
                else:
                    status_html += "<span class='status-badge status-error'>LLM ✗</span>"
                
                if components_status["document_processor"]:
                    status_html += "<span class='status-badge status-success'>文档处理 ✓</span>"
                else:
                    status_html += "<span class='status-badge status-error'>文档处理 ✗</span>"
                
                if components_status["rag_chain"]:
                    status_html += "<span class='status-badge status-success'>RAG ✓</span>"
                else:
                    status_html += "<span class='status-badge status-error'>RAG ✗</span>"
                
                # 显示模型信息和组件状态
                gr.Markdown(f"<div class='footer'>{status_html}<br>当前模型: {model_name}</div>")
                
                # 聊天历史显示区域
                chat_history = gr.Chatbot(
                    label="对话历史",
                    height=320,
                    show_copy_button=True,
                    avatar_images=(None, "🤖"),
                )
                
                # 输入区域
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="在此输入您的问题...",
                        container=False,
                        scale=9,
                    )
                    submit_btn = gr.Button("发送", scale=1)
                    clear_btn = gr.Button("清空", scale=1)
            
            # 定义回调函数
            def user_message(message, history):
                """处理用户消息"""
                return "", history + [[message, None]]
            
            def bot_response(history):
                """生成机器人响应"""
                if not history:
                    return history
                    
                message = history[-1][0]
                
                # 使用RAG链处理查询
                if has_rag_chain and rag_chain:
                    try:
                        # 使用RAG链执行查询
                        result = rag_chain.query(message)
                        response = result["answer"]
                        source_docs = result.get("source_documents", [])
                        
                        # 如果有引用源，添加到回答中
                        if source_docs:
                            source_info = "\n\n**参考来源:**\n"
                            for i, doc in enumerate(source_docs[:2]):
                                filename = doc.metadata.get('filename', '未知')
                                source_info += f"- {filename}\n"
                            
                            response += source_info
                        
                        history[-1][1] = response
                        
                    except Exception as e:
                        logger.error(f"RAG处理失败: {e}")
                        history[-1][1] = f"抱歉，无法使用知识库回答您的问题: {str(e)}"
                
                # 使用基础LLM处理
                elif has_langchain and chat_handler:
                    try:
                        response = chat_handler.chat(message)
                        history[-1][1] = response
                    except Exception as e:
                        logger.error(f"LLM处理失败: {e}")
                        history[-1][1] = f"抱歉，处理您的请求时出错: {str(e)}"
                
                # 回退方案：模拟响应
                else:
                    # 模拟响应
                    time.sleep(1)
                    history[-1][1] = f"您的消息已收到：{message}。这是一个模拟响应，请配置LLM或RAG系统以获取真实回答。"
                
                return history
            
            def clear_history():
                """清空聊天历史"""
                if has_rag_chain and rag_chain:
                    rag_chain.clear_history()
                elif has_langchain and chat_handler:
                    chat_handler.clear_history()
                return [], []
            
            # 设置事件触发
            submit_btn.click(
                user_message,
                inputs=[user_input, chat_history],
                outputs=[user_input, chat_history],
                queue=False
            ).then(
                bot_response,
                inputs=[chat_history],
                outputs=[chat_history]
            )
            
            user_input.submit(
                user_message,
                inputs=[user_input, chat_history],
                outputs=[user_input, chat_history],
                queue=False
            ).then(
                bot_response,
                inputs=[chat_history],
                outputs=[chat_history]
            )
            
            clear_btn.click(
                clear_history,
                outputs=[chat_history, chatbot]
            )
        
        return demo
    except Exception as e:
        logger.error(f"创建Gradio界面失败: {e}")
        return None

def start_gradio_server():
    """
    启动Gradio服务器
    """
    global gradio_app
    
    # 创建聊天机器人界面
    gradio_app = create_chatbot_ui()
    
    # 如果创建界面失败，则返回
    if gradio_app is None:
        logger.error("无法创建Gradio界面，服务器启动失败")
        return False
    
    # 获取Gradio端口
    gradio_port = int(os.getenv("GRADIO_PORT", 7860))
    
    # 启动服务器
    try:
        logger.info(f"正在启动Gradio服务器，端口: {gradio_port}")
        # 使用低并发配置，避免Gradio 4.x的队列问题
        try:
            # 仅在界面支持队列时使用队列
            gradio_app.queue(concurrency_count=1, max_size=10)
        except Exception as e:
            logger.warning(f"设置Gradio队列时出错: {e}")
            
        gradio_app.launch(
            server_name="0.0.0.0",  # 允许外部访问
            server_port=gradio_port,
            share=False,
            inbrowser=False,
            debug=False
        )
        logger.info(f"Gradio服务器已启动，端口: {gradio_port}")
        return True
    except Exception as e:
        logger.error(f"启动Gradio服务器失败: {e}")
        return False

def get_gradio_app():
    """获取或创建Gradio应用实例"""
    global gradio_app
    if gradio_app is None:
        gradio_app = create_chatbot_ui()
    return gradio_app

def start_background_gradio():
    """在后台启动Gradio"""
    global gradio_thread
    
    try:
        logger.info("开始启动后台Gradio服务...")
        
        # 检查线程是否已存在且活跃
        if gradio_thread is not None and gradio_thread.is_alive():
            logger.info("Gradio线程已经在运行中")
            return True

        # 检查API Key
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("未设置OpenAI API Key，Gradio可能无法正常工作")
        else:
            api_preview = api_key[:5] + "****" if len(api_key) > 5 else "有效但长度不足"
            logger.info(f"已检测到API Key: {api_preview}")
            
        # 创建新的线程
        logger.info("创建Gradio线程...")
        gradio_thread = threading.Thread(target=start_gradio_server)
        gradio_thread.daemon = True
        
        # 启动线程
        logger.info("启动Gradio线程...")
        gradio_thread.start()
        
        # 等待Gradio启动
        time.sleep(2)
        
        if gradio_thread.is_alive():
            logger.info("Gradio已在后台线程启动")
            return True
        else:
            logger.error("Gradio线程启动失败")
            return False
            
    except Exception as e:
        logger.error(f"启动后台Gradio服务失败: {str(e)}")
        return False

def cleanup():
    """清理资源"""
    global file_watcher
    
    # 停止文件监听器
    if file_watcher:
        try:
            file_watcher.stop()
            logger.info("文件监听器已停止")
        except Exception as e:
            logger.error(f"停止文件监听器失败: {e}")

if __name__ == "__main__":
    try:
        # 启动Gradio
        start_gradio_server()
        
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到终止信号，正在清理...")
        cleanup()
    except Exception as e:
        logger.error(f"运行时出错: {e}")
        cleanup() 