#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画廊服务器 - 纯OpenAI版本
只使用直接OpenAI API，不使用任何fallback处理器
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
import logging
import socketserver
import threading
import io
import urllib.parse
import importlib.util
import sys
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入直接聊天模块
try:
    import direct_chatbot
    logger.info("已导入direct_chatbot模块")
    direct_chat_handler = direct_chatbot.get_chat_handler()
    if direct_chat_handler:
        logger.info("成功获取direct_chat_handler")
    else:
        logger.warning("direct_chat_handler不可用")
except ImportError as e:
    logger.error(f"无法导入direct_chatbot模块: {e}")
    direct_chat_handler = None

# 尝试导入chatbot模块
try:
    import chatbot
    logger.info("已导入chatbot模块")
except ImportError as e:
    logger.error(f"无法导入chatbot模块: {e}")
    chatbot = None

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """处理请求的线程化版本的HTTP服务器"""
    daemon_threads = True

class GalleryHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # 规范化路径以处理各种URL编码问题
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        logger.info(f"处理GET请求: {path}")
        
        # 处理根目录请求
        if path == '/':
            try:
                # 获取index.html的路径
                index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
                if not os.path.exists(index_path):
                    logger.error(f"index.html not found: {index_path}")
                    self.send_error(404, "index.html not found")
                    return
                
                # 读取并发送index.html
                with open(index_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                logger.info("成功返回index.html")
                return
                
            except Exception as e:
                logger.error(f"处理根目录请求时出错: {str(e)}")
                self.send_error(500, str(e))
                return
        
        # 处理chatbot请求 - 直接内嵌聊天界面
        elif path == '/chatbot':
            try:
                logger.info("提供聊天界面")
                
                # 检查API密钥
                api_key = os.environ.get("OPENAI_API_KEY", "")
                api_key_preview = api_key[:5] + "****" if len(api_key) > 5 else "未设置" 
                logger.info(f"当前API Key: {api_key_preview}")
                
                # 返回一个简单的HTML页面
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>画廊AI助手</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }}
        .chatbox {{
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
        }}
        .messages {{
            flex-grow: 1;
            overflow-y: auto;
            padding: 15px;
            background-color: rgba(0, 0, 0, 0.7);
        }}
        .input-area {{
            display: flex;
            padding: 8px;
            background-color: rgba(0, 0, 0, 0.8);
            border-top: 1px solid #333;
        }}
        #user-input {{
            flex-grow: 1;
            padding: 8px;
            border: 1px solid #444;
            border-radius: 4px;
            font-size: 13px;
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
        }}
        button {{
            margin-left: 8px;
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }}
        .message {{
            margin-bottom: 8px;
            padding: 8px;
            border-radius: 4px;
            max-width: 85%;
            font-size: 13px;
            word-wrap: break-word;
        }}
        .user-message {{
            background-color: #2b5278;
            align-self: flex-end;
            margin-left: auto;
            color: white;
        }}
        .bot-message {{
            background-color: #333;
            align-self: flex-start;
            color: white;
        }}
        .status {{
            padding: 4px 8px;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 0.85em;
            background-color: rgba(0, 0, 0, 0.5);
            color: #4CAF50;
        }}
        .status-info {{
            background-color: rgba(0, 0, 0, 0.5);
            color: #4CAF50;
        }}
    </style>
</head>
<body>
    <div class="chatbox">
        <div class="messages" id="chat-messages">
            <div class="status status-info">画廊AI助手已就绪，可以回答您的问题</div>
            <div class="message bot-message">您好！我是画廊智能助手，请问有什么可以帮助您的？</div>
        </div>
        <div class="input-area">
            <input type="text" id="user-input" placeholder="在此输入您的问题...">
            <button id="send-btn">发送</button>
        </div>
    </div>

    <script>
        document.getElementById('send-btn').addEventListener('click', function() {{
            sendMessage();
        }});
        
        document.getElementById('user-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
        
        function sendMessage() {{
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            
            if (message) {{
                // 显示用户消息
                addMessage(message, 'user');
                input.value = '';
                
                // 显示正在输入
                const typingIndicator = addMessage('正在思考...', 'bot');
                
                // 发送到后端
                fetch('/chatbot-api', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ message: message }}),
                }})
                .then(response => response.json())
                .then(data => {{
                    // 移除输入指示器
                    typingIndicator.remove();
                    
                    // 显示机器人回复
                    addMessage(data.response, 'bot');
                }})
                .catch(error => {{
                    // 移除输入指示器
                    typingIndicator.remove();
                    
                    // 显示错误
                    addMessage('抱歉，发生了错误，请稍后再试。', 'bot');
                    console.error('Error:', error);
                }});
            }}
        }}
        
        function addMessage(text, sender) {{
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            
            // 滚动到底部
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageDiv;
        }}
    </script>
</body>
</html>"""
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
                logger.info("成功返回聊天界面HTML")
                return
                
            except Exception as e:
                logger.error(f"处理Chatbot请求时出错: {str(e)}")
                self.send_error(500, str(e))
                return
        
        # 处理/images和/images/请求
        elif path in ['/images', '/images/']:
            try:
                # 获取images目录的绝对路径
                images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
                logger.info(f"正在访问目录: {images_dir}")
                
                # 检查目录是否存在
                if not os.path.exists(images_dir):
                    logger.error(f"目录不存在: {images_dir}")
                    self.send_error(404, "Images directory not found")
                    return
                
                # 获取文件列表
                files = os.listdir(images_dir)
                logger.info(f"找到文件: {files}")
                
                # 分类文件
                images = []
                documents = []
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        images.append(file)
                    elif file.lower().endswith('.pdf'):
                        documents.append(file)
                
                # 准备响应
                response = {
                    'images': images,
                    'documents': documents
                }
                
                # 设置响应头
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                
                # 发送响应
                self.wfile.write(json.dumps(response).encode('utf-8'))
                logger.info(f"成功返回文件列表: {response}")
                return
                
            except Exception as e:
                logger.error(f"处理请求时出错: {str(e)}")
                self.send_error(500, str(e))
                return
        else:
            # 处理其他请求
            try:
                # 获取请求的文件路径
                path = self.translate_path(self.path)
                
                # 如果是目录，返回404
                if os.path.isdir(path):
                    self.send_error(404, "Directory not supported")
                    return
                
                # 处理文件请求
                super().do_GET()
            except Exception as e:
                logger.error(f"处理文件请求时出错: {str(e)}")
                self.send_error(500, str(e))

    def do_OPTIONS(self):
        """处理OPTIONS请求，支持CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # 规范化路径以处理各种URL编码问题
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        logger.info(f"处理POST请求: {path}")
        
        # 处理聊天API请求
        if path == '/chatbot-api':
            try:
                # 获取请求内容长度
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # 解析JSON数据，确保使用UTF-8编码
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except UnicodeDecodeError:
                    # 尝试其他编码
                    try:
                        data = json.loads(post_data.decode('latin-1'))
                    except:
                        data = {"message": "解码错误"}
                        logger.error("无法解码POST数据")
                
                # 获取消息，确保是字符串
                message = data.get('message', '')
                if not isinstance(message, str):
                    message = str(message)
                
                logger.info(f"收到聊天信息: {message}")
                
                # 检查处理器可用性
                direct_chat_available = direct_chat_handler is not None
                chatbot_available = chatbot and hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None
                rag_chain_available = False
                
                # 检查是否有rag_chain可用
                try:
                    from rag_chain import get_rag_chain
                    rag_chain = get_rag_chain()
                    rag_chain_available = rag_chain is not None
                    logger.info(f"RAG链可用: {rag_chain_available}")
                except Exception as e:
                    logger.error(f"无法导入或初始化RAG链: {e}")
                    rag_chain_available = False
                
                logger.info(f"direct_chat可用: {direct_chat_available}, chatbot可用: {chatbot_available}, RAG链可用: {rag_chain_available}")
                
                # 优先使用RAG链（自动决定是否使用搜索工具）
                if rag_chain_available:
                    try:
                        logger.info("使用RAG链处理查询")
                        result = rag_chain.query(message)
                        response = result.get("answer", "")
                        logger.info(f"RAG链回复: {response[:50]}...")
                    except Exception as e:
                        logger.error(f"RAG链处理错误: {e}")
                        # 回退到直接处理器
                        if direct_chat_available:
                            logger.info("RAG链失败，尝试使用direct_chat_handler处理器")
                            try:
                                response = direct_chat_handler.chat(message)
                                logger.info(f"回复: {response[:50]}...")
                            except Exception as e2:
                                logger.error(f"direct_chat_handler错误: {e2}")
                                response = f"抱歉，无法处理您的请求: {str(e2)}"
                        else:
                            response = f"抱歉，无法处理您的请求: {str(e)}"
                # 使用直接OpenAI处理器
                elif direct_chat_available:
                    try:
                        logger.info("使用direct_chat_handler处理器")
                        response = direct_chat_handler.chat(message)
                        logger.info(f"回复: {response[:50]}...")
                    except Exception as e:
                        logger.error(f"direct_chat_handler错误: {e}")
                        # 回退到chatbot处理器
                        if chatbot_available:
                            logger.info("direct_chat失败，尝试使用chatbot处理器")
                            try:
                                response = chatbot.chat_handler.chat(message)
                                logger.info(f"回复: {response[:50]}...")
                            except Exception as e2:
                                logger.error(f"chatbot处理器错误: {e2}")
                                response = f"抱歉，无法连接到OpenAI API: {str(e2)}"
                        else:
                            response = f"抱歉，无法连接到OpenAI API: {str(e)}"
                # 其次尝试使用chatbot
                elif chatbot_available:
                    try:
                        logger.info(f"使用chatbot处理器: {type(chatbot.chat_handler).__name__}")
                        response = chatbot.chat_handler.chat(message)
                        logger.info(f"回复: {response[:50]}...")
                    except Exception as e:
                        logger.error(f"chatbot处理器错误: {e}")
                        response = f"抱歉，无法连接到OpenAI API: {str(e)}"
                # 无可用处理器
                else:
                    response = f"抱歉，当前没有可用的AI处理器来处理您的消息：{message}。请联系管理员配置OpenAI API。"
                    logger.warning("所有聊天处理器不可用")
                
                # 准备响应
                response_data = {
                    'response': response,
                    'success': True
                }
                
                # 发送响应
                response_json = json.dumps(response_data, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_json)))
                self.end_headers()
                self.wfile.write(response_json)
                return
                
            except Exception as e:
                logger.error(f"处理聊天API请求时出错: {str(e)}")
                # 发送错误响应
                error_response = json.dumps({
                    'error': str(e),
                    'success': False
                }).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response)
                return
        else:
            # 其他POST请求暂不支持
            self.send_error(405, "Method not allowed")
            return

def ensure_chatbot_module():
    """确保chatbot模块可用"""
    global chatbot
    
    if chatbot is not None:
        logger.info(f"检查chatbot.chat_handler: {chatbot.chat_handler is not None}")
        # 如果chatbot模块存在但chat_handler不存在，尝试创建
        if not hasattr(chatbot, 'chat_handler') or chatbot.chat_handler is None:
            logger.info("chatbot模块存在，但chat_handler不存在，尝试创建")
            try:
                # 尝试从langchain_helper模块导入
                from langchain_helper import create_chat_handler
                chatbot.chat_handler = create_chat_handler()
                logger.info("成功创建聊天处理器")
            except Exception as chat_error:
                logger.error(f"创建聊天处理器失败: {chat_error}")
                
                # 如果langchain_helper导入失败，尝试直接使用OpenAI API
                try:
                    # 直接使用direct_chatbot模块
                    if direct_chat_handler:
                        logger.info("使用direct_chat_handler作为chatbot.chat_handler")
                        chatbot.chat_handler = direct_chat_handler
                    else:
                        # 尝试直接使用OpenAI API
                        from openai import OpenAI
                        
                        class DirectOpenAIChatHandler:
                            def __init__(self):
                                self.api_key = os.environ.get("OPENAI_API_KEY")
                                self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
                                self.client = OpenAI(api_key=self.api_key)
                                self.messages = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。"}]
                            
                            def chat(self, message):
                                self.messages.append({"role": "user", "content": message})
                                
                                completion = self.client.chat.completions.create(
                                    model=self.model,
                                    messages=self.messages
                                )
                                
                                response = completion.choices[0].message.content
                                self.messages.append({"role": "assistant", "content": response})
                                return response
                        
                        chatbot.chat_handler = DirectOpenAIChatHandler()
                        logger.info("成功创建DirectOpenAIChatHandler")
                except Exception as direct_error:
                    logger.error(f"创建DirectOpenAIChatHandler失败: {direct_error}")
        
        # 如果chat_handler已存在
        if hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None:
            logger.info(f"chatbot.chat_handler已存在: {type(chatbot.chat_handler).__name__}")
            return True
    
    # 如果chatbot不存在，创建一个新的
    try:
        # 检查chatbot.py是否存在
        chatbot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chatbot.py')
        if not os.path.exists(chatbot_path):
            logger.error(f"未找到chatbot.py: {chatbot_path}")
            return False
        
        # 动态加载模块
        spec = importlib.util.spec_from_file_location("chatbot", chatbot_path)
        chatbot = importlib.util.module_from_spec(spec)
        sys.modules["chatbot"] = chatbot
        spec.loader.exec_module(chatbot)
        
        # 如果chatbot模块中还没有chat_handler,尝试直接创建一个
        if not hasattr(chatbot, 'chat_handler') or chatbot.chat_handler is None:
            try:
                # 尝试从langchain_helper模块导入
                from langchain_helper import create_chat_handler
                chatbot.chat_handler = create_chat_handler()
                logger.info("成功创建聊天处理器")
            except Exception as chat_error:
                logger.error(f"创建聊天处理器失败: {chat_error}")
                
                # 使用direct_chatbot模块
                if direct_chat_handler:
                    logger.info("使用direct_chat_handler作为chatbot.chat_handler")
                    chatbot.chat_handler = direct_chat_handler
                else:
                    # 最后一次尝试，创建一个直接处理器
                    try:
                        # 强制使用OpenAI
                        logger.info("尝试直接使用OpenAI API创建处理器")
                        
                        from openai import OpenAI
                        
                        class DirectOpenAIChatHandler:
                            def __init__(self):
                                self.api_key = os.environ.get("OPENAI_API_KEY")
                                self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
                                self.client = OpenAI(api_key=self.api_key)
                                self.messages = [{"role": "system", "content": "你是一个画廊中的智能助手，能够回答关于展示的PDF文档的问题。"}]
                            
                            def chat(self, message):
                                self.messages.append({"role": "user", "content": message})
                                
                                completion = self.client.chat.completions.create(
                                    model=self.model,
                                    messages=self.messages
                                )
                                
                                response = completion.choices[0].message.content
                                self.messages.append({"role": "assistant", "content": response})
                                return response
                        
                        chatbot.chat_handler = DirectOpenAIChatHandler()
                        logger.info("成功创建DirectOpenAIChatHandler")
                        
                    except Exception as direct_error:
                        logger.error(f"创建DirectOpenAIChatHandler失败: {direct_error}")
        
        logger.info("成功动态加载chatbot模块")
        logger.info(f"chat_handler是否存在: {hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None}")
        
        return hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None
    except Exception as e:
        logger.error(f"加载chatbot模块失败: {e}")
        return False

def run(server_class=ThreadedHTTPServer, handler_class=GalleryHandler, port=8000):
    # 确保chatbot模块可用
    ensure_chatbot_module()
    
    # 启动服务器
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f'Starting server on port {port}...')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到键盘中断，关闭服务器...")
    finally:
        httpd.server_close()
        logger.info("服务器已关闭")

if __name__ == '__main__':
    run() 