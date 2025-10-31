# 仅后端服务的Docker配置
# 注意：此配置文件仅用于构建后端服务镜像
# 如需同时部署前端和后端，请使用 docker-compose.full.yml
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
COPY backend/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码文件
COPY backend/app.py backend/config.py ./
COPY backend/src/ src/

# 创建缓存目录
RUN mkdir -p /app/.cemotion_cache /app/.cache/modelscope

# 设置环境变量指向持久化缓存目录
ENV MODEL_CACHE_DIR=/app/.cemotion_cache
ENV MODELSCOPE_CACHE_DIR=/app/.cache/modelscope
ENV MODELSCOPE_CACHE_HOME=/app/.cache/modelscope
ENV PYTHONPATH=/app

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false
ENV LOG_LEVEL=INFO

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令（使用 gunicorn 以适配生产环境）
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "2", "-t", "60", "-b", "0.0.0.0:5000", "app:app"]