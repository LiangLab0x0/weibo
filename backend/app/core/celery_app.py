"""
Celery应用配置

配置Celery实例，使用Redis作为broker和backend
"""

from celery import Celery
from app.core.config import settings


# 创建Celery实例
celery_app = Celery(
    "weibo_manager",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.weibo_tasks"]
)

# 配置Celery
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务过期时间
    task_time_limit=30 * 60,  # 30分钟
    task_soft_time_limit=25 * 60,  # 25分钟软限制
    
    # 结果过期时间
    result_expires=60 * 60,  # 1小时
    
    # 任务路由
    task_routes={
        "app.tasks.weibo_tasks.login_weibo_task": {"queue": "analysis"},
        "app.tasks.weibo_tasks.analyze_weibo_content": {"queue": "analysis"},
        "app.tasks.weibo_tasks.delete_weibo_posts": {"queue": "deletion"},
    },
    
    # 工作进程配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
) 