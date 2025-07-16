#!/bin/bash

# AI知识画廊 Docker 本地测试脚本
# 使用方法：./test-docker-local.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

IMAGE_NAME="iblizzard1379/ai-gallery:v1.0"
CONTAINER_NAME="ai-gallery-test"

echo -e "${GREEN}=== AI知识画廊 Docker 本地测试 ===${NC}"
echo

# 检查容器运行时
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    echo -e "${GREEN}使用 Podman 进行测试${NC}"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    echo -e "${GREEN}使用 Docker 进行测试${NC}"
else
    echo -e "${RED}错误：未找到 Docker 或 Podman${NC}"
    exit 1
fi

# 清理旧容器
echo -e "${YELLOW}清理旧的测试容器...${NC}"
$CONTAINER_CMD stop $CONTAINER_NAME 2>/dev/null || true
$CONTAINER_CMD rm $CONTAINER_NAME 2>/dev/null || true

# 检查环境变量文件
if [ ! -f ".env.docker" ]; then
    echo -e "${RED}错误：未找到 .env.docker 文件${NC}"
    echo -e "${YELLOW}请先运行：cp docker-test-env.example .env.docker${NC}"
    echo -e "${YELLOW}然后编辑 .env.docker 文件，填入您的真实API密钥${NC}"
    exit 1
fi

# 检查API密钥是否已配置
if grep -q "your_openai_api_key_here" .env.docker; then
    echo -e "${RED}警告：检测到默认API密钥，请编辑 .env.docker 文件${NC}"
    echo -e "${YELLOW}将 'your_openai_api_key_here' 替换为您的真实OpenAI API密钥${NC}"
    echo
    read -p "是否继续测试 (容器可能无法正常启动)？ [y/N]: " confirm
    if [[ $confirm != [yY] ]]; then
        exit 1
    fi
fi

# 创建测试目录
echo -e "${YELLOW}创建测试目录...${NC}"
mkdir -p ./test-documents ./test-vector-db ./test-logs

# 方法1: 使用环境变量文件运行
echo -e "${BLUE}=== 方法1: 使用环境变量文件运行 ===${NC}"
echo "运行命令："
echo "$CONTAINER_CMD run -d \\"
echo "  --name $CONTAINER_NAME \\"
echo "  -p 8000:8000 \\"
echo "  --env-file .env.docker \\"
echo "  -v \$(pwd)/test-documents:/app/documents \\"
echo "  -v \$(pwd)/test-vector-db:/app/vector_db \\"
echo "  -v \$(pwd)/test-logs:/app/logs \\"
echo "  $IMAGE_NAME"
echo

$CONTAINER_CMD run -d \
  --name $CONTAINER_NAME \
  -p 8000:8000 \
  --env-file .env.docker \
  -v $(pwd)/test-documents:/app/documents \
  -v $(pwd)/test-vector-db:/app/vector_db \
  -v $(pwd)/test-logs:/app/logs \
  $IMAGE_NAME

echo -e "${GREEN}✓ 容器已启动${NC}"

# 等待容器启动
echo -e "${YELLOW}等待容器启动...${NC}"
sleep 10

# 检查容器状态
echo -e "${BLUE}=== 容器状态检查 ===${NC}"
$CONTAINER_CMD ps | grep $CONTAINER_NAME || echo -e "${RED}容器未运行${NC}"

# 显示日志
echo -e "${BLUE}=== 容器启动日志 ===${NC}"
$CONTAINER_CMD logs $CONTAINER_NAME

# 测试服务响应
echo -e "${BLUE}=== 服务测试 ===${NC}"
echo "测试服务响应..."
if curl -f -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✓ 服务响应正常${NC}"
    echo "您可以在浏览器中访问: http://localhost:8000"
else
    echo -e "${RED}✗ 服务响应失败${NC}"
    echo "请检查容器日志了解详情"
fi

echo
echo -e "${BLUE}=== 测试命令 ===${NC}"
echo "查看容器状态: $CONTAINER_CMD ps"
echo "查看容器日志: $CONTAINER_CMD logs $CONTAINER_NAME"
echo "进入容器调试: $CONTAINER_CMD exec -it $CONTAINER_NAME /bin/bash"
echo "停止容器: $CONTAINER_CMD stop $CONTAINER_NAME"
echo "删除容器: $CONTAINER_CMD rm $CONTAINER_NAME"
echo
echo -e "${GREEN}测试完成！${NC}" 