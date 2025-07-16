# 使用Python 3.12作为基础镜像（3.13可能还未稳定发布）
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# 安装系统依赖（OCR和图像处理需要）
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgdal-dev \
    curl \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 安装uv包管理器
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY requirements.txt pyproject.toml ./

# 安装Python依赖
RUN uv pip install --system --no-cache -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p vector_db logs

# 设置权限
RUN chmod +x start_server.sh || true

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["python", "server.py"] 