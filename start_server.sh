#!/bin/bash

# 启动画廊服务器脚本
# 确保在虚拟环境中运行

echo "正在启动画廊服务器..."

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境 .venv 不存在"
    echo "请先运行: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "检查依赖..."
python -c "import langchain; print('✓ langchain 可用')" || {
    echo "错误: langchain 未安装"
    echo "请运行: pip install -r requirements.txt"
    exit 1
}

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，请复制 env.example 并配置"
    cp env.example .env
    echo "已创建 .env 文件，请配置您的 API 密钥"
fi

# 启动服务器
echo "启动服务器..."
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python server.py

echo "服务器已停止" 