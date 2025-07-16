# AI知识画廊 Docker镜像使用说明

## 🐳 镜像信息

- **Docker Hub**: https://hub.docker.com/r/iblizzard1379/ai-gallery
- **镜像名称**: `iblizzard1379/ai-gallery`
- **支持架构**: ARM64 (Apple Silicon), AMD64
- **镜像大小**: ~1.67GB

## 📋 环境要求

### 必需的环境变量

在运行容器前，您需要创建一个`.env`文件或设置环境变量：

```bash
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# 搜索工具配置 (可选)
TAVILY_API_KEY=your_tavily_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here

# 服务器配置 (可选)
PORT=8000
```

## 🚀 快速开始

### 方法1: 使用Docker Run

```bash
# 1. 拉取镜像
docker pull iblizzard1379/ai-gallery:v1.0

# 2. 创建.env文件
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
PORT=8000
EOF

# 3. 运行容器
docker run -d \
  --name ai-gallery \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/documents:/app/documents \
  -v $(pwd)/vector_db:/app/vector_db \
  iblizzard1379/ai-gallery:v1.0
```

### 方法2: 使用Podman

```bash
# 使用Podman (替代Docker)
podman pull iblizzard1379/ai-gallery:v1.0

podman run -d \
  --name ai-gallery \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/documents:/app/documents \
  -v $(pwd)/vector_db:/app/vector_db \
  iblizzard1379/ai-gallery:v1.0
```

### 方法3: 使用Docker Compose

创建`docker-compose.yml`文件：

```yaml
version: '3.8'

services:
  ai-gallery:
    image: iblizzard1379/ai-gallery:v1.0
    container_name: ai-gallery
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - PORT=8000
    volumes:
      - ./documents:/app/documents
      - ./vector_db:/app/vector_db
      - ./logs:/app/logs
    restart: unless-stopped
```

然后运行：
```bash
docker-compose up -d
```

## 📁 数据卷说明

推荐挂载以下目录：

- `/app/documents`: 文档存储目录
- `/app/vector_db`: 向量数据库存储
- `/app/logs`: 日志文件

## 🔧 配置选项

### 环境变量详解

| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | ✅ | OpenAI API密钥 | 无 |
| `TAVILY_API_KEY` | ❌ | Tavily搜索API密钥 | 无 |
| `SERPAPI_API_KEY` | ❌ | SerpAPI搜索密钥 | 无 |
| `PORT` | ❌ | 服务端口 | 8000 |

### 资源建议

- **最小内存**: 2GB RAM
- **推荐内存**: 4GB+ RAM
- **CPU**: 2核心以上
- **存储**: 10GB可用空间

## 🔍 验证部署

```bash
# 检查容器状态
docker ps

# 查看日志
docker logs ai-gallery

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
   docker logs ai-gallery
   
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
   # 确保文档目录挂载正确
   docker exec ai-gallery ls -la /app/documents
   ```

### 调试模式

```bash
# 交互式运行容器进行调试
docker run -it --rm \
  --env-file .env \
  iblizzard1379/ai-gallery:v1.0 \
  /bin/bash
```

## 📞 支持

- **开发者**: Bin Liu (bliu3@cisco.com)
- **项目地址**: https://github.com/your-repo/ai-gallery
- **Docker Hub**: https://hub.docker.com/r/iblizzard1379/ai-gallery

## 🔄 更新镜像

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
  --env-file .env \
  -v $(pwd)/documents:/app/documents \
  -v $(pwd)/vector_db:/app/vector_db \
  iblizzard1379/ai-gallery:latest
```

---

## 🏷️ 版本历史

- **v1.0**: 初始版本发布 (2025-07-16)
  - 支持文档处理和AI问答
  - 3D画廊界面
  - 多用户会话管理
  - 向量数据库集成 