#!/bin/bash

# Docker镜像发布脚本
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
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AI知识画廊 Docker镜像发布脚本 ===${NC}"
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

echo -e "${GREEN}发布信息：${NC}"
echo "镜像名称: ${FULL_IMAGE_NAME}"
echo "版本标签: ${VERSION}"
echo "发布时间: $(date)"
echo

# 检查Podman或Docker
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    echo -e "${GREEN}使用 Podman 进行发布${NC}"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    echo -e "${GREEN}使用 Docker 进行发布${NC}"
else
    echo -e "${RED}错误：未找到 Docker 或 Podman${NC}"
    exit 1
fi

# 检查镜像是否存在
if ! $CONTAINER_CMD image exists ${FULL_IMAGE_NAME}:${VERSION}; then
    echo -e "${RED}错误：镜像 ${FULL_IMAGE_NAME}:${VERSION} 不存在${NC}"
    echo -e "${YELLOW}请先运行 ./build-docker.sh 构建镜像${NC}"
    exit 1
fi

# 登录Docker Hub
echo -e "${YELLOW}登录Docker Hub...${NC}"
echo -e "${BLUE}请输入您的Docker Hub凭据：${NC}"
$CONTAINER_CMD login docker.io

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Docker Hub登录失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Hub登录成功${NC}"

# 推送镜像
echo -e "${YELLOW}推送镜像到Docker Hub...${NC}"
echo "推送 ${FULL_IMAGE_NAME}:${VERSION}..."
$CONTAINER_CMD push ${FULL_IMAGE_NAME}:${VERSION}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 版本镜像推送成功${NC}"
else
    echo -e "${RED}✗ 版本镜像推送失败${NC}"
    exit 1
fi

echo "推送 ${FULL_IMAGE_NAME}:${LATEST_TAG}..."
$CONTAINER_CMD push ${FULL_IMAGE_NAME}:${LATEST_TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Latest镜像推送成功${NC}"
else
    echo -e "${RED}✗ Latest镜像推送失败${NC}"
    exit 1
fi

echo
echo -e "${GREEN}=== 发布完成 ===${NC}"
echo -e "${GREEN}镜像已成功发布到Docker Hub！${NC}"
echo
echo -e "${YELLOW}访问链接：${NC}"
echo "https://hub.docker.com/r/${DOCKER_HUB_USERNAME}/${IMAGE_NAME}"
echo
echo -e "${YELLOW}使用命令：${NC}"
echo "${CONTAINER_CMD} pull ${FULL_IMAGE_NAME}:${VERSION}"
echo "${CONTAINER_CMD} run -p 8000:8000 ${FULL_IMAGE_NAME}:${VERSION}"
echo
echo -e "${BLUE}Docker Hub页面将在几分钟后更新镜像信息${NC}" 