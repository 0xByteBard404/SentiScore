# 模型持久化配置指南

## 新的模型持久化方案

我们已将模型持久化方案从多个分散的卷优化为统一的 `SentiScore_models` 卷。

### 优化后的优势

1. **简化管理** - 只需要管理一个卷
2. **减少配置复杂度** - 更简洁的Docker配置
3. **便于备份** - 一次性备份所有模型数据
4. **更好的组织** - 所有模型文件在一个目录结构中

### 目录结构

```
/app/models/
├── hanlp_models/          # HanLP模型文件
├── modelscope_cache/      # ModelScope缓存
└── (其他模型缓存目录)
```

### 部署步骤

1. **首次部署**：
   ```bash
   docker-compose up -d
   ```
   系统会自动下载所有需要的模型到持久化卷中

2. **后续部署**：
   ```bash
   docker-compose down
   docker-compose up -d
   ```
   模型数据会保留在卷中，无需重新下载

3. **查看卷状态**：
   ```bash
   docker volume ls | grep SentiScore
   ```

4. **备份模型数据**：
   ```bash
   docker run --rm -v SentiScore_models:/models -v $(pwd):/backup alpine tar czf /backup/models_backup.tar.gz /models
   ```

5. **恢复模型数据**：
   ```bash
   docker run --rm -v SentiScore_models:/models -v $(pwd):/backup alpine tar xzf /backup/models_backup.tar.gz -C /
   ```

### 环境变量配置

在 `docker-compose.yml` 中配置的环境变量确保所有模型组件使用正确的目录：

- `HANLP_MODEL_DIR=/app/models/hanlp_models`
- `MODELSCOPE_CACHE_DIR=/app/models/modelscope_cache`
- `MODEL_CACHE_DIR=/app/.cemotion_cache`
- `HF_HOME=/app/.cache/huggingface`

### 注意事项

1. **首次部署时间**：首次部署需要下载所有模型，可能需要较长时间
2. **存储空间**：确保有足够的磁盘空间存储模型文件
3. **网络连接**：确保服务器可以访问镜像站点下载模型
4. **权限设置**：Docker卷会自动处理文件权限问题

### 故障排除

如果遇到模型加载问题：

1. 检查卷是否正确挂载：
   ```bash
   docker exec -it sentiscore_sentiscore_1 ls -la /app/models/
   ```

2. 检查模型文件是否存在：
   ```bash
   docker exec -it sentiscore_sentiscore_1 find /app/models -type f | head -10
   ```

3. 重新下载模型（如果需要）：
   ```bash
   docker-compose down
   docker volume rm SentiScore_models
   docker-compose up -d
   ```

这种统一的模型持久化方案大大简化了部署和维护工作，同时确保了模型数据的安全性和可用性。
