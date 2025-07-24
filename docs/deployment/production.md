# AI知识画廊--Ask me anything about UEC v1.0 部署指南

本文档描述如何在内网环境中部署AI知识画廊系统以支持多用户并发访问。

## 🎯 优化特性

本次优化实现了以下核心功能：

### ✅ 多用户并发支持
- **会话隔离**：每个用户拥有独立的聊天会话和上下文
- **线程安全**：所有共享资源都经过线程安全处理
- **资源管理**：智能管理向量数据库和AI模型资源
- **自动清理**：过期会话自动清理，防止内存泄漏

### ✅ 性能优化
- **资源复用**：共享向量数据库和文档处理器
- **连接池化**：优化数据库连接管理
- **内存优化**：Python垃圾回收和内存分配优化
- **并发处理**：ThreadedHTTPServer支持多线程请求处理

### ✅ 监控管理
- **实时监控**：系统资源和应用状态监控
- **管理面板**：Web界面查看会话状态和系统健康度
- **告警机制**：资源使用超限时自动告警
- **性能分析**：详细的响应时间和错误率统计

## 🚀 快速部署

### 1. 系统要求

**硬件要求**：
- CPU: 4核心以上
- 内存: 8GB以上（推荐16GB）
- 存储: 50GB以上可用空间
- 网络: 千兆内网

**软件要求**：
- Python 3.8+
- uv包管理工具
- Linux/macOS系统

### 2. 安装uv工具

```bash
# 安装uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 重新加载shell配置
source ~/.bashrc  # 或 source ~/.zshrc
```

### 3. 一键部署

```bash
# 克隆或进入项目目录
cd mygallery

# 使用部署脚本一键部署
./scripts/deploy_intranet.sh

# 或者指定参数部署
./scripts/deploy_intranet.sh --port 9000 --max-sessions 100
```

### 4. 查看部署选项

```bash
./scripts/deploy_intranet.sh --help
```

## ⚙️ 配置说明

### 环境变量配置

编辑 `.env` 文件或设置环境变量：

```bash
# 基本配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# 多用户并发配置
MAX_SESSIONS=50              # 最大同时会话数
SESSION_TIMEOUT_MINUTES=30   # 会话超时时间（分钟）
CLEANUP_INTERVAL_SECONDS=300 # 清理检查间隔（秒）

# 服务器配置
PORT=8000                    # 服务器端口
HOST=0.0.0.0                # 监听地址（0.0.0.0为所有网口）

# 监控配置
MONITOR_SERVER_URL=http://localhost:8000
MONITOR_INTERVAL=30          # 监控检查间隔（秒）
```

### 性能调优参数

```bash
# 系统优化
export PYTHON_GC_THRESHOLD="700,10,10"  # Python垃圾回收阈值
export MALLOC_TRIM_THRESHOLD=100000     # 内存分配优化
export PYTHONOPTIMIZE=2                 # Python字节码优化
export PYTHONDONTWRITEBYTECODE=1        # 禁用.pyc文件生成
```

## 📊 系统监控

### 管理面板

访问 `http://服务器IP:端口/admin` 查看系统状态：

- **系统状态**：CPU、内存、磁盘使用率
- **会话管理**：活跃会话列表和状态
- **健康检查**：各组件运行状态
- **性能指标**：响应时间、错误率统计

### 命令行监控

```bash
# 启动独立监控进程
python3 monitor.py

# 执行一次检查
python3 monitor.py --once

# 查看监控帮助
python3 monitor.py --help
```

### 监控告警

系统会在以下情况发出告警：

- CPU使用率 > 80%
- 内存使用率 > 85%
- 磁盘使用率 > 90%
- 活跃会话数 > 40
- 响应时间 > 5秒
- 应用程序不可用

告警信息会记录在 `monitor.log` 和 `alerts.log` 文件中。

## 🧪 性能测试

### 并发测试工具

使用内置的并发测试工具验证系统性能：

```bash
# 基本并发测试（5用户，每用户3请求）
python3 test_concurrent.py

# 高并发测试（20用户，每用户5请求）
python3 test_concurrent.py --users 20 --requests 5

# 保存测试报告
python3 test_concurrent.py --users 10 --requests 3 --output test_report.txt

# 仅查看当前会话统计
python3 test_concurrent.py --stats-only
```

### 压力测试建议

**轻负载测试**：
```bash
python3 test_concurrent.py --users 5 --requests 3
```

**中负载测试**：
```bash
python3 test_concurrent.py --users 15 --requests 5
```

**重负载测试**：
```bash
python3 test_concurrent.py --users 30 --requests 10
```

### 性能基准

基于推荐硬件配置的性能基准：

| 指标 | 目标值 |
|------|--------|
| 并发用户数 | 50+ |
| 平均响应时间 | < 3秒 |
| 峰值响应时间 | < 10秒 |
| 成功率 | > 95% |
| 内存使用 | < 4GB |
| CPU使用率 | < 70% |

## 🔧 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 更换端口
./scripts/deploy_intranet.sh --port 9000
```

**2. 内存不足**
```bash
# 减少最大会话数
export MAX_SESSIONS=20

# 减少会话超时时间
export SESSION_TIMEOUT_MINUTES=15
```

**3. uv工具未安装**
```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**4. Python版本过低**
```bash
# 检查Python版本
python3 --version

# 需要Python 3.8+，请升级Python
```

### 日志文件

系统运行时产生的日志文件：

- `server.log` - 服务器运行日志
- `monitor.log` - 监控系统日志
- `alerts.log` - 告警记录
- `test_report.txt` - 测试报告（如果生成）

### 调试模式

启用调试模式获取更多信息：

```bash
export DEBUG=true
./scripts/deploy_intranet.sh
```

## 🔒 安全建议

### 内网部署安全

1. **网络隔离**：确保服务器仅在内网可访问
2. **防火墙配置**：限制不必要的端口访问
3. **API密钥管理**：妥善保管OpenAI API密钥
4. **定期更新**：保持依赖包和系统更新

### 访问控制

```bash
# 限制监听地址（仅本机）
export HOST=127.0.0.1

# 或指定特定网段
export HOST=192.168.1.100
```

## 📈 扩展建议

### 水平扩展

**负载均衡部署**：
```bash
# 服务器1
./scripts/deploy_intranet.sh --port 8000

# 服务器2  
./scripts/deploy_intranet.sh --port 8001

# 使用Nginx负载均衡
```

### 垂直扩展

**资源升级**：
- 增加内存：支持更多并发会话
- 升级CPU：提高响应速度
- 使用SSD：加快向量数据库访问

## 🆘 技术支持

### 性能优化建议

1. **会话管理**：根据实际用户数调整 `MAX_SESSIONS`
2. **清理频率**：根据服务器性能调整 `CLEANUP_INTERVAL_SECONDS`
3. **模型选择**：使用 `gpt-4o-mini` 获得更快响应
4. **资源监控**：定期检查系统资源使用情况

### 最佳实践

1. **定期重启**：每24小时重启一次服务，清理累积状态
2. **日志轮转**：配置日志轮转，避免日志文件过大
3. **备份策略**：定期备份向量数据库和配置文件
4. **性能测试**：定期执行并发测试，确保系统稳定性

---

## 🎉 部署完成

部署完成后，您可以：

1. **访问应用**：`http://服务器IP:端口`
2. **查看管理面板**：`http://服务器IP:端口/admin`
3. **运行性能测试**：`python3 test_concurrent.py`
4. **监控系统状态**：`python3 monitor.py --once`

## 👨‍💻 开发信息

**开发者**：Bin Liu (bliu3@cisco.com)  
**版本**：v1.0  
**适用领域**：UEC文档知识管理  
**项目性质**：AI知识画廊系统

## 📞 技术支持

如需技术支持或有任何问题，请联系：
- **邮箱**：bliu3@cisco.com
- **项目**：AI知识画廊--Ask me anything about UEC v1.0

---

🎉 **享受您的多用户AI知识画廊系统！** 如有问题，请参考基础文档 [README.md](README.md) 或联系开发者。🎨