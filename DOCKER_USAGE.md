# AI知识画廊 Docker镜像使用说明

## 🐳 镜像信息

- **Docker Hub**: https://hub.docker.com/r/iblizzard1379/ai-gallery
- **镜像名称**: `iblizzard1379/ai-gallery`
- **当前版本**: `v1.2`
- **支持架构**: ARM64 (Apple Silicon), AMD64
- **镜像大小**: ~1.71GB

## 📋 环境要求

### 必需的环境变量

在运行容器前，您需要配置环境变量。项目提供了完整的`.env.docker`配置文件模板。

#### 核心必需配置：
```bash
# OpenAI API配置 (必需)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 搜索工具配置 (推荐配置至少一个)
TAVILY_API_KEY=your_tavily_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here

# 服务器配置 (可选)
PORT=8000
HOST=0.0.0.0
```

更多配置选项请参考项目中的`.env.docker`文件。

## 🚀 快速开始

### 方法1: 使用Docker Run + 环境变量文件

```bash
# 1. 拉取最新镜像
docker pull iblizzard1379/ai-gallery:v1.2

# 2. 编辑.env.docker文件，填入您的API密钥
# (项目已提供完整模板)

# 3. 运行容器
docker run -d \
  --name ai-gallery \
  -p 8000:8000 \
  --env-file .env.docker \
  -v $(pwd)/vector_db:/app/vector_db \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/images:/app/images \
  iblizzard1379/ai-gallery:v1.2
```

### 方法2: 使用Podman

```bash
# 使用Podman (替代Docker)
podman pull iblizzard1379/ai-gallery:v1.2

podman run -d \
  --name ai-gallery \
  -p 8000:8000 \
  --env-file .env.docker \
  -v $(pwd)/vector_db:/app/vector_db \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/images:/app/images \
  iblizzard1379/ai-gallery:v1.2
```

### 方法3: 使用Docker Compose (推荐)

项目已包含完整的`docker-compose.yml`配置文件：

```yaml
version: '3.8'

services:
  ai-gallery:
    image: iblizzard1379/ai-gallery:v1.2
    container_name: ai-gallery
    ports:
      - "8000:8000"
    env_file:
      - .env.docker
    volumes:
      - ./vector_db:/app/vector_db
      - ./logs:/app/logs
      - ./images:/app/images
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

运行命令：
```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f ai-gallery

# 停止服务
docker-compose down
```

## 📁 数据卷说明

推荐挂载以下目录：

- `/app/images`: 上传的图片文件存储目录
- `/app/vector_db`: 向量数据库存储
- `/app/logs`: 应用日志文件

## 🔧 配置选项

### 环境变量详解

| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | ✅ | OpenAI API密钥 | 无 |
| `OPENAI_MODEL` | ❌ | OpenAI模型名称 | gpt-4o-mini |
| `TAVILY_API_KEY` | ❌ | Tavily搜索API密钥 | 无 |
| `SERPAPI_API_KEY` | ❌ | SerpAPI搜索密钥 | 无 |
| `SEARCH_TOOL` | ❌ | 搜索工具选择 | tavily |
| `PORT` | ❌ | 服务端口 | 8000 |
| `HOST` | ❌ | 服务主机地址 | 0.0.0.0 |
| `MAX_SESSIONS` | ❌ | 最大同时会话数 | 50 |
| `SESSION_TIMEOUT_MINUTES` | ❌ | 会话超时时间(分钟) | 30 |
| `DEBUG` | ❌ | 调试模式 | false |
| `LOG_LEVEL` | ❌ | 日志级别 | INFO |

### 资源建议

- **最小内存**: 2GB RAM
- **推荐内存**: 4GB+ RAM
- **CPU**: 2核心以上
- **存储**: 10GB可用空间

## 🔍 验证部署

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs ai-gallery

# 测试服务
curl http://localhost:8000

# 访问Web界面
open http://localhost:8000
```

## 🛠️ 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker-compose logs ai-gallery
   
   # 常见原因：缺少OPENAI_API_KEY
   ```

2. **无法访问Web界面**
   ```bash
   # 检查端口映射
   docker port ai-gallery
   
   # 检查防火墙设置
   ```

3. **文档处理失败**
   ```bash
   # 确保图片目录挂载正确
   docker exec ai-gallery ls -la /app/images
   ```

### 调试模式

```bash
# 交互式运行容器进行调试
docker run -it --rm \
  --env-file .env.docker \
  iblizzard1379/ai-gallery:v1.2 \
  /bin/bash
```

## 📞 支持

- **开发者**: Bin Liu (bliu3@cisco.com)
- **项目地址**: https://github.com/your-repo/ai-gallery
- **Docker Hub**: https://hub.docker.com/r/iblizzard1379/ai-gallery

## 🔄 更新镜像

### 使用Docker Compose更新 (推荐)
```bash
# 拉取最新镜像并重启服务
docker-compose pull && docker-compose up -d
```

### 手动更新
```bash
# 停止现有容器
docker stop ai-gallery
docker rm ai-gallery

# 拉取最新镜像
docker pull iblizzard1379/ai-gallery:latest

# 重新运行容器
docker run -d \
  --name ai-gallery \
  -p 8000:8000 \
  --env-file .env.docker \
  -v $(pwd)/vector_db:/app/vector_db \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/images:/app/images \
  iblizzard1379/ai-gallery:latest
```

---

## 🏷️ 版本历史

- **v1.2**: UI响应式优化版本 (2025-07-16)
  - ✨ 优化AI助手标签和按钮的响应式定位
  - 🔧 改进聊天窗口的展开动画和位置算法
  - 📱 增强跨设备兼容性和用户体验
  - 🐛 修复多项UI定位和缩放问题

- **v1.1**: 功能增强版本 (2025-07-16)
  - 🔧 优化文档处理性能
  - 📊 改进会话管理机制
  - 🛡️ 增强系统稳定性

- **v1.0**: 初始版本发布 (2025-07-16)
  - 🎯 支持文档处理和AI问答
  - 🎨 3D画廊界面
  - 👥 多用户会话管理
  - 🗄️ 向量数据库集成 