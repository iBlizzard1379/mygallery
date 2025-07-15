"""
系统监控脚本
监控画廊系统的资源使用情况、会话状态和应用健康度
"""
import psutil
import time
import requests
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """系统监控类"""
    
    def __init__(self, server_url: str = "http://localhost:8000", check_interval: int = 30):
        self.server_url = server_url
        self.check_interval = check_interval
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'max_sessions': 40,
            'error_rate': 10.0,
            'response_time': 5.0  # 秒
        }
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5分钟冷却期
        
    def get_system_metrics(self) -> Dict:
        """获取系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络连接数
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, OSError):
                connections = -1
                
            # 进程信息
            try:
                current_process = psutil.Process()
                process_memory = current_process.memory_info().rss / 1024 / 1024  # MB
                process_cpu = current_process.cpu_percent()
            except psutil.NoSuchProcess:
                process_memory = -1
                process_cpu = -1
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / 1024**3,
                'memory_total_gb': memory.total / 1024**3,
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / 1024**3,
                'disk_total_gb': disk.total / 1024**3,
                'connections': connections,
                'process_memory_mb': process_memory,
                'process_cpu_percent': process_cpu
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def get_application_metrics(self) -> Dict:
        """获取应用程序指标"""
        try:
            start_time = time.time()
            
            # 获取会话统计
            try:
                response = requests.get(f"{self.server_url}/api/session-stats", timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    session_stats = response.json()
                    app_available = True
                else:
                    session_stats = {"active_sessions": -1}
                    app_available = False
            except requests.RequestException as e:
                logger.warning(f"无法获取会话统计: {e}")
                session_stats = {"active_sessions": -1}
                app_available = False
                response_time = time.time() - start_time
            
            # 尝试健康检查（如果有的话）
            health_status = "unknown"
            try:
                if app_available:
                    # 这里可以添加具体的健康检查端点
                    health_status = "healthy"
                else:
                    health_status = "unhealthy"
            except Exception:
                health_status = "error"
            
            return {
                'timestamp': datetime.now().isoformat(),
                'app_available': app_available,
                'response_time': response_time,
                'active_sessions': session_stats.get('active_sessions', -1),
                'max_sessions': session_stats.get('max_sessions', 50),
                'health_status': health_status,
                'session_details': session_stats.get('sessions', [])
            }
        except Exception as e:
            logger.error(f"获取应用指标失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'app_available': False,
                'error': str(e)
            }
    
    def check_alerts(self, system_metrics: Dict, app_metrics: Dict):
        """检查告警条件"""
        current_time = time.time()
        alerts = []
        
        # 系统资源告警
        if system_metrics.get('cpu_percent', 0) > self.alert_thresholds['cpu_percent']:
            alert_key = 'high_cpu'
            if self._should_alert(alert_key, current_time):
                alerts.append(f"CPU使用率过高: {system_metrics['cpu_percent']:.1f}%")
        
        if system_metrics.get('memory_percent', 0) > self.alert_thresholds['memory_percent']:
            alert_key = 'high_memory'
            if self._should_alert(alert_key, current_time):
                alerts.append(f"内存使用率过高: {system_metrics['memory_percent']:.1f}%")
        
        if system_metrics.get('disk_percent', 0) > self.alert_thresholds['disk_percent']:
            alert_key = 'high_disk'
            if self._should_alert(alert_key, current_time):
                alerts.append(f"磁盘使用率过高: {system_metrics['disk_percent']:.1f}%")
        
        # 应用程序告警
        if not app_metrics.get('app_available', False):
            alert_key = 'app_down'
            if self._should_alert(alert_key, current_time):
                alerts.append("应用程序不可用")
                self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        if app_metrics.get('active_sessions', 0) > self.alert_thresholds['max_sessions']:
            alert_key = 'high_sessions'
            if self._should_alert(alert_key, current_time):
                alerts.append(f"活跃会话数过多: {app_metrics['active_sessions']}")
        
        if app_metrics.get('response_time', 0) > self.alert_thresholds['response_time']:
            alert_key = 'slow_response'
            if self._should_alert(alert_key, current_time):
                alerts.append(f"响应时间过长: {app_metrics['response_time']:.2f}秒")
        
        # 连续失败告警
        if self.consecutive_failures >= self.max_consecutive_failures:
            alert_key = 'consecutive_failures'
            if self._should_alert(alert_key, current_time):
                alerts.append(f"连续{self.consecutive_failures}次检查失败")
        
        return alerts
    
    def _should_alert(self, alert_key: str, current_time: float) -> bool:
        """检查是否应该发送告警（考虑冷却期）"""
        last_alert = self.last_alert_time.get(alert_key, 0)
        if current_time - last_alert > self.alert_cooldown:
            self.last_alert_time[alert_key] = current_time
            return True
        return False
    
    def send_alerts(self, alerts: list):
        """发送告警（可以扩展为邮件、钉钉等）"""
        if alerts:
            logger.warning("🚨 系统告警:")
            for alert in alerts:
                logger.warning(f"  - {alert}")
            
            # 这里可以添加其他告警方式，如：
            # - 发送邮件
            # - 钉钉机器人
            # - 短信告警
            # - 写入告警文件
            
            # 写入告警文件
            try:
                with open('alerts.log', 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    for alert in alerts:
                        f.write(f"{timestamp} - {alert}\n")
            except Exception as e:
                logger.error(f"写入告警文件失败: {e}")
    
    def log_metrics(self, system_metrics: Dict, app_metrics: Dict):
        """记录指标日志"""
        # 系统指标
        if system_metrics:
            logger.info(
                f"系统状态 - CPU: {system_metrics.get('cpu_percent', 0):.1f}%, "
                f"内存: {system_metrics.get('memory_percent', 0):.1f}%, "
                f"磁盘: {system_metrics.get('disk_percent', 0):.1f}%"
            )
        
        # 应用指标
        if app_metrics:
            status = "正常" if app_metrics.get('app_available', False) else "异常"
            logger.info(
                f"应用状态 - 状态: {status}, "
                f"活跃会话: {app_metrics.get('active_sessions', 0)}, "
                f"响应时间: {app_metrics.get('response_time', 0):.2f}s"
            )
    
    def run_once(self):
        """执行一次监控检查"""
        logger.debug("开始监控检查...")
        
        # 获取指标
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()
        
        # 记录日志
        self.log_metrics(system_metrics, app_metrics)
        
        # 检查告警
        alerts = self.check_alerts(system_metrics, app_metrics)
        if alerts:
            self.send_alerts(alerts)
        
        return {
            'system': system_metrics,
            'application': app_metrics,
            'alerts': alerts
        }
    
    def run_forever(self):
        """持续监控"""
        logger.info(f"开始系统监控，检查间隔: {self.check_interval}秒")
        logger.info(f"监控目标: {self.server_url}")
        logger.info(f"告警阈值: {self.alert_thresholds}")
        
        try:
            while True:
                try:
                    self.run_once()
                except KeyboardInterrupt:
                    logger.info("收到中断信号，停止监控")
                    break
                except Exception as e:
                    logger.error(f"监控检查出错: {e}")
                
                time.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"监控程序异常退出: {e}")
        finally:
            logger.info("监控程序已停止")

def main():
    """主函数"""
    # 从环境变量读取配置
    server_url = os.getenv('MONITOR_SERVER_URL', 'http://localhost:8000')
    check_interval = int(os.getenv('MONITOR_INTERVAL', '30'))
    
    # 创建监控器
    monitor = SystemMonitor(server_url=server_url, check_interval=check_interval)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # 执行一次检查
            result = monitor.run_once()
            print("监控结果:")
            print(f"系统指标: {result['system']}")
            print(f"应用指标: {result['application']}")
            if result['alerts']:
                print(f"告警: {result['alerts']}")
            return
        elif sys.argv[1] == '--help':
            print("使用方法:")
            print("  python monitor.py           # 持续监控")
            print("  python monitor.py --once    # 执行一次检查")
            print("  python monitor.py --help    # 显示帮助")
            print()
            print("环境变量:")
            print("  MONITOR_SERVER_URL  # 服务器URL (默认: http://localhost:8000)")
            print("  MONITOR_INTERVAL    # 检查间隔秒数 (默认: 30)")
            return
    
    # 持续监控
    monitor.run_forever()

if __name__ == "__main__":
    main() 