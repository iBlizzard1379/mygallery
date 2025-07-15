#!/usr/bin/env python3
"""
多用户并发测试脚本
验证画廊系统的多用户会话隔离和并发性能
"""
import asyncio
import aiohttp
import time
import json
import sys
import random
from typing import List, Dict, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """测试结果类"""
    user_id: str
    session_id: str
    success: bool
    response_time: float
    response_data: Dict
    error: str = None

class ConcurrentTester:
    """并发测试器"""
    
    def __init__(self, server_url: str = "http://localhost:8000", num_users: int = 10):
        self.server_url = server_url
        self.num_users = num_users
        self.results: List[TestResult] = []
        self.lock = threading.Lock()
        
        # 测试消息池
        self.test_messages = [
            "你好，请介绍一下画廊系统",
            "PDF文档主要讲了什么内容？",
            "请总结一下文档的要点",
            "这个系统有什么功能？",
            "如何使用画廊功能？",
            "文档中提到了哪些重要概念？",
            "请解释一下相关技术原理",
            "有什么使用建议吗？",
            "系统的主要优势是什么？",
            "如何优化使用体验？"
        ]
    
    async def test_single_user(self, session: aiohttp.ClientSession, user_id: str, num_requests: int = 3) -> List[TestResult]:
        """测试单个用户的多次请求"""
        user_results = []
        session_id = None
        
        logger.info(f"用户 {user_id} 开始测试，计划发送 {num_requests} 个请求")
        
        for i in range(num_requests):
            try:
                # 随机选择测试消息
                message = random.choice(self.test_messages)
                
                # 准备请求数据
                request_data = {
                    "message": f"{message} (用户{user_id}的第{i+1}次请求)"
                }
                
                # 如果有会话ID，包含在请求中
                if session_id:
                    request_data["session_id"] = session_id
                
                # 发送请求
                start_time = time.time()
                async with session.post(
                    f"{self.server_url}/chatbot-api",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # 更新会话ID
                        if response_data.get("session_id"):
                            session_id = response_data["session_id"]
                        
                        result = TestResult(
                            user_id=user_id,
                            session_id=session_id or "unknown",
                            success=True,
                            response_time=response_time,
                            response_data=response_data
                        )
                        
                        logger.info(f"用户 {user_id} 请求 {i+1} 成功，响应时间: {response_time:.2f}s")
                    else:
                        error_text = await response.text()
                        result = TestResult(
                            user_id=user_id,
                            session_id=session_id or "unknown",
                            success=False,
                            response_time=response_time,
                            response_data={},
                            error=f"HTTP {response.status}: {error_text}"
                        )
                        logger.error(f"用户 {user_id} 请求 {i+1} 失败: {result.error}")
                
                user_results.append(result)
                
                # 请求间隔
                if i < num_requests - 1:
                    await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                result = TestResult(
                    user_id=user_id,
                    session_id=session_id or "unknown",
                    success=False,
                    response_time=0,
                    response_data={},
                    error=str(e)
                )
                user_results.append(result)
                logger.error(f"用户 {user_id} 请求 {i+1} 异常: {e}")
        
        return user_results
    
    async def run_concurrent_test(self, requests_per_user: int = 3) -> List[TestResult]:
        """运行并发测试"""
        logger.info(f"开始并发测试：{self.num_users} 个用户，每个用户 {requests_per_user} 个请求")
        
        async with aiohttp.ClientSession() as session:
            # 创建并发任务
            tasks = []
            for i in range(self.num_users):
                user_id = f"user_{i+1:03d}"
                task = self.test_single_user(session, user_id, requests_per_user)
                tasks.append(task)
            
            # 并发执行所有任务
            start_time = time.time()
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # 收集结果
            results = []
            for user_results in all_results:
                if isinstance(user_results, Exception):
                    logger.error(f"用户测试异常: {user_results}")
                else:
                    results.extend(user_results)
            
            logger.info(f"并发测试完成，总耗时: {total_time:.2f}s")
            return results
    
    def test_session_stats_api(self) -> Dict:
        """测试会话统计API"""
        try:
            import requests
            response = requests.get(f"{self.server_url}/api/session-stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_results(self, results: List[TestResult]) -> Dict:
        """分析测试结果"""
        if not results:
            return {"error": "没有测试结果"}
        
        # 基本统计
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r.success)
        failed_requests = total_requests - successful_requests
        
        # 响应时间统计
        response_times = [r.response_time for r in results if r.success]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        # 会话统计
        sessions = set(r.session_id for r in results if r.session_id != "unknown")
        users = set(r.user_id for r in results)
        
        # 错误统计
        errors = {}
        for result in results:
            if not result.success and result.error:
                error_type = result.error.split(':')[0] if ':' in result.error else result.error
                errors[error_type] = errors.get(error_type, 0) + 1
        
        # 会话隔离检查
        session_isolation_ok = len(sessions) == len(users)
        
        analysis = {
            "总体统计": {
                "总请求数": total_requests,
                "成功请求数": successful_requests,
                "失败请求数": failed_requests,
                "成功率": f"{successful_requests/total_requests*100:.1f}%" if total_requests > 0 else "0%"
            },
            "性能指标": {
                "平均响应时间": f"{avg_response_time:.2f}s",
                "最大响应时间": f"{max_response_time:.2f}s",
                "最小响应时间": f"{min_response_time:.2f}s"
            },
            "会话统计": {
                "用户数": len(users),
                "会话数": len(sessions),
                "会话隔离": "正常" if session_isolation_ok else "异常"
            },
            "错误统计": errors if errors else "无错误"
        }
        
        return analysis
    
    def generate_report(self, results: List[TestResult], analysis: Dict) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 60)
        report.append("画廊系统多用户并发测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"服务器地址: {self.server_url}")
        report.append("")
        
        # 总体统计
        report.append("📊 总体统计")
        report.append("-" * 20)
        for key, value in analysis["总体统计"].items():
            report.append(f"  {key}: {value}")
        report.append("")
        
        # 性能指标
        report.append("⚡ 性能指标")
        report.append("-" * 20)
        for key, value in analysis["性能指标"].items():
            report.append(f"  {key}: {value}")
        report.append("")
        
        # 会话统计
        report.append("🔄 会话统计")
        report.append("-" * 20)
        for key, value in analysis["会话统计"].items():
            report.append(f"  {key}: {value}")
        report.append("")
        
        # 错误统计
        if analysis["错误统计"] != "无错误":
            report.append("❌ 错误统计")
            report.append("-" * 20)
            for error_type, count in analysis["错误统计"].items():
                report.append(f"  {error_type}: {count} 次")
            report.append("")
        
        # 详细结果
        report.append("📋 详细结果")
        report.append("-" * 20)
        for result in results:
            status = "✅" if result.success else "❌"
            report.append(f"  {status} {result.user_id} | 会话:{result.session_id[:8]}... | {result.response_time:.2f}s")
            if not result.success:
                report.append(f"     错误: {result.error}")
        
        return "\n".join(report)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="画廊系统并发测试工具")
    parser.add_argument("--server", default="http://localhost:8000", help="服务器地址")
    parser.add_argument("--users", type=int, default=5, help="并发用户数")
    parser.add_argument("--requests", type=int, default=3, help="每个用户的请求数")
    parser.add_argument("--output", help="保存测试报告到文件")
    parser.add_argument("--stats-only", action="store_true", help="仅获取会话统计")
    
    args = parser.parse_args()
    
    tester = ConcurrentTester(server_url=args.server, num_users=args.users)
    
    if args.stats_only:
        # 仅获取统计信息
        stats = tester.test_session_stats_api()
        print("当前会话统计:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return
    
    # 运行并发测试
    print(f"🚀 开始测试...")
    print(f"服务器: {args.server}")
    print(f"并发用户: {args.users}")
    print(f"每用户请求: {args.requests}")
    print("-" * 50)
    
    try:
        # 异步运行测试
        results = asyncio.run(tester.run_concurrent_test(args.requests))
        
        # 分析结果
        analysis = tester.analyze_results(results)
        
        # 生成报告
        report = tester.generate_report(results, analysis)
        
        # 输出报告
        print(report)
        
        # 保存报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 报告已保存到: {args.output}")
        
        # 获取当前会话统计
        print("\n📈 当前系统状态:")
        stats = tester.test_session_stats_api()
        if "error" not in stats:
            print(f"  活跃会话数: {stats.get('active_sessions', 0)}")
            print(f"  最大会话数: {stats.get('max_sessions', 0)}")
        else:
            print(f"  无法获取统计: {stats['error']}")
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 