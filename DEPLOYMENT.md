# SentiScore 部署指南

## 一键部署脚本

为了简化 SentiScore 的部署过程，项目提供了两个一键部署脚本：

1. `deploy.sh` - 适用于 Linux/macOS 系统的 Bash 脚本
2. `deploy.ps1` - 适用于 Windows 系统的 PowerShell 脚本

### 功能说明

这些脚本会自动执行以下操作：

1. 检查 Docker 和 Docker Compose 是否已安装
2. 检查是否在项目根目录运行
3. 停止任何正在运行的服务实例
4. 删除旧的 Docker 镜像
5. 重新构建并启动服务

### 使用方法

#### Linux/macOS

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

#### Windows

```powershell
# 运行部署脚本
./deploy.ps1
```

### 访问服务

部署完成后，可以通过以下地址访问服务：

- 前端管理后台: http://localhost
- 后端API服务: http://localhost:5000

### 手动部署

如果需要手动部署，可以使用以下命令：

```bash
# 停止并删除现有服务
docker-compose -f docker-compose.full.yml down

# 构建并启动服务
docker-compose -f docker-compose.full.yml up --build -d
```