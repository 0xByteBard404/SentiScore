#!/bin/bash

# SentiScore 一键部署脚本
# 该脚本会检查 Docker 环境，停止正在运行的服务，删除旧镜像，然后重新构建和启动服务

set -e  # 遇到错误立即退出

echo "=== SentiScore 一键部署脚本 ==="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否已安装
log_info "正在检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    log_error "未检测到 Docker，请先安装 Docker"
    echo "请访问 https://docs.docker.com/get-docker/ 获取安装指南"
    exit 1
fi

# 检查 Docker Compose 是否已安装
if ! command -v docker-compose &> /dev/null; then
    log_error "未检测到 Docker Compose，请先安装 Docker Compose"
    echo "请访问 https://docs.docker.com/compose/install/ 获取安装指南"
    exit 1
fi

# 显示 Docker 版本信息
DOCKER_VERSION=$(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',')
DOCKER_COMPOSE_VERSION=$(docker-compose --version 2>/dev/null | cut -d' ' -f3 | tr -d ',')
log_info "Docker 版本: $DOCKER_VERSION"
log_info "Docker Compose 版本: $DOCKER_COMPOSE_VERSION"

log_success "Docker 环境检查通过"

# 检查是否在项目根目录
if [ ! -f "docker-compose.full.yml" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 创建所有必要的模型目录并设置权限
log_info "正在创建模型目录..."
MODEL_DIRS=(
    "models/hanlp_models"
    "models/cemotion_cache" 
    "models/huggingface_cache"
    "models/modelscope_cache"
    "instance"
)

for dir in "${MODEL_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    else
        log_info "目录已存在: $dir"
    fi
    # 设置目录权限
    chmod 777 "$dir" 2>/dev/null || log_warning "无法设置 $dir 目录权限"
done

log_success "模型目录准备完成"

# 停止正在运行的服务
log_info "正在检查是否有正在运行的服务..."
if docker-compose -f docker-compose.full.yml ps --services --filter "status=running" 2>/dev/null | grep -q .; then
    log_info "检测到正在运行的服务，正在停止..."
    if docker-compose -f docker-compose.full.yml down; then
        log_success "服务已停止"
    else
        log_warning "停止服务时出现问题，尝试强制停止"
        docker-compose -f docker-compose.full.yml down --remove-orphans --timeout 30
    fi
else
    log_info "没有正在运行的服务"
fi

# 清理旧的镜像和容器
log_info "正在清理系统资源..."

# 删除旧的镜像（如果存在）
log_info "正在检查是否存在旧的镜像..."
OLD_IMAGES=$(docker images --filter "reference=sentiscore-*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)

if [ -n "$OLD_IMAGES" ]; then
    log_info "检测到旧的镜像，正在删除..."
    echo "$OLD_IMAGES" | while read -r image; do
        if [ -n "$image" ]; then
            docker rmi "$image" 2>/dev/null || log_warning "无法删除镜像: $image"
        fi
    done
    log_success "旧镜像清理完成"
else
    log_info "没有找到旧的镜像"
fi

# 清理悬空镜像
log_info "正在清理悬空镜像..."
DANGLING_IMAGES=$(docker images -f "dangling=true" -q 2>/dev/null || true)
if [ -n "$DANGLING_IMAGES" ]; then
    echo "$DANGLING_IMAGES" | xargs -r docker rmi 2>/dev/null || log_warning "无法清理所有悬空镜像"
    log_success "悬空镜像清理完成"
else
    log_info "没有悬空镜像需要清理"
fi

# 重新构建并启动服务
log_info "正在构建并启动服务..."
if docker-compose -f docker-compose.full.yml up --build -d; then
    log_success "服务构建并启动成功"
    
    # 等待服务启动
    log_info "正在等待服务启动..."
    sleep 10
    
    # 检查服务状态
    log_info "检查服务状态..."
    if docker-compose -f docker-compose.full.yml ps --services --filter "status=running" 2>/dev/null | grep -q .; then
        log_success "所有服务运行正常"
    else
        log_warning "部分服务可能未正常启动，请检查日志"
    fi
    
    echo ""
    echo -e "${GREEN}=== 部署完成 ==="
    echo -e "${BLUE}前端管理后台: http://localhost:8888"
    echo -e "${BLUE}后端API服务: http://localhost:5000"
    echo -e "${BLUE}健康检查: http://localhost:5000/health"
    echo -e "${GREEN}==================${NC}"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose -f docker-compose.full.yml logs -f"
    echo "  停止服务: docker-compose -f docker-compose.full.yml down"
    echo "  重启服务: docker-compose -f docker-compose.full.yml restart"
    
else
    log_error "服务构建或启动失败"
    log_info "请检查错误信息并重试"
    exit 1
fi

# 显示最终状态
log_info "最终服务状态:"
docker-compose -f docker-compose.full.yml ps
