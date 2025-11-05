#!/bin/bash

# 创建 Docker Volume 用于持久化数据库
echo "Creating Docker volume for SentiScore database..."
docker volume create SentiScore_sqlite_data

echo "Docker volume 'SentiScore_sqlite_data' created successfully!"
echo "You can now run the application with persistent database storage."