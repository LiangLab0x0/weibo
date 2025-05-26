"""
微博管理API路由

提供微博内容分析和删除的REST API端点
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.tasks.weibo_tasks import analyze_weibo_content, delete_weibo_posts, login_weibo_task
from app.models.schemas import (
    AnalysisRequest, DeleteRequest, TaskResponse, TaskStatus,
    LoginRequest, ErrorResponse
)
from app.core.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weibo", tags=["微博管理"])


@router.post("/login", response_model=TaskResponse)
async def login_weibo(
    request: LoginRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """
    登录微博账号
    
    创建异步任务来登录微博账号，支持扫码和密码两种方式
    """
    try:
        # 创建Celery任务，默认使用扫码登录
        task = login_weibo_task.delay(
            username=request.username,
            password=request.password,
            use_qr=True  # 默认使用扫码登录
        )
        
        logger.info(f"创建扫码登录任务: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message="扫码登录任务已创建，请使用微博APP扫描二维码..."
        )
        
    except Exception as e:
        logger.error(f"创建登录任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建登录任务失败: {str(e)}"
        )


@router.post("/login/password", response_model=TaskResponse)
async def login_weibo_password(
    request: LoginRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """
    使用密码登录微博账号（备用方案）
    
    创建异步任务来使用用户名密码登录微博账号
    """
    try:
        # 验证必需参数
        if not request.username or not request.password:
            raise HTTPException(
                status_code=400,
                detail="用户名和密码不能为空"
            )
        
        # 创建Celery任务，使用密码登录
        task = login_weibo_task.delay(
            username=request.username,
            password=request.password,
            use_qr=False  # 使用密码登录
        )
        
        logger.info(f"创建密码登录任务: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message="密码登录任务已创建，正在处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建密码登录任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建密码登录任务失败: {str(e)}"
        )


@router.get("/login/qr-status/{task_id}")
async def check_qr_login_status(task_id: str) -> Dict[str, Any]:
    """
    检查扫码登录状态
    
    专门用于检查扫码登录的二维码状态
    """
    try:
        # 获取任务结果
        task_result = AsyncResult(task_id, app=celery_app)
        
        if not task_result:
            raise HTTPException(
                status_code=404,
                detail="任务不存在"
            )
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "qr_status": "waiting",
            "message": "等待扫码...",
            "qr_code": None,
            "user_info": None,
            "error": None
        }
        
        if task_result.status == "PENDING":
            response["message"] = "正在生成二维码..."
            
        elif task_result.status == "PROGRESS":
            # 获取进度信息
            meta = task_result.info or {}
            response["message"] = meta.get("message", "任务执行中...")
            response["qr_code"] = meta.get("qr_code")
            response["qr_status"] = meta.get("qr_status", "waiting")
            
        elif task_result.status == "SUCCESS":
            result = task_result.result or {}
            response["message"] = "登录成功"
            response["qr_status"] = "confirmed"
            response["user_info"] = result.get("user_info", {})
            
        elif task_result.status == "FAILURE":
            response["message"] = "登录失败"
            response["qr_status"] = "error"
            response["error"] = str(task_result.info)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查扫码登录状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"检查扫码登录状态失败: {str(e)}"
        )


@router.post("/analyze", response_model=TaskResponse)
async def analyze_content(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """
    分析微博内容
    
    创建异步任务来分析微博内容的风险等级
    """
    try:
        # 构建分析条件
        criteria = {
            "time_range": request.time_range.dict() if request.time_range else {},
            "keywords": request.keywords or [],
            "max_posts": request.max_posts
        }
        
        # 创建Celery任务
        task = analyze_weibo_content.delay(
            user_id="default_user",  # TODO: 从认证中获取用户ID
            criteria=criteria
        )
        
        logger.info(f"创建分析任务: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message="分析任务已创建，正在处理中..."
        )
        
    except Exception as e:
        logger.error(f"创建分析任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建分析任务失败: {str(e)}"
        )


@router.post("/delete", response_model=TaskResponse)
async def delete_posts(
    request: DeleteRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """
    批量删除微博
    
    创建异步任务来批量删除指定的微博
    """
    try:
        # 验证删除确认
        if not request.confirm:
            raise HTTPException(
                status_code=400,
                detail="必须确认删除操作"
            )
        
        # 验证删除数量限制
        if len(request.post_ids) > settings.max_delete_per_hour:
            raise HTTPException(
                status_code=400,
                detail=f"单次删除数量不能超过 {settings.max_delete_per_hour} 条"
            )
        
        # 创建Celery任务
        task = delete_weibo_posts.delay(
            user_id="default_user",  # TODO: 从认证中获取用户ID
            post_ids=request.post_ids
        )
        
        logger.info(f"创建删除任务: {task.id}，删除 {len(request.post_ids)} 条微博")
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message=f"删除任务已创建，将删除 {len(request.post_ids)} 条微博..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建删除任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建删除任务失败: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str) -> TaskStatus:
    """
    获取任务状态
    
    查询Celery任务的执行状态和结果
    """
    try:
        # 获取任务结果
        task_result = AsyncResult(task_id, app=celery_app)
        
        if not task_result:
            raise HTTPException(
                status_code=404,
                detail="任务不存在"
            )
        
        # 构建响应
        response = TaskStatus(
            task_id=task_id,
            status=task_result.status,
            progress=None,
            message=None,
            result=None,
            error=None
        )
        
        if task_result.status == "PENDING":
            response.message = "任务等待执行中..."
            
        elif task_result.status == "PROGRESS":
            # 获取进度信息
            meta = task_result.info or {}
            response.progress = meta.get("progress")
            response.message = meta.get("message", "任务执行中...")
            
        elif task_result.status == "SUCCESS":
            response.message = "任务执行成功"
            response.result = task_result.result
            response.progress = 100
            
        elif task_result.status == "FAILURE":
            response.message = "任务执行失败"
            response.error = str(task_result.info)
            
        else:
            response.message = f"任务状态: {task_result.status}"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    取消任务
    
    取消正在执行或等待执行的任务
    """
    try:
        # 撤销任务
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"任务 {task_id} 已被取消")
        
        return {
            "success": True,
            "message": f"任务 {task_id} 已被取消",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"取消任务失败: {str(e)}"
        )


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    获取系统统计信息
    
    返回任务队列和系统状态的统计信息
    """
    try:
        # 获取Celery统计信息
        inspect = celery_app.control.inspect()
        
        # 活跃任务
        active_tasks = inspect.active()
        active_count = sum(len(tasks) for tasks in (active_tasks or {}).values())
        
        # 等待任务
        reserved_tasks = inspect.reserved()
        reserved_count = sum(len(tasks) for tasks in (reserved_tasks or {}).values())
        
        return {
            "active_tasks": active_count,
            "reserved_tasks": reserved_count,
            "total_pending": active_count + reserved_count,
            "max_delete_per_hour": settings.max_delete_per_hour,
            "operation_delay_range": f"{settings.operation_delay_min}-{settings.operation_delay_max}秒"
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        ) 