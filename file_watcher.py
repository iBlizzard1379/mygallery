"""
文件监听器模块
监控images目录中的文件变化，并自动更新向量数据库
"""

import os
import time
import logging
from typing import Callable, Dict, Any, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent

# 导入文档处理器
try:
    from document_processor import get_document_processor
except ImportError:
    print("警告: 无法导入document_processor模块")
    get_document_processor = None

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

class DocumentEventHandler(FileSystemEventHandler):
    """
    文档事件处理器，监听文件变化并触发处理
    """
    
    def __init__(self, watch_dir: str, processor_func: Callable):
        """
        初始化文档事件处理器
        
        Args:
            watch_dir: 监听的目录
            processor_func: 文档处理函数
        """
        self.watch_dir = watch_dir
        self.processor_func = processor_func
        
        # 防止重复处理的计时器
        self.last_processed = {}
        # 处理延迟（秒）：防止短时间内重复处理同一文件
        self.process_delay = 5
    
    def dispatch(self, event):
        """处理所有事件类型"""
        # 获取文件路径
        file_path = event.src_path
        
        # 检查是否为支持的文件格式
        if not self._is_supported_file(file_path):
            return
        
        # 检查是否需要处理该事件
        if self._should_process(event):
            # 记录处理时间
            self.last_processed[file_path] = time.time()
            # 调用处理函数
            try:
                self.processor_func(file_path)
            except Exception as e:
                logger.error(f"处理文件事件时出错: {file_path} - {e}")
    
    def _is_supported_file(self, file_path: str) -> bool:
        """检查是否为支持的文件格式"""
        # 支持的文件扩展名
        supported_extensions = {
            '.pdf', '.docx', '.doc', '.pptx', '.ppt', 
            '.xlsx', '.xls', '.jpg', '.jpeg', '.png', 
            '.gif', '.bmp', '.tiff', '.webp'
        }
        
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in supported_extensions
    
    def _should_process(self, event) -> bool:
        """判断事件是否需要处理"""
        # 获取文件路径
        file_path = event.src_path
        
        # 如果是创建或修改事件，且是支持的文件格式
        if (isinstance(event, FileCreatedEvent) or isinstance(event, FileModifiedEvent)) \
           and self._is_supported_file(file_path):
            
            # 检查文件是否存在（有些编辑器可能会触发虚假事件）
            if not os.path.exists(file_path):
                return False
            
            # 检查文件大小是否为0
            try:
                if os.path.getsize(file_path) == 0:
                    return False
            except Exception:
                return False
            
            # 检查是否在短时间内重复处理
            current_time = time.time()
            last_time = self.last_processed.get(file_path, 0)
            if current_time - last_time < self.process_delay:
                logger.debug(f"跳过重复处理: {file_path}")
                return False
            
            # 获取文件扩展名用于日志
            file_ext = os.path.splitext(file_path)[1].lower()
            logger.info(f"检测到 {file_ext} 文件变更: {file_path}")
            return True
        
        # 如果是删除事件，暂不处理
        # 在将来的版本中可以考虑从向量数据库中删除相应的文档
        return False

class FileWatcher:
    """
    文件监听器，监控目录中的文件变化
    """
    
    def __init__(self, watch_dir: str = None):
        """
        初始化文件监听器
        
        Args:
            watch_dir: 监听的目录，默认为 'images'
        """
        # 设置监听目录
        self.watch_dir = watch_dir or 'images'
        
        # 确保目录存在
        if not os.path.exists(self.watch_dir):
            os.makedirs(self.watch_dir, exist_ok=True)
        
        # 获取文档处理器
        if get_document_processor:
            self.document_processor = get_document_processor()
        else:
            self.document_processor = None
            logger.error("文档处理器不可用，文件监听功能将受限")
        
        # 初始化观察者
        self.observer = None
        self.event_handler = None
    
    def _process_document(self, file_path: str) -> None:
        """
        处理文档的回调函数
        
        Args:
            file_path: 文档路径
        """
        logger.info(f"处理文档: {file_path}")
        
        if self.document_processor:
            try:
                result = self.document_processor.process_document(file_path)
                if result:
                    logger.info(f"文档处理成功: {file_path}")
                else:
                    logger.warning(f"文档处理失败: {file_path}")
            except Exception as e:
                logger.error(f"处理文档时出错: {file_path} - {e}")
        else:
            logger.error("文档处理器不可用，无法处理文档")
    
    def start(self) -> bool:
        """
        启动文件监听器
        
        Returns:
            是否成功启动
        """
        try:
            if self.observer:
                logger.warning("文件监听器已在运行")
                return True
            
            logger.info(f"启动文件监听器，监听目录: {self.watch_dir}")
            
            # 创建事件处理器
            self.event_handler = DocumentEventHandler(
                watch_dir=self.watch_dir,
                processor_func=self._process_document
            )
            
            # 创建观察者
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                path=self.watch_dir,
                recursive=True
            )
            
            # 启动观察者
            self.observer.start()
            logger.info("文件监听器已启动")
            
            return True
        
        except Exception as e:
            logger.error(f"启动文件监听器时出错: {e}")
            # 清理资源
            if self.observer:
                self.observer.stop()
                self.observer = None
            
            return False
    
    def stop(self) -> None:
        """停止文件监听器"""
        if not self.observer:
            logger.warning("文件监听器未运行")
            return
        
        logger.info("停止文件监听器")
        
        try:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.event_handler = None
            logger.info("文件监听器已停止")
        except Exception as e:
            logger.error(f"停止文件监听器时出错: {e}")
    
    def is_running(self) -> bool:
        """
        检查文件监听器是否在运行
        
        Returns:
            是否在运行
        """
        return self.observer is not None and self.observer.is_alive()
    
    def process_existing_documents(self) -> None:
        """处理已存在的文档"""
        if not self.document_processor:
            logger.error("文档处理器不可用，无法处理已存在的文档")
            return
        
        logger.info("处理已存在的文档...")
        
        try:
            # 使用文档处理器的批处理功能
            success_count, total_count = self.document_processor.process_all_documents()
            logger.info(f"已处理 {success_count}/{total_count} 个文档")
        except Exception as e:
            logger.error(f"处理已存在文档时出错: {e}")

# 单例模式
_file_watcher_instance = None

def get_file_watcher() -> FileWatcher:
    """
    获取文件监听器单例实例
    
    Returns:
        FileWatcher实例
    """
    global _file_watcher_instance
    if _file_watcher_instance is None:
        _file_watcher_instance = FileWatcher()
    return _file_watcher_instance

# 测试代码
if __name__ == "__main__":
    watcher = get_file_watcher()
    
    # 处理已存在的文档
    watcher.process_existing_documents()
    
    # 启动监听
    if watcher.start():
        try:
            logger.info("监听中，按Ctrl+C退出...")
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到退出信号")
        finally:
            watcher.stop() 