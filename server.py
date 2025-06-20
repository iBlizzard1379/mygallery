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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加chatbot模块
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
                logger.info("提供简易聊天界面")
                
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
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        .chatbox {{ display: flex; flex-direction: column; height: 100vh; }}
        .messages {{ flex-grow: 1; overflow-y: auto; padding: 20px; background-color: #f5f5f5; }}
        .input-area {{ display: flex; padding: 10px; background-color: white; border-top: 1px solid #ddd; }}
        #user-input {{ flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
        button {{ margin-left: 10px; padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        .message {{ margin-bottom: 10px; padding: 10px; border-radius: 4px; max-width: 70%; }}
        .user-message {{ background-color: #DCF8C6; align-self: flex-end; margin-left: auto; }}
        .bot-message {{ background-color: white; align-self: flex-start; }}
        .status {{ padding: 5px 10px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9em; }}
        .status-info {{ background-color: #e3f2fd; color: #0d47a1; }}
    </style>
</head>
<body>
    <div class="chatbox">
        <div class="messages" id="chat-messages">
            <div class="status status-info">画廊AI助手已准备就绪，可以回答您的问题</div>
            <div class="message bot-message">您好！我是画廊AI助手，有什么可以帮助您的吗？</div>
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
                
                # 解析JSON数据
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                
                logger.info(f"收到聊天信息: {message}")
                
                # 检查处理器可用性
                chatbot_available = chatbot and hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None
                rag_chain_available = False
                
                # 检查是否有RAG链可用
                try:
                    from rag_chain import get_rag_chain
                    rag_chain = get_rag_chain()
                    rag_chain_available = rag_chain is not None
                    logger.info(f"RAG链可用: {rag_chain_available}")
                except Exception as e:
                    logger.error(f"无法导入或初始化RAG链: {e}")
                    rag_chain_available = False
                
                logger.info(f"chatbot可用: {chatbot_available}, RAG链可用: {rag_chain_available}")
                
                # 优先使用RAG链（自动决定是否使用搜索工具）
                if rag_chain_available:
                    try:
                        logger.info("使用RAG链处理查询")
                        result = rag_chain.query(message)
                        response = result.get("answer", "")
                        logger.info(f"RAG链回复: {response[:50]}...")
                    except Exception as e:
                        logger.error(f"RAG链处理错误: {e}")
                        # 回退到普通聊天处理器
                        if chatbot_available:
                            logger.info("RAG链失败，尝试使用chatbot处理器")
                            try:
                                response = chatbot.chat_handler.chat(message)
                                logger.info(f"回复: {response[:50]}...")
                            except Exception as e2:
                                logger.error(f"chatbot处理器错误: {e2}")
                                response = f"抱歉，无法处理您的请求: {str(e2)}"
                        else:
                            response = f"抱歉，无法处理您的请求: {str(e)}"
                # 使用普通聊天处理器
                elif chatbot_available:
                    try:
                        logger.info("使用chatbot处理器")
                        response = chatbot.chat_handler.chat(message)
                        logger.info(f"聊天回复: {response[:50]}...")
                    except Exception as e:
                        logger.error(f"聊天处理器处理消息失败: {e}")
                        response = f"抱歉，处理您的消息时出现了问题: {str(e)}"
                else:
                    # 后备回复
                    response = f"收到您的消息：{message}。感谢您的提问，我会尽力回答。"
                    logger.warning("所有聊天处理器不可用，使用后备回复")
                
                # 准备响应
                response_data = {
                    'response': response,
                    'success': True
                }
                
                # 发送响应
                response_json = json.dumps(response_data).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
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
        return True
    
    try:
        # 先检查matplotlib是否可用
        try:
            import matplotlib
            logger.info("matplotlib已安装")
        except ImportError:
            logger.warning("matplotlib未安装，chatbot可能无法正常工作")
            
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
        
        logger.info("成功动态加载chatbot模块")
        return True
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