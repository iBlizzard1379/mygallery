# 完整功能Docker镜像 - 包含所有功能
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    PATH=/root/.local/bin:$PATH

# 完整系统依赖（但仍然优化过的）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 完整OCR支持
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng \
    # EasyOCR需要的额外依赖
    libglib2.0-0 \
    libgomp1 \
    libgl1-mesa-glx \
    # 网络工具
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

WORKDIR /app

# 安装uv包管理器
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY requirements-docker-build.txt ./

# 安装Python依赖
RUN uv pip install --system --no-cache -r requirements-docker-build.txt

# 复制项目文件
COPY . .

# 创建目录
RUN mkdir -p vector_db logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "server.py"] 