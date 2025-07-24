# AI知识画廊

> 🚀 **新版本优化**: Docker镜像已优化，从1.71GB减少到600MB-1.2GB！

一个集成AI智能问答功能的3D虚拟画廊系统。

## ✨ 核心特性

- �� 3D虚拟画廊
- 🤖 AI智能问答  
- 👥 多用户并发
- 📊 系统监控

## 🚀 快速开始

### Docker部署（推荐）

```bash
git clone <项目地址>
cd mygallery
./scripts/build-optimized.sh standard
docker-compose up -d
```

### 传统部署

```bash
git clone <项目地址>
cd mygallery
cp env.example .env
uv run python server.py
```

## 📚 详细文档

- [Docker部署指南](docs/deployment/docker.md)
- [生产环境部署](docs/deployment/production.md)  
- [测试指南](docs/deployment/testing.md)
- [Docker优化指南](docs/optimization/docker-optimization.md)
- [性能优化](docs/optimization/performance.md)
- [API参考](docs/api/reference.md)

## 🎮 使用指南

- **画廊导航**: WASD移动，鼠标控制视角
- **文档交互**: 点击画框查看内容
- **AI问答**: 使用右侧聊天功能

## 🔧 配置

详细配置说明请参考 [部署文档](docs/deployment/)。

## 🧪 测试

性能测试和故障排除请参考 [测试指南](docs/deployment/testing.md)。

