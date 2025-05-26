"""
API数据模型定义

使用Pydantic定义请求和响应的数据模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """时间范围模型"""
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: Optional[str] = Field(None, min_length=1, description="用户名（密码登录时必需）")
    password: Optional[str] = Field(None, min_length=1, description="密码（密码登录时必需）")


class UserInfo(BaseModel):
    """用户信息模型"""
    nickname: str = Field(..., description="用户昵称")
    followers_count: str = Field(..., description="粉丝数")
    following_count: str = Field(..., description="关注数")
    weibo_count: str = Field(..., description="微博数")


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = Field(..., description="是否登录成功")
    user_info: Optional[UserInfo] = Field(None, description="用户信息")
    message: str = Field(..., description="登录消息")
    error: Optional[str] = Field(None, description="错误信息")


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    time_range: Optional[TimeRange] = Field(None, description="时间范围")
    keywords: Optional[List[str]] = Field(default=[], description="关键词列表")
    max_posts: int = Field(default=100, ge=1, le=1000, description="最大分析数量")


class AnalysisResult(BaseModel):
    """分析结果模型"""
    post_id: str = Field(..., description="微博ID")
    content: str = Field(..., description="微博内容摘要")
    date: str = Field(..., description="发布日期")
    risk_score: float = Field(..., ge=0, le=10, description="风险分数 (0-10)")
    risk_reason: str = Field(..., description="风险原因")
    risk_category: Optional[str] = Field(None, description="风险类别")
    suggestion: Optional[str] = Field(None, description="处理建议")
    url: Optional[str] = Field(None, description="微博链接")


class DeleteRequest(BaseModel):
    """删除请求模型"""
    post_ids: List[str] = Field(..., min_items=1, max_items=100, description="微博ID列表")
    confirm: bool = Field(..., description="确认删除")


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    message: Optional[str] = Field(None, description="状态消息")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")


class AnalysisResponse(BaseModel):
    """分析响应模型"""
    success: bool = Field(..., description="是否成功")
    total_analyzed: int = Field(..., description="总分析数量")
    high_risk_count: int = Field(..., description="高风险数量")
    medium_risk_count: int = Field(..., description="中风险数量")
    low_risk_count: int = Field(..., description="低风险数量")
    analyzed_posts: List[AnalysisResult] = Field(..., description="分析结果列表")


class DeleteResult(BaseModel):
    """删除结果模型"""
    post_id: str = Field(..., description="微博ID")
    success: bool = Field(..., description="是否删除成功")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: str = Field(..., description="删除时间")


class DeleteResponse(BaseModel):
    """删除响应模型"""
    success: bool = Field(..., description="是否成功")
    total_requested: int = Field(..., description="请求删除总数")
    successful_count: int = Field(..., description="成功删除数量")
    failed_count: int = Field(..., description="失败删除数量")
    successful_deletes: List[DeleteResult] = Field(..., description="成功删除列表")
    failed_deletes: List[DeleteResult] = Field(..., description="失败删除列表")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: bool = Field(True, description="错误标识")
    message: str = Field(..., description="错误消息")
    status_code: int = Field(..., description="状态码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情") 