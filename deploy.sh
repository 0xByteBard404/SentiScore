#!/bin/bash

# SentiScore 一键部署脚本
# 该脚本会检查 Docker 环境，停止正在运行的服务，删除旧镜像，然后重新构建和启动服务

echo "=== SentiScore 一键部署脚本 ==="

# 检查 Docker 是否已安装
echo "正在检查 Docker 环境..."
if ! command -v docker &> /dev/null
then
    echo "错误: 未检测到 Docker，请先安装 Docker"
    echo "请访问 https://docs.docker.com/get-docker/ 获取安装指南"
    exit 1
fi

# 检查 Docker Compose 是否已安装
if ! command -v docker-compose &> /dev/null
then
    echo "错误: 未检测到 Docker Compose，请先安装 Docker Compose"
    echo "请访问 https://docs.docker.com/compose/install/ 获取安装指南"
    exit 1
fi

echo "Docker 环境检查通过 ✓"

# 检查是否在项目根目录
if [ ! -f "docker-compose.full.yml" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 确保模型目录存在并设置正确的权限
mkdir -p models/hanlp_models
chmod 777 models/hanlp_models

# 停止正在运行的服务
echo "正在检查是否有正在运行的服务..."
if docker-compose -f docker-compose.full.yml ps | grep -q "Up"; then
    echo "检测到正在运行的服务，正在停止..."
    if docker-compose -f docker-compose.full.yml down; then
        echo "服务已停止 ✓"
    else
        echo "警告: 停止服务时出现问题"
    fi
else
    echo "没有正在运行的服务"
fi

# 删除旧的镜像（如果存在）
echo "正在检查是否存在旧的镜像..."
if docker images | grep -q "sentiscore-backend" || docker images | grep -q "sentiscore-frontend"; then
    echo "检测到旧的镜像，正在删除..."
    docker rmi sentiscore-backend:latest 2>/dev/null || true
    docker rmi sentiscore-frontend:latest 2>/dev/null || true
    echo "旧镜像已删除 ✓"
else
    echo "没有找到旧的镜像"
fi

# 重新构建并启动服务
echo "正在构建并启动服务..."
docker-compose -f docker-compose.full.yml up --build -d

if [ $? -eq 0 ]; then
    echo "服务构建并启动成功 ✓"
    echo ""
    echo "=== 部署完成 ==="
    echo "前端管理后台: http://localhost:8888"
    echo "后端API服务: http://localhost:5000"
    echo "=================="
else
    echo "错误: 服务构建或启动失败"
    exit 1
fi