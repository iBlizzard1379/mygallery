# AI知识画廊--Ask me anything about UEC v1.0

一个集成AI智能问答功能的3D虚拟画廊系统，支持多用户并发访问，智能展示和处理多种格式的文档。

## ✨ 核心特性

### 🎨 3D虚拟画廊
- **沉浸式体验**：长廊式画廊布局，模仿真实美术馆展示效果
- **智能布局**：文档按编号交替显示在左右墙面，奇数文档在左墙，偶数文档在右墙
- **专业照明**：每个画框都配备聚光灯照明系统
- **第一人称控制**：自由移动和观看，支持WASD移动和鼠标视角控制
- **多格式支持**：智能显示PDF、Word、Excel、PowerPoint等文档格式

### 🤖 AI智能问答
- **RAG检索增强**：基于文档内容的智能问答系统
- **多模态处理**：支持文本、图片、表格等多种内容类型
- **实时对话**：即时响应用户问题，提供准确的文档信息
- **上下文理解**：维持对话上下文，支持追问和深入讨论

### 👥 多用户并发
- **会话隔离**：每个用户拥有独立的聊天会话和上下文
- **线程安全**：所有共享资源经过线程安全处理
- **资源管理**：智能管理向量数据库和AI模型资源
- **自动清理**：过期会话自动清理，防止内存泄漏

### 📊 系统监控
- **实时监控**：CPU、内存、会话状态实时监控
- **管理面板**：Web界面查看系统健康度和性能指标
- **性能测试**：内置并发测试工具验证系统稳定性

## 🚀 快速开始

### 前置要求
- Python 3.8+
- uv 包管理工具
- OpenAI API Key

### 1. 安装uv工具
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 或 source ~/.zshrc
```

### 2. 克隆项目
```bash
git clone <项目地址>
cd mygallery
```

### 3. 配置环境
```bash
# 复制环境变量示例文件
cp env.example .env

# 编辑.env文件，添加你的API密钥
# OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 启动系统
```bash
# 开发环境快速启动
uv run python server.py

# 或使用部署脚本（推荐生产环境）
./deploy_intranet.sh

# 或使用简单启动脚本
./start_server.sh
```

### 5. 访问应用
- **主画廊**：`http://localhost:8000`
- **管理面板**：`http://localhost:8000/admin`
- **聊天界面**：`http://localhost:8000/chatbot`

## 🎮 使用指南

### 画廊导航
- **W / ↑** - 前进
- **S / ↓** - 后退  
- **A / ←** - 左移
- **D / →** - 右移
- **鼠标** - 点击激活视角控制，移动鼠标转动视角
- **ESC** - 退出视角控制/关闭浏览器

### 文档交互
- **点击文档画框** - 查看文档详细内容
- **PDF预览** - 支持全页面滚动浏览
- **文档下载** - 点击下载按钮获取原文件
- **智能问答** - 使用右侧聊天功能询问文档相关问题

### AI问答功能
- **文档查询**：询问任何文档相关问题
- **内容搜索**：基于文档内容的智能检索
- **实时对话**：支持多轮对话和上下文理解
- **示例问题**：
  - "UE规范的主要内容是什么？"
  - "第3章讲了哪些技术要点？"
  - "软件层和网络层有什么区别？"

## 🏗️ 技术架构

### 前端技术
- **Three.js**：3D场景渲染和交互
- **JavaScript ES6+**：现代JavaScript特性
- **CSS3**：响应式设计和动画效果
- **PDF.js**：PDF文档在线预览

### 后端技术
- **Python 3.8+**：服务器端语言
- **FastAPI/HTTP.server**：Web服务框架
- **LangChain**：AI应用开发框架
- **OpenAI GPT**：大语言模型
- **FAISS**：向量数据库用于相似性搜索

### AI能力
- **RAG检索增强生成**：结合文档检索和生成式AI
- **向量化存储**：文档内容智能索引和检索
- **多模态处理**：文本、表格、图片内容理解
- **上下文管理**：维持对话状态和会话隔离

### 系统特性
- **多用户并发**：支持50+用户同时访问
- **会话管理**：独立会话隔离和自动清理
- **资源管理**：智能资源分配和缓存
- **监控告警**：实时系统健康监控

## 📁 文档管理

### 添加文档
1. 将PDF、Word、Excel、PowerPoint文件放入 `images/` 目录
2. 文档会自动被处理并添加到向量数据库
3. 文档按文件名开头数字自动排序显示
4. 奇数编号文档显示在左墙，偶数编号文档显示在右墙

### 支持格式
- **PDF文档** (.pdf)
- **Word文档** (.doc, .docx)
- **Excel表格** (.xls, .xlsx)  
- **PowerPoint演示** (.ppt, .pptx)
- **图片文件** (.jpg, .png, .gif等)

## 🔧 高级配置

### 环境变量
```bash
# AI配置
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini

# 多用户配置
MAX_SESSIONS=50
SESSION_TIMEOUT_MINUTES=30

# 服务器配置
PORT=8000
HOST=0.0.0.0
```

### 性能调优
```bash
# 并发测试
python test_concurrent.py --users 20 --requests 5

# 系统监控
python monitor.py

# 管理面板
访问 http://localhost:8000/admin
```

## 🧪 测试和监控

### 并发测试
```bash
# 基本测试
python test_concurrent.py

# 高并发测试
python test_concurrent.py --users 30 --requests 10

# 查看会话统计
python test_concurrent.py --stats-only
```

### 系统监控
```bash
# 启动监控
python monitor.py

# 一次性检查
python monitor.py --once
```

## 📋 部署指南

详细的生产环境部署说明请参考：[README_DEPLOYMENT.md](README_DEPLOYMENT.md)

包含：
- 内网多用户部署
- 性能优化配置
- 监控告警设置
- 故障排除指南

## 👨‍💻 开发信息

**开发者**：Bin Liu (bliu3@cisco.com)  
**版本**：v1.0  
**适用领域**：UEC文档知识管理

## 📄 许可证

本项目基于开源许可证发布，详见 [LICENSE](LICENSE) 文件。

---

🎉 **享受您的AI知识画廊体验！** 如有问题，请查看部署文档或联系开发者。 