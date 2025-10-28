import os
import time
import torch
import traceback
from flask import request, jsonify
from dataclasses import asdict

from src.utils.helpers import create_error_response, create_success_response, get_client_ip, EmotionResult


def register_routes(app, analyzer, config):
    """注册所有API路由"""
    
    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(error):
        return create_error_response("BAD_REQUEST", "请求格式错误", 400)

    @app.errorhandler(404)
    def not_found(error):
        return create_error_response("NOT_FOUND", "接口不存在", 404)

    @app.errorhandler(405)
    def method_not_allowed(error):
        return create_error_response("METHOD_NOT_ALLOWED", "请求方法不支持", 405)

    @app.errorhandler(500)
    def internal_error(error):
        return create_error_response("INTERNAL_ERROR", "服务器内部错误", 500)

    @app.before_request
    def log_request_info():
        """记录请求信息"""
        client_ip = get_client_ip()
        method = request.method
        path = request.path
        app.logger.debug(f"[{client_ip}] {method} {path} - Headers: {dict(request.headers)}")

    @app.teardown_appcontext
    def cleanup(exception=None):
        """应用上下文清理"""
        import gc
        # 更智能的GPU内存清理
        if torch.cuda.is_available():
            torch.cuda.empty_cache()  # 清理未使用的GPU内存
            torch.cuda.synchronize()   # 同步确保清理完成
        
        # 垃圾回收
        collected = gc.collect()
        app.logger.debug(f"垃圾回收完成，清理对象数: {collected}")

    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查端点"""
        try:
            # 简单的健康检查：测试模型是否可用
            test_result = analyzer.predict_single("测试文本")
            health_status = {
                "status": "healthy",
                "timestamp": int(time.time()),
                "model_ready": True,
                "version": "v1.0.0",
                "gpu_available": torch.cuda.is_available()
            }
            return jsonify(health_status), 200
        except Exception as e:
            app.logger.error(f"健康检查失败: {e}")
            return jsonify({
                "status": "unhealthy",
                "timestamp": int(time.time()),
                "error": str(e)
            }), 503

    @app.route('/', methods=['GET'])
    def home():
        """服务信息"""
        return jsonify({
            "message": "中文情感分析API服务",
            "version": "1.0.0",
            "endpoints": {
                "analyze": "/analyze",
                "batch_analyze": "/batch",
                "health": "/health"
            },
            "documentation": "/docs"
        })

    @app.route('/analyze', methods=['POST'])
    def analyze_emotion():
        """单文本情感分析"""
        start_time = time.time()

        try:
            # 解析请求数据
            data = request.get_json(silent=True)
            if not data:
                return create_error_response("INVALID_JSON", "无效的JSON格式", 400)

            text = data.get('text', '').strip()

            # 输入验证
            is_valid, error = analyzer.validate_input(text)
            if not is_valid:
                return create_error_response(error.code, error.message, 400, error.details)

            # 执行情感分析
            result = analyzer.analyze_emotion(text)

            # 记录处理时间
            processing_time = time.time() - start_time
            app.logger.info(f"[情感分析] 耗时: {processing_time:.4f}秒")

            return create_success_response(result.to_dict())

        except Exception as e:
            app.logger.error(f"未预期的错误: {traceback.format_exc()}")
            return create_error_response("UNKNOWN_ERROR", f"服务暂时异常，请稍后重试", 500)

    @app.route('/batch', methods=['POST'])
    def batch_analyze():
        """批量情感分析"""
        start_time = time.time()

        try:
            data = request.get_json(silent=True)
            if not data:
                return create_error_response("INVALID_JSON", "无效的JSON格式", 400)

            texts = data.get('texts', [])
            if not isinstance(texts, list):
                return create_error_response("INVALID_TYPE", "texts必须是数组", 400)

            if len(texts) > config.BATCH_SIZE:
                return create_error_response("BATCH_TOO_LARGE", f"批量大小最多支持{config.BATCH_SIZE}个文本", 400)

            if not texts:
                return create_error_response("EMPTY_BATCH", "texts数组不能为空", 400)

            # 验证所有文本
            for i, text in enumerate(texts):
                if not isinstance(text, str):
                    return create_error_response("INVALID_TEXT_TYPE", f"第{i}个文本不是字符串类型", 400)

                is_valid, error = analyzer.validate_input(text)
                if not is_valid:
                    return create_error_response(error.code, f"第{i}个文本验证失败: {error.message}", 400, error.details)

            # 执行批量情感分析
            try:
                predictions = analyzer.predict_batch(texts)
                results = []
                for text, score in zip(texts, predictions):
                    # 计算置信度（距离0.5的程度）
                    confidence = abs(score - 0.5) * 2
                    emotion = "正面" if score >= 0.5 else "负面"
                    
                    result = EmotionResult(
                        emotion_score=score,
                        emotion=emotion,
                        confidence=round(confidence, 4),
                        text_length=len(text)
                    )
                    results.append(result.to_dict())
                    
            except Exception as e:
                app.logger.error(f"批量处理预测失败: {e}")
                return create_error_response("BATCH_PROCESSING_ERROR", f"批量处理预测失败: {str(e)}", 500)

            processing_time = time.time() - start_time
            app.logger.info(f"[批量情感分析] 处理数量: {len(texts)}, 耗时: {processing_time:.4f}秒")
            return create_success_response(results)

        except Exception as e:
            app.logger.error(f"批量分析错误: {traceback.format_exc()}")
            return create_error_response("BATCH_ERROR", "批量处理失败", 500)

    @app.route('/metrics', methods=['GET'])
    def get_metrics():
        """获取服务指标（仅开发环境）"""
        if os.getenv('FLASK_ENV') != 'development':
            return create_error_response("ACCESS_DENIED", "生产环境不支持此端点", 403)

        # 获取内存使用情况
        metrics = {
            "memory_usage": {
                "cuda_mb": torch.cuda.memory_reserved(0) / 1024 / 1024 if torch.cuda.is_available() else 0,
                "cuda_cached_mb": torch.cuda.memory_cached(0) / 1024 / 1024 if torch.cuda.is_available() else 0
            },
            "config": asdict(config),
            "timestamp": int(time.time())
        }
        
        # 添加系统内存信息（如果psutil可用）
        try:
            import psutil
            process = psutil.Process(os.getpid())
            metrics["system_memory"] = {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            pass

        return jsonify(metrics)