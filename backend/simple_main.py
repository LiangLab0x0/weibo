"""
简化版微博AI内容管理器 - 用于测试部署

提供基础的REST API服务
"""

import logging
import sys
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="微博AI内容管理器",
    version="1.0.0",
    description="基于AI的微博内容智能管理工具"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, Any]:
    """根路径端点"""
    return {
        "message": "欢迎使用微博AI内容管理器",
        "version": "1.0.0",
        "status": "运行中"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "微博AI内容管理器",
        "version": "1.0.0"
    }


@app.get("/api/v1/test")
async def test_api() -> Dict[str, Any]:
    """测试API端点"""
    return {
        "success": True,
        "message": "API测试成功",
        "timestamp": "2025-05-25T08:00:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 