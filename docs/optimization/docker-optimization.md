# AI知识画廊 Docker镜像优化指南

## 🎯 优化概述

本项目已完成Docker镜像大小优化，从原来的 **1.71GB** 减少到不同功能级别的镜像：

| 镜像类型 | 大小估计 | 节省空间 | 功能描述 |
|---------|---------|---------|----------|
| **Minimal** | ~600MB | 65% | 核心AI功能：PDF处理、基础OCR、RAG问答 |
| **Standard** | ~950MB | 44% | 平衡配置：多格式文档、轻量级OCR、搜索工具 |
| **Full** | ~1.2GB | 30% | 完整功能：所有文档格式、高级OCR、完整搜索 |

## 🛠️ 优化措施

### 1. 系统依赖优化
- ❌ 移除 `libgdal-dev` (500MB+) - 地理信息处理
- ❌ 移除 `ffmpeg` (100MB+) - 视频处理
- ❌ 移除 `wget` - 已有curl替代
- ❌ 移除GUI相关库 - 服务器环境不需要

### 2. Python依赖优化
- 🔄 用 `openpyxl` 替代 `pandas` 处理Excel
- 🔄 选择性安装OCR：`pytesseract` (轻量) vs `easyocr` (功能强)
- ❌ 移除 `google-search-results` - 保留 `tavily-python`
- ✅ 保留所有核心LangChain和AI功能

### 3. 多阶段构建
- 🏗️ 构建阶段：安装依赖
- 🚀 运行阶段：仅复制必要文件
- 📦 减少镜像层数和临时文件

## 🚀 使用方法

### 方法1: 使用优化构建脚本（推荐）

```bash
# 查看帮助
./scripts/build-optimized.sh --help

# 构建不同类型的镜像
./scripts/build-optimized.sh minimal    # 最小化镜像
./scripts/build-optimized.sh standard   # 标准镜像（默认）
./scripts/build-optimized.sh full      # 完整功能镜像

# 高级选项
./scripts/build-optimized.sh standard --tag v2.0 --no-cache
```

### 方法2: 直接使用Docker命令

```bash
# 标准镜像（推荐）
docker build -t ai-gallery:optimized .

# 最小化镜像
docker build -f Dockerfile.minimal -t ai-gallery:minimal .

# 完整功能镜像
docker build -f Dockerfile -t ai-gallery:full .
```

### 方法3: 使用Docker Compose

```bash
# 标准版本
docker-compose up -d ai-gallery

# 最小化版本
docker-compose --profile minimal up -d ai-gallery-minimal

# 完整功能版本
docker-compose --profile full up -d ai-gallery-full
```

## 📋 依赖配置选择

项目提供了多个依赖配置文件，您可以根据需要选择：

### `requirements-core.txt` - 核心功能
- LangChain + OpenAI
- FAISS向量数据库
- 基础PDF处理
- 系统监控

### `requirements-minimal.txt` - 最小化
- 核心功能 +
- 轻量级OCR (pytesseract)
- 基础Office文档处理
- 文件监控

### `requirements-docker-build.txt` - 完整功能
- 最小化功能 +
- 高级OCR (easyocr)
- 完整Office文档处理
- 互联网搜索工具

### `requirements.txt` - 标准配置
- 平衡功能与大小的推荐配置

## 🔧 功能对比

| 功能 | Minimal | Standard | Full |
|------|---------|----------|------|
| **AI问答** | ✅ | ✅ | ✅ |
| **PDF处理** | ✅ | ✅ | ✅ |
| **Word文档** | ❌ | ✅ | ✅ |
| **Excel表格** | ❌ | ✅ (openpyxl) | ✅ (pandas) |
| **PPT演示** | ❌ | ✅ | ✅ |
| **图像OCR** | ❌ | ✅ (pytesseract) | ✅ (easyocr) |
| **中文OCR** | ❌ | ✅ | ✅ |
| **互联网搜索** | ❌ | ✅ (tavily) | ✅ (full) |
| **文件监控** | ❌ | ✅ | ✅ |
| **系统监控** | ✅ | ✅ | ✅ |

## 🎯 选择建议

### 🟢 推荐：Standard镜像
- **适用场景**：大多数生产环境
- **优点**：功能完善，大小合理
- **包含**：所有文档格式、基础OCR、搜索功能

### 🔵 开发/测试：Minimal镜像
- **适用场景**：开发环境、CI/CD、资源受限环境
- **优点**：启动快、占用少
- **包含**：核心AI功能、PDF处理

### 🟠 特殊需求：Full镜像
- **适用场景**：需要最佳OCR效果、复杂文档处理
- **优点**：功能最全、OCR效果最好
- **包含**：所有功能、高级OCR、完整搜索

## 🔄 迁移指南

### 从原版本迁移

1. **备份数据**：
```bash
cp -r vector_db vector_db.backup
cp .env .env.backup
```

2. **选择镜像类型**：
```bash
# 评估功能需求，选择合适的镜像类型
./scripts/build-optimized.sh standard
```

3. **测试功能**：
```bash
# 启动新镜像
docker-compose up -d

# 验证功能正常
curl http://localhost:8000/
```

4. **性能验证**：
```bash
# 检查镜像大小
docker images ai-gallery

# 检查运行内存
docker stats ai-gallery
```

## 📊 性能对比

### 构建时间
- Minimal: ~5-8分钟
- Standard: ~8-12分钟  
- Full: ~12-18分钟

### 运行内存
- Minimal: ~500MB-1GB
- Standard: ~1-2GB
- Full: ~1.5-3GB

### 启动时间
- Minimal: ~10-15秒
- Standard: ~15-25秒
- Full: ~20-35秒

## 🚨 注意事项

1. **功能差异**：选择Minimal镜像前确认功能需求
2. **OCR语言**：Minimal版本不支持中文OCR
3. **搜索功能**：Minimal版本不包含互联网搜索
4. **文档格式**：Minimal版本仅支持PDF

## 🛟 故障排除

### 构建失败
```bash
# 清理构建缓存
docker system prune -f

# 使用无缓存构建
./scripts/build-optimized.sh standard --no-cache
```

### 功能缺失
```bash
# 检查选择的镜像类型
docker inspect ai-gallery | grep -i image

# 切换到Full镜像
./scripts/build-optimized.sh full
docker-compose down
docker-compose --profile full up -d ai-gallery-full
```

### 性能问题
```bash
# 监控资源使用
docker stats

# 检查日志
docker logs ai-gallery
```

---

## 📞 支持

如有问题，请参考：
- [README.md](README.md) - 基础使用说明
- [README_DEPLOYMENT.md](README_DEPLOYMENT.md) - 部署指南
- [Issues](../../issues) - 问题反馈 