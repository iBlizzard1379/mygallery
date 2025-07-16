#!/bin/bash

# Docker镜像构建脚本
set -e

# 配置变量
IMAGE_NAME="ai-gallery"
DOCKER_HUB_USERNAME=""  # 用户需要填写自己的Docker Hub用户名
VERSION="v1.0"
LATEST_TAG="latest"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AI知识画廊 Docker镜像构建脚本 ===${NC}"
echo

# 检查Docker Hub用户名
if [ -z "$DOCKER_HUB_USERNAME" ]; then
    echo -e "${YELLOW}请编辑此脚本，设置您的Docker Hub用户名：${NC}"
    echo "DOCKER_HUB_USERNAME=\"your-username\""
    echo
    echo -e "${BLUE}注意：Docker Hub用户名只能包含小写字母、数字、下划线和连字符${NC}"
    read -p "请输入您的Docker Hub用户名 (不是邮箱): " DOCKER_HUB_USERNAME
    if [ -z "$DOCKER_HUB_USERNAME" ]; then
        echo -e "${RED}错误：Docker Hub用户名不能为空${NC}"
        exit 1
    fi
    # 验证用户名格式
    if [[ ! $DOCKER_HUB_USERNAME =~ ^[a-z0-9_-]+$ ]]; then
        echo -e "${RED}错误：Docker Hub用户名只能包含小写字母、数字、下划线和连字符${NC}"
        exit 1
    fi
fi

FULL_IMAGE_NAME="${DOCKER_HUB_USERNAME}/${IMAGE_NAME}"

echo -e "${GREEN}构建信息：${NC}"
echo "镜像名称: ${FULL_IMAGE_NAME}"
echo "版本标签: ${VERSION}"
echo "构建时间: $(date)"
echo

# 检查Podman或Docker
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    echo -e "${GREEN}使用 Podman 进行构建${NC}"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    echo -e "${GREEN}使用 Docker 进行构建${NC}"
else
    echo -e "${RED}错误：未找到 Docker 或 Podman${NC}"
    exit 1
fi

# 构建镜像
echo -e "${YELLOW}开始构建镜像...${NC}"
$CONTAINER_CMD build -t ${FULL_IMAGE_NAME}:${VERSION} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    exit 1
fi

# 添加latest标签
echo -e "${YELLOW}添加latest标签...${NC}"
$CONTAINER_CMD tag ${FULL_IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}:${LATEST_TAG}

# 显示构建的镜像
echo -e "${GREEN}构建完成的镜像：${NC}"
$CONTAINER_CMD images | grep ${FULL_IMAGE_NAME}

echo
echo -e "${GREEN}=== 构建完成 ===${NC}"
echo -e "${YELLOW}下一步：运行 ./publish-docker.sh 发布到Docker Hub${NC}"
echo
echo -e "${YELLOW}本地测试命令：${NC}"
echo "${CONTAINER_CMD} run -p 8000:8000 ${FULL_IMAGE_NAME}:${VERSION}" 