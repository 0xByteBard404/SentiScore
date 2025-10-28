FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到用户目录
RUN pip install --user -r requirements.txt

# 多阶段构建：运行阶段
FROM python:3.11-slim

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的依赖
COPY --from=builder /root/.local /root/.local

# 确保pip已安装的包在PATH中
ENV PATH=/root/.local/bin:$PATH

# 复制代码文件
COPY app.py config.py ./
COPY src/ src/

# 创建缓存目录
RUN mkdir -p /app/.cemotion_cache /app/.cache/modelscope

# 设置环境变量指向持久化缓存目录
ENV MODEL_CACHE_DIR=/app/.cemotion_cache
ENV MODELSCOPE_CACHE_DIR=/app/.cache/modelscope

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

# 启动命令
CMD ["python", "app.py"]
