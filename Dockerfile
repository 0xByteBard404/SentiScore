FROM python:3.11-slim

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建src目录
RUN mkdir -p /app/src

# 复制代码文件
COPY app.py config.py /app/
COPY src/ /app/src/

# 创建缓存目录
RUN mkdir -p .cemotion_cache

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false
ENV LOG_LEVEL=INFO
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["python", "app.py"]
