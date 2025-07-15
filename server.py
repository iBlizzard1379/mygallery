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

# 添加会话管理器
try:
    from session_manager import get_session_manager
    session_manager = get_session_manager()
    logger.info("已导入会话管理器")
except ImportError as e:
    logger.error(f"无法导入会话管理器: {e}")
    session_manager = None

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
        
        let sessionId = null;
        
        function sendMessage() {{
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            
            if (message) {{
                // 显示用户消息
                addMessage(message, 'user');
                input.value = '';
                
                // 显示正在输入
                const typingIndicator = addMessage('正在思考...', 'bot');
                
                // 准备请求数据
                const requestData = {{ 
                    message: message,
                    session_id: sessionId  // 包含会话ID
                }};
                
                // 发送到后端
                fetch('/chatbot-api', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(requestData),
                }})
                .then(response => response.json())
                .then(data => {{
                    // 移除输入指示器
                    typingIndicator.remove();
                    
                    // 更新会话ID
                    if (data.session_id) {{
                        sessionId = data.session_id;
                    }}
                    
                    // 显示机器人回复
                    const responseText = data.response || '抱歉，无法处理您的请求';
                    addMessage(responseText, 'bot');
                    
                    // 显示信息来源（如果有）
                    if (data.source_type && data.source_type !== 'unknown') {{
                        const sourceInfo = getSourceTypeDisplay(data.source_type);
                        addMessage(`💡 ${{sourceInfo}}`, 'info');
                    }}
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
        
        function getSourceTypeDisplay(sourceType) {{
            const sourceMap = {{
                'document_only': '回答基于本地文档',
                'document+internet': '回答基于本地文档和网络搜索',
                'internet_only': '回答基于网络搜索',
                'rag': '回答基于知识库',
                'chatbot': '回答基于AI助手',
                'agent': '回答基于AI智能代理',
                'fallback': '基础回复模式'
            }};
            return sourceMap[sourceType] || '回答来源未知';
        }}
        
        function addMessage(text, sender) {{
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            
            if (sender === 'user') {{
                messageDiv.classList.add('user-message');
            }} else if (sender === 'info') {{
                messageDiv.classList.add('bot-message');
                messageDiv.style.fontSize = '0.9em';
                messageDiv.style.fontStyle = 'italic';
                messageDiv.style.opacity = '0.8';
            }} else {{
                messageDiv.classList.add('bot-message');
            }}
            
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
        
        # 管理面板
        elif path == '/admin':
            try:
                from datetime import datetime
                if session_manager:
                    stats = session_manager.get_stats()
                else:
                    stats = {"active_sessions": 0, "sessions": [], "max_sessions": 0}
                
                # 获取资源统计
                try:
                    from resource_manager import get_resource_manager
                    resource_stats = get_resource_manager().get_stats()
                    health_status = get_resource_manager().health_check()
                except Exception as e:
                    resource_stats = {"error": str(e)}
                    health_status = {"status": "unknown", "error": str(e)}
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>画廊系统管理面板</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                        .container {{ max-width: 1200px; margin: 0 auto; }}
                        .card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
                        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
                        .stat-item {{ padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #4CAF50; }}
                        .session {{ background: #fff; padding: 12px; margin: 8px 0; border-radius: 5px; border-left: 3px solid #2196F3; }}
                        .session-expired {{ border-left-color: #ff9800; }}
                        .health-ok {{ color: #4CAF50; }}
                        .health-error {{ color: #f44336; }}
                        .button {{ 
                            padding: 10px 20px; margin: 5px; background: #4CAF50; color: white; 
                            border: none; border-radius: 4px; cursor: pointer; text-decoration: none;
                            display: inline-block;
                        }}
                        .button:hover {{ background: #45a049; }}
                        .button-danger {{ background: #f44336; }}
                        .button-danger:hover {{ background: #da190b; }}
                        .timestamp {{ font-size: 0.9em; color: #666; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎨 画廊系统管理面板</h1>
                            <p class="timestamp">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                        
                        <div class="card">
                            <h3>🔧 系统状态</h3>
                            <div class="stats-grid">
                                <div class="stat-item">
                                    <strong>活跃会话数</strong><br>
                                    <span style="font-size: 1.5em;">{stats['active_sessions']}</span> / {stats.get('max_sessions', 50)}
                                </div>
                                <div class="stat-item">
                                    <strong>健康状态</strong><br>
                                    <span class="{'health-ok' if health_status.get('status') == 'healthy' else 'health-error'}">
                                        {health_status.get('status', 'unknown').upper()}
                                    </span>
                                </div>
                                <div class="stat-item">
                                    <strong>资源访问次数</strong><br>
                                    <span style="font-size: 1.2em;">{resource_stats.get('access_count', 0)}</span>
                                </div>
                                <div class="stat-item">
                                    <strong>错误率</strong><br>
                                    <span style="font-size: 1.2em;">{resource_stats.get('error_rate', 0):.2f}%</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>📊 会话列表</h3>
                            {''.join([f'''<div class="session {'session-expired' if s.get('idle_minutes', 0) > 25 else ''}">
                                <strong>会话ID:</strong> {s["session_id"][:8]}...<br>
                                <strong>创建时间:</strong> {s["created_at"]}<br>
                                <strong>最后活动:</strong> {s["last_activity"]}<br>
                                <strong>空闲时间:</strong> {s.get("idle_minutes", 0):.1f} 分钟
                            </div>''' for s in stats['sessions']]) if stats['sessions'] else '<p>暂无活跃会话</p>'}
                        </div>
                        
                        <div class="card">
                            <h3>⚙️ 操作</h3>
                            <button class="button" onclick="location.reload()">🔄 刷新状态</button>
                            <button class="button" onclick="cleanupSessions()">🧹 清理过期会话</button>
                            <button class="button button-danger" onclick="location.href='/'">🏠 返回主页</button>
                        </div>
                    </div>
                    
                    <script>
                        function cleanupSessions() {{
                            if (confirm('确定要清理过期会话吗？')) {{
                                fetch('/api/cleanup-sessions', {{method: 'POST'}})
                                .then(response => response.json())
                                .then(data => {{
                                    alert(data.message || '操作完成');
                                    location.reload();
                                }})
                                .catch(error => {{
                                    alert('操作失败: ' + error);
                                }});
                            }}
                        }}
                        
                        // 自动刷新
                        setInterval(() => location.reload(), 30000);
                    </script>
                </body>
                </html>
                """
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
                return
            except Exception as e:
                logger.error(f"管理面板错误: {e}")
                self.send_error(500, str(e))
                return
                
        # 会话状态API
        elif path == '/api/session-stats':
            try:
                if session_manager:
                    stats = session_manager.get_stats()
                else:
                    stats = {"active_sessions": 0, "sessions": []}
                
                response_json = json.dumps(stats, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(response_json)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_json)
                return
            except Exception as e:
                logger.error(f"获取会话统计失败: {e}")
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
                    elif file.lower().endswith(('.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls')):
                        documents.append(file)
                
                # 对文件列表进行自然排序（支持数字排序）
                import re
                def natural_sort_key(filename):
                    """自然排序键函数，正确处理数字序列"""
                    # 分离数字和文字部分
                    parts = re.split(r'(\d+)', filename.lower())
                    # 将数字部分转换为整数进行排序
                    for i in range(len(parts)):
                        if parts[i].isdigit():
                            parts[i] = int(parts[i])
                    return parts
                
                # 对图片和文档分别排序
                images.sort(key=natural_sort_key)
                documents.sort(key=natural_sort_key)
                
                logger.info(f"排序后的图片: {images}")
                logger.info(f"排序后的文档: {documents}")
                
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
        
        # 处理文档内容API请求
        if path == '/api/document-content':
            try:
                # 获取请求内容长度
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # 解析JSON数据
                data = json.loads(post_data.decode('utf-8'))
                filename = data.get('filename', '')
                
                logger.info(f"请求文档内容: {filename}")
                
                if not filename:
                    raise ValueError("文件名不能为空")
                
                # 获取文档处理器
                try:
                    from document_processors.enhanced_document_processor import get_enhanced_document_processor
                    processor = get_enhanced_document_processor()
                    
                    # 构建文件路径
                    file_path = os.path.join('images', filename)
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"文件不存在: {file_path}")
                    
                    # 获取特定处理器
                    specific_processor = processor._get_processor(file_path)
                    if not specific_processor:
                        raise ValueError(f"不支持的文件格式: {filename}")
                    
                    # 提取文本内容
                    content = specific_processor.extract_text(file_path)
                    
                    # 提取元数据
                    metadata = specific_processor.extract_metadata(file_path)
                    
                    # 准备响应
                    response_data = {
                        'success': True,
                        'content': content,
                        'metadata': {
                            'filename': filename,
                            'processor': specific_processor.name,
                            'document_type': metadata.get('document_type', '未知'),
                            'file_size': metadata.get('file_size', 0),
                            'processed_time': metadata.get('processed_time', '未知')
                        }
                    }
                    
                    logger.info(f"成功提取文档内容: {filename}, 长度: {len(content)} 字符")
                    
                except Exception as e:
                    logger.error(f"提取文档内容失败: {filename} - {e}")
                    response_data = {
                        'success': False,
                        'error': str(e),
                        'content': None
                    }
                
                # 发送响应
                response_json = json.dumps(response_data, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(response_json)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_json)
                return
                
            except Exception as e:
                logger.error(f"处理文档内容API请求时出错: {str(e)}")
                # 发送错误响应
                error_response = json.dumps({
                    'success': False,
                    'error': str(e),
                    'content': None
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(error_response)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_response)
                return
        
        # 处理聊天API请求 - 使用会话管理器
        if path == '/chatbot-api':
            try:
                # 获取请求内容
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                
                logger.info(f"收到聊天信息: {message}")
                
                # 会话管理 - 获取或创建会话ID
                session_id = data.get('session_id')
                if not session_id or not session_manager:
                    if session_manager:
                        try:
                            session_id = session_manager.create_session()
                            logger.info(f"为新用户创建会话: {session_id}")
                        except Exception as e:
                            logger.error(f"创建会话失败: {e}")
                            raise Exception("系统繁忙，请稍后重试")
                    else:
                        # 回退到原有逻辑
                        logger.warning("会话管理器不可用，使用原有处理方式")
                        session_id = "fallback"
                
                # 使用会话管理器处理查询
                if session_manager and session_id != "fallback":
                    user_session = session_manager.get_session(session_id)
                    if not user_session:
                        # 会话不存在或过期，创建新会话
                        try:
                            session_id = session_manager.create_session()
                            user_session = session_manager.get_session(session_id)
                            logger.info(f"会话过期或不存在，创建新会话: {session_id}")
                        except Exception as e:
                            logger.error(f"重新创建会话失败: {e}")
                            raise Exception("系统繁忙，请稍后重试")
                    
                    # 使用用户专属的会话处理查询
                    logger.info(f"处理会话 {session_id} 的消息")
                    result = user_session.query(message)
                    response = result.get("answer", "抱歉，无法处理您的请求")
                    success = result.get("success", False)
                    search_type = result.get("search_type", "unknown")
                else:
                    # 回退到原有逻辑
                    logger.warning("使用回退处理方式")
                    success, response, search_type = self._fallback_chat_processing(message)
                
                # 准备响应
                response_data = {
                    'response': response,
                    'session_id': session_id,
                    'success': success,
                    'source_type': search_type
                }
                
                # 发送响应
                response_json = json.dumps(response_data, ensure_ascii=False).encode('utf-8')
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
                    'success': False,
                    'response': '抱歉，系统出现问题，请稍后重试。'
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response)
                return
        # 处理会话清理API
        elif path == '/api/cleanup-sessions':
            try:
                if session_manager:
                    cleaned_count = session_manager.cleanup_expired_sessions()
                    response_data = {'success': True, 'message': f'清理了{cleaned_count}个过期会话'}
                else:
                    response_data = {'success': False, 'message': '会话管理器不可用'}
                
                response_json = json.dumps(response_data, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(response_json)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_json)
                return
            except Exception as e:
                logger.error(f"清理会话失败: {e}")
                self.send_error(500, str(e))
                return
        else:
            # 其他POST请求暂不支持
            self.send_error(405, "Method not allowed")
            return
    
    def _fallback_chat_processing(self, message: str):
        """回退聊天处理方式"""
        try:
            # 检查处理器可用性
            chatbot_available = chatbot and hasattr(chatbot, 'chat_handler') and chatbot.chat_handler is not None
            rag_chain_available = False
            
            # 检查是否有RAG链可用
            try:
                from rag_chain import create_rag_chain
                rag_chain = create_rag_chain()
                rag_chain_available = rag_chain is not None
                logger.info(f"RAG链可用: {rag_chain_available}")
            except Exception as e:
                logger.error(f"无法创建RAG链: {e}")
                rag_chain_available = False
            
            logger.info(f"chatbot可用: {chatbot_available}, RAG链可用: {rag_chain_available}")
            
            # 优先使用RAG链
            if rag_chain_available:
                try:
                    logger.info("使用RAG链处理查询（回退模式）")
                    result = rag_chain.query(message)
                    response = result.get("answer", "")
                    search_type = result.get("search_type", "rag")
                    logger.info(f"RAG链回复: {response[:50]}...")
                    return True, response, search_type
                except Exception as e:
                    logger.error(f"RAG链处理错误: {e}")
                    # 继续尝试chatbot
            
            # 使用普通聊天处理器
            if chatbot_available:
                try:
                    logger.info("使用chatbot处理器（回退模式）")
                    response = chatbot.chat_handler.chat(message)
                    logger.info(f"聊天回复: {response[:50]}...")
                    return True, response, "chatbot"
                except Exception as e:
                    logger.error(f"chatbot处理器错误: {e}")
            
            # 最后的回退
            response = f"收到您的消息：{message}。感谢您的提问，我会尽力回答。"
            logger.warning("所有聊天处理器不可用，使用最基本回复")
            return False, response, "fallback"
            
        except Exception as e:
            logger.error(f"回退处理失败: {e}")
            return False, f"抱歉，处理您的请求时出现了问题: {str(e)}", "error"

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