from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GalleryHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # 处理根目录请求
        if self.path == '/':
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
        
        # 处理/images和/images/请求
        if self.path in ['/images', '/images/']:
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
                
            except Exception as e:
                logger.error(f"处理请求时出错: {str(e)}")
                self.send_error(500, str(e))
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

def run(server_class=HTTPServer, handler_class=GalleryHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run() 