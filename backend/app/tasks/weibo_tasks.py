"""
微博管理异步任务

使用Celery实现微博内容分析和删除的异步任务
"""

import asyncio
import logging
from typing import Dict, Any, List
from celery import current_task

from app.core.celery_app import celery_app
from app.agents.weibo_agent import WeiboAgent


logger = logging.getLogger(__name__)

# 全局微博代理实例（在实际应用中应该使用会话管理）
_weibo_agent = None


def run_async_task(coro):
    """在Celery中运行异步任务的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def get_weibo_agent():
    """获取微博代理实例"""
    global _weibo_agent
    if _weibo_agent is None:
        _weibo_agent = WeiboAgent()
    return _weibo_agent


@celery_app.task(bind=True, name="login_weibo_task")
def login_weibo_task(self, username: str = None, password: str = None, use_qr: bool = True) -> Dict[str, Any]:
    """
    登录微博任务
    
    Args:
        username: 用户名（密码登录时使用）
        password: 密码（密码登录时使用）
        use_qr: 是否使用扫码登录
        
    Returns:
        登录结果
    """
    login_method = "扫码登录" if use_qr else f"密码登录: {username}"
    logger.info(f"开始微博登录: {login_method}")
    
    def progress_callback(message: str):
        """进度回调函数"""
        meta = {"message": message, "login_method": login_method}
        if username:
            meta["username"] = username
        current_task.update_state(state="PROGRESS", meta=meta)
    
    async def qr_login_task():
        """异步扫码登录任务"""
        agent = get_weibo_agent()
        try:
            # 更新任务状态
            progress_callback("初始化浏览器...")
            
            # 生成二维码
            result = await agent.login_weibo_qr(progress_callback)
            
            if result.get("qr_code"):
                # 更新任务状态，包含二维码信息
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "message": "请使用微博APP扫描二维码",
                        "qr_code": result["qr_code"],
                        "qr_status": result.get("qr_status", "waiting"),
                        "login_method": login_method
                    }
                )
                
                # 轮询检查登录状态
                max_attempts = 60  # 最多等待5分钟
                for attempt in range(max_attempts):
                    await asyncio.sleep(5)  # 每5秒检查一次
                    
                    status_result = await agent.check_qr_status(progress_callback)
                    qr_status = status_result.get("qr_status", "waiting")
                    
                    # 更新任务状态
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "message": f"扫码状态: {qr_status}",
                            "qr_code": result["qr_code"],
                            "qr_status": qr_status,
                            "login_method": login_method,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts
                        }
                    )
                    
                    if qr_status == "confirmed":
                        # 登录成功
                        return {
                            "success": True,
                            "user_info": status_result.get("user_info", {}),
                            "message": "扫码登录成功",
                            "login_method": login_method
                        }
                    elif qr_status == "expired":
                        # 二维码过期
                        return {
                            "success": False,
                            "error": "二维码已过期，请重新登录",
                            "login_method": login_method
                        }
                    elif qr_status == "error":
                        # 登录错误
                        return {
                            "success": False,
                            "error": status_result.get("error", "扫码登录失败"),
                            "login_method": login_method
                        }
                
                # 超时
                return {
                    "success": False,
                    "error": "扫码登录超时，请重新尝试",
                    "login_method": login_method
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "生成二维码失败"),
                    "login_method": login_method
                }
                
        except Exception as e:
            logger.error(f"扫码登录任务异常: {str(e)}")
            return {
                "success": False,
                "error": f"扫码登录过程中出现异常: {str(e)}",
                "login_method": login_method
            }
    
    async def password_login_task():
        """异步密码登录任务"""
        agent = get_weibo_agent()
        try:
            # 更新任务状态
            progress_callback("初始化浏览器...")
            
            # 执行密码登录
            result = await agent.login_weibo(username, password, False, progress_callback)
            
            if result["success"]:
                progress_callback("登录成功，获取用户信息...")
                
                return {
                    "success": True,
                    "user_info": result.get("user_info", {}),
                    "message": "密码登录成功",
                    "username": username,
                    "login_method": login_method
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "密码登录失败"),
                    "username": username,
                    "login_method": login_method
                }
                
        except Exception as e:
            logger.error(f"密码登录任务异常: {str(e)}")
            return {
                "success": False,
                "error": f"密码登录过程中出现异常: {str(e)}",
                "username": username,
                "login_method": login_method
            }
    
    try:
        if use_qr:
            result = run_async_task(qr_login_task())
        else:
            if not username or not password:
                return {
                    "success": False,
                    "error": "密码登录需要提供用户名和密码",
                    "login_method": login_method
                }
            result = run_async_task(password_login_task())
        
        if result["success"]:
            logger.info(f"{login_method} 成功")
        else:
            logger.error(f"{login_method} 失败: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"登录任务执行异常: {str(e)}")
        return {
            "success": False,
            "error": f"任务执行异常: {str(e)}",
            "login_method": login_method
        }


@celery_app.task(bind=True, name="analyze_weibo_content")
def analyze_weibo_content(self, user_id: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析微博内容任务
    
    Args:
        user_id: 用户ID
        criteria: 分析条件
        
    Returns:
        分析结果
    """
    logger.info(f"开始分析用户 {user_id} 的微博内容")
    
    def progress_callback(message: str):
        """进度回调函数"""
        current_task.update_state(
            state="PROGRESS",
            meta={"message": message, "user_id": user_id}
        )
    
    async def analyze_task():
        """异步分析任务"""
        agent = get_weibo_agent()
        try:
            # 检查是否已登录
            if not agent.is_logged_in:
                return {
                    "success": False,
                    "error": "请先登录微博账号",
                    "user_id": user_id
                }
            
            # 更新任务状态
            progress_callback("开始分析微博内容...")
            
            # 执行分析
            result = await agent.analyze_posts(criteria, progress_callback)
            
            if result["success"]:
                progress_callback("分析完成，正在整理结果...")
                
                # 按风险分数排序
                analyzed_posts = result["data"]
                analyzed_posts.sort(key=lambda x: x["risk_score"], reverse=True)
                
                return {
                    "success": True,
                    "total_analyzed": result["total_analyzed"],
                    "high_risk_count": len([p for p in analyzed_posts if p["risk_score"] >= 7]),
                    "medium_risk_count": len([p for p in analyzed_posts if 4 <= p["risk_score"] < 7]),
                    "low_risk_count": len([p for p in analyzed_posts if p["risk_score"] < 4]),
                    "analyzed_posts": analyzed_posts,
                    "criteria": criteria,
                    "user_id": user_id
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "分析失败"),
                    "user_id": user_id
                }
                
        except Exception as e:
            logger.error(f"分析任务异常: {str(e)}")
            return {
                "success": False,
                "error": f"分析过程中出现异常: {str(e)}",
                "user_id": user_id
            }
    
    try:
        result = run_async_task(analyze_task())
        
        if result["success"]:
            logger.info(f"用户 {user_id} 的微博分析完成，共分析 {result['total_analyzed']} 条")
        else:
            logger.error(f"用户 {user_id} 的微博分析失败: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"分析任务执行异常: {str(e)}")
        return {
            "success": False,
            "error": f"任务执行异常: {str(e)}",
            "user_id": user_id
        }


@celery_app.task(bind=True, name="delete_weibo_posts")
def delete_weibo_posts(self, user_id: str, post_ids: List[str]) -> Dict[str, Any]:
    """
    批量删除微博任务
    
    Args:
        user_id: 用户ID
        post_ids: 要删除的微博ID列表
        
    Returns:
        删除结果
    """
    logger.info(f"开始为用户 {user_id} 批量删除 {len(post_ids)} 条微博")
    
    def progress_callback(message: str, current: int, total: int):
        """进度回调函数"""
        progress = int((current / total) * 100)
        current_task.update_state(
            state="PROGRESS",
            meta={
                "message": message,
                "current": current,
                "total": total,
                "progress": progress,
                "user_id": user_id
            }
        )
    
    async def delete_task():
        """异步删除任务"""
        agent = get_weibo_agent()
        try:
            # 检查是否已登录
            if not agent.is_logged_in:
                return {
                    "success": False,
                    "error": "请先登录微博账号",
                    "user_id": user_id
                }
            
            # 更新任务状态
            progress_callback("初始化删除代理...", 0, len(post_ids))
            
            # 执行批量删除
            result = await agent.batch_delete_posts(post_ids, progress_callback)
            
            return {
                "success": True,
                "total_requested": result["total_requested"],
                "successful_count": result["successful_count"],
                "failed_count": result["failed_count"],
                "successful_deletes": result["successful_deletes"],
                "failed_deletes": result["failed_deletes"],
                "completion_time": result["completion_time"],
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"删除任务异常: {str(e)}")
            return {
                "success": False,
                "error": f"删除过程中出现异常: {str(e)}",
                "user_id": user_id
            }
    
    try:
        result = run_async_task(delete_task())
        
        if result["success"]:
            logger.info(
                f"用户 {user_id} 的微博删除完成，"
                f"成功: {result['successful_count']}, "
                f"失败: {result['failed_count']}"
            )
        else:
            logger.error(f"用户 {user_id} 的微博删除失败: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"删除任务执行异常: {str(e)}")
        return {
            "success": False,
            "error": f"任务执行异常: {str(e)}",
            "user_id": user_id
        } 