# AI知识画廊 Docker 本地测试完整指南

## 🎯 测试目标

本地测试Docker镜像的目的是验证：
- ✅ 容器能否正常启动
- ✅ 环境变量是否正确传递
- ✅ 服务端口是否可访问
- ✅ API连接是否工作
- ✅ 文档处理功能是否正常

## 📋 测试前准备

### 1. 确保容器运行时可用
```bash
# 检查Docker或Podman
docker --version
# 或
podman --version
```

### 2. 准备API密钥
- OpenAI API Key (必需): https://platform.openai.com/api-keys
- Tavily API Key (可选): https://tavily.com/
- SerpAPI Key (可选): https://serpapi.com/

## 🚀 快速测试方法

### 方法1: 使用测试脚本 (推荐)

1. **配置环境变量**:
```bash
# 复制环境变量模板
cp docker-test-env.example .env.docker

# 编辑并填入真实的API密钥
nano .env.docker
# 或
code .env.docker
```

2. **运行自动化测试**:
```bash
./test-docker-local.sh
```

### 方法2: 手动测试步骤

1. **创建环境变量文件**:
```bash
cat > .env.docker << 'EOF'
OPENAI_API_KEY=your_actual_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
PORT=8000
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
EOF
```

2. **创建数据目录**:
```bash
mkdir -p ./documents ./vector_db ./logs
```

3. **启动容器**:
```bash
# 使用Podman
podman run -d \
  --name ai-gallery-test \
  -p 8000:8000 \
  --env-file .env.docker \
  -v $(pwd)/documents:/app/documents \
  -v $(pwd)/vector_db:/app/vector_db \
  -v $(pwd)/logs:/app/logs \
  iblizzard1379/ai-gallery:v1.0

# 或使用Docker
docker run -d \
  --name ai-gallery-test \
  -p 8000:8000 \
  --env-file .env.docker \
  -v $(pwd)/documents:/app/documents \
  -v $(pwd)/vector_db:/app/vector_db \
  -v $(pwd)/logs:/app/logs \
  iblizzard1379/ai-gallery:v1.0
```

4. **检查容器状态**:
```bash
# 查看运行状态
podman ps

# 查看启动日志
podman logs ai-gallery-test

# 检查资源使用
podman stats --no-stream ai-gallery-test
```

5. **测试服务**:
```bash
# 测试HTTP响应
curl -I http://localhost:8000/

# 在浏览器中打开
open http://localhost:8000
```

## 🔍 日志分析指南

### 正常启动日志特征
```
INFO:__main__:Starting server on port 8000...
INFO:document_processors.enhanced_document_processor:使用OpenAI嵌入模型
INFO:rag_chain:成功创建工具调用代理
```

### 常见错误和解决方案

#### 1. API密钥错误
**错误信息**:
```
ERROR code: 401 - Incorrect API key provided
```
**解决方案**: 检查并更新`.env.docker`文件中的`OPENAI_API_KEY`

#### 2. 端口冲突
**错误信息**:
```
bind: address already in use
```
**解决方案**: 更改端口映射 `-p 8001:8000` 或停止占用8000端口的进程

#### 3. 向量数据库初始化失败
**错误信息**:
```
ERROR:document_processors.enhanced_document_processor:初始化向量数据库失败
```
**解决方案**: 确保API密钥有效且有足够的配额

#### 4. 文档处理失败
**错误信息**:
```
ERROR:向量数据库未初始化，无法处理文档
```
**解决方案**: 检查API密钥和网络连接

## 🧪 测试场景

### 场景1: 基础功能测试
```bash
# 测试Web界面
curl http://localhost:8000/

# 测试健康检查
curl http://localhost:8000/health
```

### 场景2: AI问答测试
```bash
# 通过API测试聊天功能
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}'
```

### 场景3: 文档上传测试
1. 在浏览器中访问 http://localhost:8000
2. 使用文档上传功能
3. 检查向量数据库是否更新

## 🛠️ 调试技巧

### 1. 进入容器调试
```bash
# 进入运行中的容器
podman exec -it ai-gallery-test /bin/bash

# 查看文件系统
ls -la /app/
cat /app/.env

# 查看Python进程
ps aux | grep python
```

### 2. 实时查看日志
```bash
# 实时跟踪日志
podman logs -f ai-gallery-test

# 只查看错误日志
podman logs ai-gallery-test 2>&1 | grep ERROR
```

### 3. 网络诊断
```bash
# 检查端口监听
netstat -tulpn | grep 8000

# 测试容器内网络
podman exec ai-gallery-test curl localhost:8000
```

## 🧹 清理和重置

### 停止和删除容器
```bash
# 停止容器
podman stop ai-gallery-test

# 删除容器
podman rm ai-gallery-test

# 一键停止并删除
podman rm -f ai-gallery-test
```

### 清理数据
```bash
# 清理测试数据
rm -rf ./documents ./vector_db ./logs .env.docker

# 清理镜像 (谨慎操作)
podman rmi iblizzard1379/ai-gallery:v1.0
```

## 📊 性能基准

### 正常资源使用范围
- **内存**: 100-300MB (空闲状态)
- **CPU**: 1-10% (空闲状态)
- **启动时间**: 10-30秒
- **响应时间**: < 2秒 (首次访问)

### 性能测试命令
```bash
# 内存使用
podman stats --no-stream ai-gallery-test | grep MEM

# 响应时间测试
time curl http://localhost:8000/

# 并发测试 (需要安装ab)
ab -n 100 -c 10 http://localhost:8000/
```

## 💡 最佳实践

1. **始终使用环境变量文件**，不要在命令行中直接暴露API密钥
2. **定期检查日志**，及时发现和解决问题
3. **使用数据卷**，确保数据持久化
4. **设置资源限制**，防止容器消耗过多系统资源
5. **定期更新镜像**，获取最新的功能和安全修复

## 🆘 获取帮助

如果遇到问题：
1. 查看本地日志: `podman logs ai-gallery-test`
2. 检查环境变量: `podman exec ai-gallery-test env`
3. 联系开发者: bliu3@cisco.com
4. 查看Docker Hub: https://hub.docker.com/r/iblizzard1379/ai-gallery 