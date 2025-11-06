# SentiScore 一键部署脚本 (PowerShell 版本)
# 该脚本会检查 Docker 环境，停止正在运行的服务，删除旧镜像，然后重新构建和启动服务

Write-Host "=== SentiScore 一键部署脚本 ===" -ForegroundColor Green

# 检查 Docker 是否已安装
Write-Host "正在检查 Docker 环境..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker 版本: $dockerVersion" -ForegroundColor Cyan
} catch {
    Write-Host "错误: 未检测到 Docker，请先安装 Docker" -ForegroundColor Red
    Write-Host "请访问 https://docs.docker.com/get-docker/ 获取安装指南" -ForegroundColor Yellow
    exit 1
}

# 检查 Docker Compose 是否已安装
try {
    $dockerComposeVersion = docker-compose --version
    Write-Host "Docker Compose 版本: $dockerComposeVersion" -ForegroundColor Cyan
} catch {
    Write-Host "错误: 未检测到 Docker Compose，请先安装 Docker Compose" -ForegroundColor Red
    Write-Host "请访问 https://docs.docker.com/compose/install/ 获取安装指南" -ForegroundColor Yellow
    exit 1
}

Write-Host "Docker 环境检查通过 ✓" -ForegroundColor Green

# 检查是否在项目根目录
if (-not (Test-Path "docker-compose.full.yml")) {
    Write-Host "错误: 请在项目根目录运行此脚本" -ForegroundColor Red
    exit 1
}

# 停止正在运行的服务
Write-Host "正在检查是否有正在运行的服务..." -ForegroundColor Yellow
try {
    $runningServices = docker-compose -f docker-compose.full.yml ps
    if ($runningServices -match "Up") {
        Write-Host "检测到正在运行的服务，正在停止..." -ForegroundColor Yellow
        $result = docker-compose -f docker-compose.full.yml down
        if ($result) {
            Write-Host "服务已停止 ✓" -ForegroundColor Green
        } else {
            Write-Host "警告: 停止服务时出现问题" -ForegroundColor Yellow
        }
    } else {
        Write-Host "没有正在运行的服务" -ForegroundColor Green
    }
} catch {
    Write-Host "检查运行服务时出错: $_" -ForegroundColor Red
}

# 删除旧的镜像（如果存在）
Write-Host "正在检查是否存在旧的镜像..." -ForegroundColor Yellow
try {
    $images = docker images
    if ($images -match "sentiscore-backend" -or $images -match "sentiscore-frontend") {
        Write-Host "检测到旧的镜像，正在删除..." -ForegroundColor Yellow
        docker rmi sentiscore-backend:latest 2>$null
        docker rmi sentiscore-frontend:latest 2>$null
        Write-Host "旧镜像已删除 ✓" -ForegroundColor Green
    } else {
        Write-Host "没有找到旧的镜像" -ForegroundColor Green
    }
} catch {
    Write-Host "检查或删除镜像时出错: $_" -ForegroundColor Red
}

# 重新构建并启动服务
Write-Host "正在构建并启动服务..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.full.yml up --build -d
    Write-Host "服务构建并启动成功 ✓" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== 部署完成 ===" -ForegroundColor Green
    Write-Host "前端管理后台: http://localhost" -ForegroundColor Cyan
    Write-Host "后端API服务: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Green
} catch {
    Write-Host "错误: 服务构建或启动失败" -ForegroundColor Red
    Write-Host "错误详情: $_" -ForegroundColor Red
    exit 1
}