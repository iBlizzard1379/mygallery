#!/bin/bash

# AI知识画廊 优化构建脚本
# 支持不同级别的Docker镜像构建

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "AI知识画廊 优化构建脚本"
    echo ""
    echo "用法: $0 [选项] [构建类型]"
    echo ""
    echo "构建类型:"
    echo "  minimal    - 最小化镜像 (~600MB, 仅核心AI功能)"
    echo "  standard   - 标准镜像 (~950MB, 平衡功能与大小)"
    echo "  full       - 完整镜像 (~1.2GB, 包含所有功能)"
    echo ""
    echo "选项:"
    echo "  --no-cache    - 不使用构建缓存"
    echo "  --push        - 构建后推送到Docker Hub"
    echo "  --tag TAG     - 指定镜像标签"
    echo "  --help        - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 standard                    # 构建标准镜像"
    echo "  $0 minimal --tag v2.0          # 构建最小化镜像并指定标签"
    echo "  $0 full --no-cache --push      # 无缓存构建完整镜像并推送"
}

# 默认参数
BUILD_TYPE="standard"
USE_CACHE="--cache"
PUSH_IMAGE=false
IMAGE_TAG="optimized"
BASE_NAME="ai-gallery"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        minimal|standard|full)
            BUILD_TYPE="$1"
            shift
            ;;
        --no-cache)
            USE_CACHE="--no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 设置构建配置
case $BUILD_TYPE in
    minimal)
        DOCKERFILE="Dockerfile.standard.minimal"
        FULL_IMAGE_NAME="$BASE_NAME:minimal-$IMAGE_TAG"
        log_info "构建最小化镜像 (~600MB)"
        ;;
    standard)
        DOCKERFILE="Dockerfile.standard"
        FULL_IMAGE_NAME="$BASE_NAME:$IMAGE_TAG"
        log_info "构建标准镜像 (~950MB)"
        ;;
    full)
        DOCKERFILE="Dockerfile.standard.full"
        FULL_IMAGE_NAME="$BASE_NAME:full-$IMAGE_TAG"
        log_info "构建完整功能镜像 (~1.2GB)"
        ;;
esac

# 检查必要文件
log_info "检查构建文件..."
if [ ! -f "$DOCKERFILE" ]; then
    log_error "未找到Dockerfile.standard: $DOCKERFILE"
    exit 1
fi

# 显示构建信息
log_info "构建配置:"
log_info "  构建类型: $BUILD_TYPE"
log_info "  Dockerfile.standard: $DOCKERFILE"
log_info "  镜像名称: $FULL_IMAGE_NAME"
log_info "  缓存选项: $USE_CACHE"

# 开始构建
log_info "开始构建Docker镜像..."
if [ "$USE_CACHE" = "--no-cache" ]; then
    docker build --no-cache -f "$DOCKERFILE" -t "$FULL_IMAGE_NAME" .
else
    docker build -f "$DOCKERFILE" -t "$FULL_IMAGE_NAME" .
fi

if [ $? -eq 0 ]; then
    log_info "镜像构建成功!"
    
    # 显示镜像信息
    IMAGE_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
    log_info "镜像大小: $IMAGE_SIZE"
    
    # 推送镜像（如果需要）
    if [ "$PUSH_IMAGE" = true ]; then
        log_info "推送镜像到Docker Hub..."
        docker push "$FULL_IMAGE_NAME"
    fi
    
    # 提供运行命令
    echo ""
    log_info "运行命令:"
    echo "docker run -d --name ai-gallery-$BUILD_TYPE -p 8000:8000 --env-file .env $FULL_IMAGE_NAME"
    echo ""
    log_info "或使用Docker Compose:"
    case $BUILD_TYPE in
        minimal)
            echo "docker-compose --profile minimal up -d ai-gallery-minimal"
            ;;
        standard)
            echo "docker-compose up -d ai-gallery"
            ;;
        full)
            echo "docker-compose --profile full up -d ai-gallery-full"
            ;;
    esac
    
else
    log_error "镜像构建失败!"
    exit 1
fi 