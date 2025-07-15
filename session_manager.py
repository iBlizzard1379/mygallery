"""
用户会话管理器
支持多用户并发访问的会话隔离系统
"""
import uuid
import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UserSession:
    """用户会话类"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.rag_chain = None  # 延迟初始化
        self._lock = threading.Lock()  # 会话级别的线程锁
        self._initialized = False
    
    def _ensure_rag_chain(self):
        """确保RAG链已初始化"""
        if not self._initialized:
            try:
                from rag_chain import create_rag_chain
                self.rag_chain = create_rag_chain()
                self._initialized = True
                logger.info(f"会话 {self.session_id} 的RAG链初始化完成")
            except Exception as e:
                logger.error(f"初始化会话 {self.session_id} 的RAG链失败: {e}")
                raise
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
    
    def query(self, message: str) -> Dict:
        """线程安全的查询处理"""
        with self._lock:
            self.update_activity()
            self._ensure_rag_chain()
            
            if not self.rag_chain:
                return {
                    "answer": "抱歉，系统初始化失败，请稍后重试。",
                    "success": False,
                    "error": "RAG链未初始化"
                }
            
            try:
                result = self.rag_chain.query(message)
                logger.info(f"会话 {self.session_id} 处理查询成功")
                return result
            except Exception as e:
                logger.error(f"会话 {self.session_id} 查询失败: {e}")
                return {
                    "answer": f"抱歉，处理您的请求时出现了问题: {str(e)}",
                    "success": False,
                    "error": str(e)
                }
    
    def is_expired(self, max_idle_minutes: int = 30) -> bool:
        """检查会话是否过期"""
        return datetime.now() - self.last_activity > timedelta(minutes=max_idle_minutes)
    
    def clear_history(self):
        """清除会话历史"""
        with self._lock:
            if self.rag_chain:
                self.rag_chain.clear_history()
                logger.info(f"清除会话 {self.session_id} 的历史记录")
    
    def get_info(self) -> Dict:
        """获取会话信息"""
        with self._lock:
            return {
                "session_id": self.session_id,
                "created_at": self.created_at.isoformat(),
                "last_activity": self.last_activity.isoformat(),
                "initialized": self._initialized,
                "idle_minutes": (datetime.now() - self.last_activity).total_seconds() / 60
            }

class SessionManager:
    """会话管理器"""
    def __init__(self, max_idle_minutes: int = 30, cleanup_interval: int = 300, max_sessions: int = 50):
        self.sessions: Dict[str, UserSession] = {}
        self.max_idle_minutes = max_idle_minutes
        self.cleanup_interval = cleanup_interval
        self.max_sessions = max_sessions
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._start_cleanup_thread()
        logger.info(f"会话管理器初始化完成 - 最大会话数: {max_sessions}, 空闲超时: {max_idle_minutes}分钟")
    
    def create_session(self) -> str:
        """创建新会话"""
        with self._lock:
            # 检查会话数量限制
            if len(self.sessions) >= self.max_sessions:
                # 强制清理过期会话
                self._cleanup_expired_sessions_internal()
                
                # 如果仍然超出限制，拒绝创建新会话
                if len(self.sessions) >= self.max_sessions:
                    raise Exception(f"达到最大会话数限制 ({self.max_sessions})")
            
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = UserSession(session_id)
            logger.info(f"创建新会话: {session_id}, 当前会话数: {len(self.sessions)}")
            return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """获取会话"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired(self.max_idle_minutes):
                return session
            elif session:
                # 清理过期会话
                del self.sessions[session_id]
                logger.info(f"清理过期会话: {session_id}")
        return None
    
    def _cleanup_expired_sessions_internal(self):
        """内部清理过期会话（需要在锁内调用）"""
        expired_sessions = [
            sid for sid, session in self.sessions.items() 
            if session.is_expired(self.max_idle_minutes)
        ]
        for sid in expired_sessions:
            del self.sessions[sid]
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
        return len(expired_sessions)
    
    def cleanup_expired_sessions(self):
        """清理过期会话（公共接口）"""
        with self._lock:
            return self._cleanup_expired_sessions_internal()
    
    def force_cleanup_session(self, session_id: str) -> bool:
        """强制清理指定会话"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"强制清理会话: {session_id}")
                return True
            return False
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    cleaned_count = self.cleanup_expired_sessions()
                    if cleaned_count > 0:
                        logger.info(f"定期清理完成，清理了 {cleaned_count} 个过期会话")
                except Exception as e:
                    logger.error(f"清理线程出错: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("会话清理线程已启动")
    
    def get_stats(self) -> Dict:
        """获取会话统计信息"""
        with self._lock:
            active_sessions = []
            for session in self.sessions.values():
                try:
                    active_sessions.append(session.get_info())
                except Exception as e:
                    logger.warning(f"获取会话信息失败: {e}")
            
            return {
                "active_sessions": len(self.sessions),
                "max_sessions": self.max_sessions,
                "max_idle_minutes": self.max_idle_minutes,
                "cleanup_interval": self.cleanup_interval,
                "sessions": active_sessions
            }
    
    def shutdown(self):
        """关闭会话管理器"""
        with self._lock:
            logger.info("正在关闭会话管理器...")
            # 清理所有会话
            session_count = len(self.sessions)
            self.sessions.clear()
            logger.info(f"会话管理器已关闭，清理了 {session_count} 个会话")

# 全局会话管理器实例
# 从环境变量读取配置，提供默认值
import os
MAX_IDLE_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL_SECONDS', '300'))
MAX_SESSIONS = int(os.getenv('MAX_SESSIONS', '50'))

session_manager = SessionManager(
    max_idle_minutes=MAX_IDLE_MINUTES,
    cleanup_interval=CLEANUP_INTERVAL,
    max_sessions=MAX_SESSIONS
)

def get_session_manager() -> SessionManager:
    """获取全局会话管理器实例"""
    return session_manager 