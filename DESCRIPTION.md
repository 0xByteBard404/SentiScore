# Chinese Sentiment Analysis API

基于 cemotion 情感分析库封装的 Flask RESTful API 服务，提供高精度的中文文本情感倾向识别功能。该服务支持单条文本分析和批量处理，具备模型缓存、GPU加速、多源模型下载等特性。

## 核心特性

- 🎯 基于 cemotion：使用经过优化的中文情感分析模型
- ⚡ 高性能设计：支持批量处理、结果缓存和 GPU 加速
- 🌐 多环境部署：支持 Docker、Docker Compose 和传统部署方式
- 🔄 模块化架构：清晰的代码结构，便于维护和扩展
- 🌍 多源下载：支持国内外多种模型镜像源，适应不同网络环境
- 📊 实时监控：内置健康检查和性能指标接口

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

API 服务将在 `http://localhost:5000` 上运行，提供情感分析核心功能。