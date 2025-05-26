"""
微博专用AI代理

基于Browser Use实现微博内容分析和删除功能
"""

import asyncio
import json
import random
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable

from .base_agent import BaseAgent
from app.core.config import settings


logger = logging.getLogger(__name__)


class WeiboAgent(BaseAgent):
    """微博专用AI代理"""
    
    def __init__(self):
        super().__init__(
            task_description="微博内容智能管理代理",
            temperature=0.1,
            max_retries=3
        )
        self.is_logged_in = False
        self.user_info = {}
    
    async def login_weibo_qr(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        使用扫码方式登录微博
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            登录结果，包含二维码信息
        """
        login_prompt = """
请帮我使用扫码方式登录微博。

任务步骤：
1. 访问微博登录页面 https://weibo.com/login.php
2. 寻找并点击"扫码登录"或"二维码登录"按钮
3. 等待二维码出现在页面上
4. 截取二维码图片或获取其信息
5. 返回登录状态和二维码信息

请以JSON格式返回结果，包含以下字段：
- success: 布尔值，表示操作是否成功
- qr_code: 二维码信息或图片路径
- qr_status: 状态（waiting/scanned/confirmed/expired）
- user_info: 用户信息对象（如果登录成功）
- error: 错误信息（如果失败）

示例：{"success": true, "qr_code": "data:image/png;base64,...", "qr_status": "waiting", "user_info": {}, "error": ""}
"""
        
        if progress_callback:
            progress_callback("正在生成登录二维码...")
        
        result = await self.execute_task(login_prompt, progress_callback)
        
        if result["success"]:
            try:
                # 解析登录结果
                login_data = self._parse_qr_login_result(result["result"])
                if login_data.get("qr_status") == "confirmed" and login_data.get("success"):
                    self.is_logged_in = True
                    self.user_info = login_data.get("user_info", {})
                    logger.info(f"微博扫码登录成功: {self.user_info.get('nickname', 'Unknown')}")
                return login_data
            except Exception as e:
                logger.error(f"解析扫码登录结果失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"解析扫码登录结果失败: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "生成登录二维码失败")
            }
    
    async def check_qr_status(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        检查二维码登录状态
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            登录状态
        """
        check_prompt = """
请检查当前二维码登录的状态。

请执行以下操作：
1. 检查页面上的登录状态提示
2. 判断二维码是否已被扫描
3. 判断用户是否已确认登录
4. 如果登录成功，获取用户信息
5. 如果二维码过期，返回过期状态

请返回JSON格式的结果：
{
    "success": true/false,
    "qr_status": "waiting/scanned/confirmed/expired",
    "user_info": {
        "nickname": "用户昵称",
        "followers_count": "粉丝数",
        "following_count": "关注数",
        "weibo_count": "微博数"
    },
    "message": "状态描述",
    "error": "错误信息（如果有）"
}
"""
        
        if progress_callback:
            progress_callback("正在检查登录状态...")
        
        result = await self.execute_task(check_prompt, progress_callback)
        
        if result["success"]:
            try:
                status_data = self._parse_qr_status_result(result["result"])
                if status_data.get("qr_status") == "confirmed" and status_data.get("success"):
                    self.is_logged_in = True
                    self.user_info = status_data.get("user_info", {})
                    logger.info(f"微博扫码登录确认成功: {self.user_info.get('nickname', 'Unknown')}")
                return status_data
            except Exception as e:
                logger.error(f"解析登录状态失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"解析登录状态失败: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "检查登录状态失败")
            }
    
    async def login_weibo(
        self,
        username: str = None,
        password: str = None,
        use_qr: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        登录微博（支持扫码和密码两种方式）
        
        Args:
            username: 用户名（密码登录时使用）
            password: 密码（密码登录时使用）
            use_qr: 是否使用扫码登录
            progress_callback: 进度回调函数
            
        Returns:
            登录结果
        """
        if use_qr:
            return await self.login_weibo_qr(progress_callback)
        else:
            # 保留原有的密码登录方式作为备选
            return await self.login_weibo_password(username, password, progress_callback)
    
    async def login_weibo_password(
        self,
        username: str,
        password: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        使用用户名密码登录微博（备用方案）
        
        Args:
            username: 用户名
            password: 密码
            progress_callback: 进度回调函数
            
        Returns:
            登录结果
        """
        login_prompt = f"""
请帮我使用用户名密码登录微博账号。

登录信息：
- 用户名：{username}
- 密码：{password}

请执行以下步骤：
1. 打开微博登录页面 (https://weibo.com/login.php)
2. 选择用户名密码登录方式
3. 输入用户名和密码
4. 处理可能出现的验证码或滑块验证
5. 确认登录成功
6. 获取用户基本信息（昵称、粉丝数等）

注意：现在很多微博账号可能不支持密码登录，如果遇到此情况，请返回相应错误信息。

请返回JSON格式的结果：
{{
    "success": true/false,
    "user_info": {{
        "nickname": "用户昵称",
        "followers_count": "粉丝数",
        "following_count": "关注数",
        "weibo_count": "微博数"
    }},
    "error": "错误信息（如果有）"
}}
"""
        
        if progress_callback:
            progress_callback("正在使用密码登录微博...")
        
        result = await self.execute_task(login_prompt, progress_callback)
        
        if result["success"]:
            try:
                # 解析登录结果
                login_data = self._parse_login_result(result["result"])
                if login_data["success"]:
                    self.is_logged_in = True
                    self.user_info = login_data.get("user_info", {})
                    logger.info(f"微博密码登录成功: {self.user_info.get('nickname', 'Unknown')}")
                return login_data
            except Exception as e:
                logger.error(f"解析登录结果失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"解析登录结果失败: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "密码登录失败")
            }
    
    async def get_user_weibos(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        max_count: int = 100,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        获取用户微博列表
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            keywords: 关键词过滤
            max_count: 最大获取数量
            progress_callback: 进度回调函数
            
        Returns:
            微博列表
        """
        if not self.is_logged_in:
            return {
                "success": False,
                "error": "请先登录微博"
            }
        
        # 构建获取微博的提示词
        time_filter = ""
        if start_date and end_date:
            time_filter = f"时间范围：{start_date} 到 {end_date}"
        elif start_date:
            time_filter = f"从 {start_date} 开始"
        elif end_date:
            time_filter = f"到 {end_date} 结束"
        
        keyword_filter = ""
        if keywords:
            keyword_filter = f"包含关键词：{', '.join(keywords)}"
        
        get_weibos_prompt = f"""
请帮我获取我的微博列表。

筛选条件：
- {time_filter if time_filter else '不限时间'}
- {keyword_filter if keyword_filter else '不限关键词'}
- 最大数量：{max_count} 条

请执行以下步骤：
1. 进入我的微博主页
2. 滚动页面加载更多微博
3. 根据时间和关键词筛选微博
4. 提取每条微博的详细信息

对于每条微博，请提取以下信息：
- 微博ID
- 发布时间
- 微博内容（完整文本）
- 转发数、评论数、点赞数
- 是否包含图片/视频
- 微博链接

请返回JSON格式的结果：
{{
    "success": true/false,
    "weibos": [
        {{
            "id": "微博ID",
            "content": "微博内容",
            "publish_time": "发布时间",
            "repost_count": 转发数,
            "comment_count": 评论数,
            "like_count": 点赞数,
            "has_media": true/false,
            "url": "微博链接"
        }}
    ],
    "total_count": 总数量,
    "error": "错误信息（如果有）"
}}
"""
        
        if progress_callback:
            progress_callback("正在获取微博列表...")
        
        result = await self.execute_task(get_weibos_prompt, progress_callback)
        
        if result["success"]:
            try:
                weibos_data = self._parse_weibos_result(result["result"])
                return weibos_data
            except Exception as e:
                logger.error(f"解析微博列表失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"解析微博列表失败: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "获取微博列表失败")
            }
    
    async def analyze_posts(
        self,
        criteria: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        分析微博内容
        
        Args:
            criteria: 筛选条件，包含时间范围、关键词等
            progress_callback: 进度回调函数
            
        Returns:
            分析结果
        """
        if progress_callback:
            progress_callback("开始获取微博内容...")
        
        # 首先获取微博列表
        time_range = criteria.get("time_range", {})
        keywords = criteria.get("keywords", [])
        max_posts = criteria.get("max_posts", 100)
        
        weibos_result = await self.get_user_weibos(
            start_date=time_range.get("start_date"),
            end_date=time_range.get("end_date"),
            keywords=keywords,
            max_count=max_posts,
            progress_callback=progress_callback
        )
        
        if not weibos_result["success"]:
            return weibos_result
        
        weibos = weibos_result["weibos"]
        if not weibos:
            return {
                "success": True,
                "data": [],
                "total_analyzed": 0,
                "criteria": criteria
            }
        
        if progress_callback:
            progress_callback(f"开始分析 {len(weibos)} 条微博...")
        
        # 分析每条微博的风险
        analyzed_posts = []
        for i, weibo in enumerate(weibos):
            if progress_callback:
                progress_callback(f"分析进度: {i+1}/{len(weibos)}")
            
            risk_analysis = await self._analyze_single_weibo(weibo)
            analyzed_posts.append(risk_analysis)
            
            # 添加延迟避免过于频繁的请求
            await asyncio.sleep(1)
        
        # 按风险分数排序
        analyzed_posts.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "success": True,
            "data": analyzed_posts,
            "total_analyzed": len(analyzed_posts),
            "criteria": criteria
        }
    
    async def _analyze_single_weibo(self, weibo: Dict[str, Any]) -> Dict[str, Any]:
        """分析单条微博的风险"""
        content = weibo.get("content", "")
        publish_time = weibo.get("publish_time", "")
        
        analysis_prompt = f"""
请分析以下微博内容的风险等级：

微博内容：{content}
发布时间：{publish_time}

请从以下维度评估风险（0-10分，10分为最高风险）：
1. 政治敏感内容
2. 不当言论或争议性内容
3. 过时信息或不准确信息
4. 个人隐私泄露
5. 商业推广或垃圾信息
6. 负面情绪或抱怨
7. 可能引起误解的内容

请返回JSON格式的分析结果：
{{
    "risk_score": 风险分数(0-10),
    "risk_reasons": ["具体风险原因1", "具体风险原因2"],
    "risk_category": "主要风险类别",
    "suggestion": "处理建议"
}}
"""
        
        try:
            result = await self.execute_task(analysis_prompt)
            if result["success"]:
                analysis_data = self._parse_analysis_result(result["result"])
                
                return {
                    "post_id": weibo.get("id", ""),
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "date": publish_time,
                    "risk_score": analysis_data.get("risk_score", 0),
                    "risk_reason": "; ".join(analysis_data.get("risk_reasons", [])),
                    "risk_category": analysis_data.get("risk_category", ""),
                    "suggestion": analysis_data.get("suggestion", ""),
                    "url": weibo.get("url", ""),
                    "original_weibo": weibo
                }
            else:
                # 如果AI分析失败，使用简单的关键词检测
                return self._simple_risk_analysis(weibo)
                
        except Exception as e:
            logger.error(f"分析微博失败: {str(e)}")
            return self._simple_risk_analysis(weibo)
    
    def _simple_risk_analysis(self, weibo: Dict[str, Any]) -> Dict[str, Any]:
        """简单的关键词风险分析"""
        content = weibo.get("content", "").lower()
        
        # 定义风险关键词
        high_risk_keywords = ["政治", "敏感", "抗议", "游行"]
        medium_risk_keywords = ["抱怨", "投诉", "不满", "愤怒"]
        
        risk_score = 0
        risk_reasons = []
        
        for keyword in high_risk_keywords:
            if keyword in content:
                risk_score = max(risk_score, 8)
                risk_reasons.append(f"包含高风险关键词: {keyword}")
        
        for keyword in medium_risk_keywords:
            if keyword in content:
                risk_score = max(risk_score, 5)
                risk_reasons.append(f"包含中风险关键词: {keyword}")
        
        if not risk_reasons:
            risk_score = 2
            risk_reasons = ["内容相对安全"]
        
        return {
            "post_id": weibo.get("id", ""),
            "content": content[:200] + "..." if len(content) > 200 else content,
            "date": weibo.get("publish_time", ""),
            "risk_score": risk_score,
            "risk_reason": "; ".join(risk_reasons),
            "risk_category": "关键词检测",
            "suggestion": "建议人工审核",
            "url": weibo.get("url", ""),
            "original_weibo": weibo
        }
    
    async def delete_post(
        self,
        post_id: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        删除单条微博
        
        Args:
            post_id: 微博ID
            progress_callback: 进度回调函数
            
        Returns:
            删除结果
        """
        if not self.is_logged_in:
            return {
                "post_id": post_id,
                "success": False,
                "error": "请先登录微博",
                "timestamp": datetime.now().isoformat()
            }
        
        # 添加随机延迟，避免被检测
        delay = random.randint(
            settings.operation_delay_min, 
            settings.operation_delay_max
        )
        
        if progress_callback:
            progress_callback(f"等待 {delay} 秒后删除微博 {post_id}...")
        
        await asyncio.sleep(delay)
        
        # 构建删除任务的提示词
        delete_prompt = f"""
请帮我删除指定的微博。

微博ID：{post_id}

请执行以下步骤：
1. 在我的微博页面找到ID为 {post_id} 的微博
2. 点击微博右上角的"更多"按钮
3. 选择"删除"选项
4. 确认删除操作
5. 验证删除是否成功

请小心操作，确保只删除指定的微博。
如果找不到该微博或删除失败，请返回具体的错误信息。

请返回JSON格式的结果：
{{
    "success": true/false,
    "error": "错误信息（如果有）"
}}
"""
        
        if progress_callback:
            progress_callback(f"正在删除微博 {post_id}...")
        
        result = await self.execute_task(delete_prompt, progress_callback)
        
        delete_result = {
            "post_id": post_id,
            "success": result["success"],
            "timestamp": datetime.now().isoformat()
        }
        
        if result["success"]:
            try:
                delete_data = self._parse_delete_result(result["result"])
                delete_result["success"] = delete_data.get("success", False)
                if not delete_result["success"]:
                    delete_result["error"] = delete_data.get("error", "删除失败")
            except Exception as e:
                delete_result["success"] = False
                delete_result["error"] = f"解析删除结果失败: {str(e)}"
        else:
            delete_result["error"] = result.get("error", "删除操作失败")
        
        return delete_result
    
    async def batch_delete_posts(
        self,
        post_ids: List[str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        批量删除微博
        
        Args:
            post_ids: 微博ID列表
            progress_callback: 进度回调函数 (message, current, total)
            
        Returns:
            批量删除结果
        """
        total_posts = len(post_ids)
        successful_deletes = []
        failed_deletes = []
        
        logger.info(f"开始批量删除 {total_posts} 条微博")
        
        for i, post_id in enumerate(post_ids, 1):
            if progress_callback:
                progress_callback(f"删除进度", i, total_posts)
            
            try:
                result = await self.delete_post(
                    post_id,
                    lambda msg: progress_callback(msg, i, total_posts) if progress_callback else None
                )
                
                if result["success"]:
                    successful_deletes.append(result)
                    logger.info(f"成功删除微博: {post_id}")
                else:
                    failed_deletes.append(result)
                    logger.error(f"删除微博失败: {post_id} - {result.get('error')}")
                    
            except Exception as e:
                error_result = {
                    "post_id": post_id,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                failed_deletes.append(error_result)
                logger.error(f"删除微博异常: {post_id} - {str(e)}")
        
        return {
            "total_requested": total_posts,
            "successful_count": len(successful_deletes),
            "failed_count": len(failed_deletes),
            "successful_deletes": successful_deletes,
            "failed_deletes": failed_deletes,
            "completion_time": datetime.now().isoformat()
        }
    
    def _parse_login_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析登录结果"""
        try:
            if isinstance(raw_result, str):
                # 提取JSON部分
                start_idx = raw_result.find('{')
                end_idx = raw_result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = raw_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON数据")
            else:
                result_data = raw_result
            
            return {
                "success": result_data.get("success", False),
                "user_info": result_data.get("user_info", {}),
                "error": result_data.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"解析登录结果时出错: {str(e)}")
            return {
                "success": False,
                "error": f"解析登录结果失败: {str(e)}"
            }
    
    def _parse_weibos_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析微博列表结果"""
        try:
            if isinstance(raw_result, str):
                # 提取JSON部分
                start_idx = raw_result.find('{')
                end_idx = raw_result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = raw_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON数据")
            else:
                result_data = raw_result
            
            weibos = result_data.get("weibos", [])
            
            # 验证和清理数据
            cleaned_weibos = []
            for weibo in weibos:
                if isinstance(weibo, dict) and "id" in weibo:
                    cleaned_weibo = {
                        "id": str(weibo.get("id", "")),
                        "content": str(weibo.get("content", "")),
                        "publish_time": str(weibo.get("publish_time", "")),
                        "repost_count": int(weibo.get("repost_count", 0)),
                        "comment_count": int(weibo.get("comment_count", 0)),
                        "like_count": int(weibo.get("like_count", 0)),
                        "has_media": bool(weibo.get("has_media", False)),
                        "url": str(weibo.get("url", ""))
                    }
                    cleaned_weibos.append(cleaned_weibo)
            
            return {
                "success": True,
                "weibos": cleaned_weibos,
                "total_count": len(cleaned_weibos)
            }
            
        except Exception as e:
            logger.error(f"解析微博列表时出错: {str(e)}")
            return {
                "success": False,
                "error": f"解析微博列表失败: {str(e)}"
            }
    
    def _parse_analysis_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析AI分析结果"""
        try:
            if isinstance(raw_result, str):
                # 提取JSON部分
                start_idx = raw_result.find('{')
                end_idx = raw_result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = raw_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON数据")
            else:
                result_data = raw_result
            
            return {
                "risk_score": min(max(float(result_data.get("risk_score", 0)), 0), 10),
                "risk_reasons": result_data.get("risk_reasons", []),
                "risk_category": str(result_data.get("risk_category", "")),
                "suggestion": str(result_data.get("suggestion", ""))
            }
            
        except Exception as e:
            logger.error(f"解析分析结果时出错: {str(e)}")
            return {
                "risk_score": 0,
                "risk_reasons": ["解析失败"],
                "risk_category": "未知",
                "suggestion": "建议人工审核"
            }
    
    def _parse_delete_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析删除结果"""
        try:
            if isinstance(raw_result, str):
                # 提取JSON部分
                start_idx = raw_result.find('{')
                end_idx = raw_result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = raw_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON数据")
            else:
                result_data = raw_result
            
            return {
                "success": result_data.get("success", False),
                "error": result_data.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"解析删除结果时出错: {str(e)}")
            return {
                "success": False,
                "error": f"解析删除结果失败: {str(e)}"
            }
    
    def _parse_qr_login_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析扫码登录结果"""
        try:
            # 处理AgentHistoryList对象
            if hasattr(raw_result, 'final_result'):
                final_result = raw_result.final_result()
                if final_result:
                    raw_result = final_result
                else:
                    # 如果没有final_result，尝试获取最后的输出
                    if hasattr(raw_result, 'model_outputs') and raw_result.model_outputs():
                        last_output = raw_result.model_outputs()[-1]
                        if hasattr(last_output, 'content'):
                            raw_result = last_output.content
                        else:
                            raw_result = str(last_output)
                    else:
                        # 尝试直接转换为字符串
                        raw_result = str(raw_result)
                        
            # 如果仍然是对象，尝试获取其字符串表示
            if not isinstance(raw_result, str):
                raw_result = str(raw_result)
            
            if isinstance(raw_result, str):
                # 提取JSON部分
                start_idx = raw_result.find('{')
                end_idx = raw_result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = raw_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON数据")
            else:
                result_data = raw_result
            
            return {
                "success": result_data.get("success", False),
                "qr_code": result_data.get("qr_code", ""),
                "qr_status": result_data.get("qr_status", "waiting"),
                "user_info": result_data.get("user_info", {}),
                "error": result_data.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"解析扫码登录结果时出错: {str(e)}")
            # 如果解析失败，返回一个基本的成功状态，让前端可以继续
            logger.warning(f"解析扫码登录结果失败，返回默认状态: {str(e)}")
            return {
                "success": True,
                "qr_code": "generated",
                "qr_status": "waiting",
                "user_info": {},
                "error": f"解析结果时出现问题，但二维码可能已生成: {str(e)}"
            }
    
    def _parse_qr_status_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析二维码状态检查结果"""
        try:
            # 处理AgentHistoryList对象
            if hasattr(raw_result, 'final_result'):
                final_result = raw_result.final_result()
                if final_result:
                    raw_result = final_result
                else:
                    # 如果没有final_result，尝试获取最后的输出
                    if hasattr(raw_result, 'model_outputs') and raw_result.model_outputs():
                        last_output = raw_result.model_outputs()[-1]
                        if hasattr(last_output, 'content'):
                            raw_result = last_output.content
                        else:
                            raw_result = str(last_output)
                    else:
                        raw_result = str(raw_result)
            
            if isinstance(raw_result, str):
                # 提取JSON部分
                start_idx = raw_result.find('{')
                end_idx = raw_result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = raw_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON数据")
            else:
                result_data = raw_result
            
            return {
                "success": result_data.get("success", False),
                "qr_status": result_data.get("qr_status", "waiting"),
                "user_info": result_data.get("user_info", {}),
                "message": result_data.get("message", ""),
                "error": result_data.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"解析二维码状态结果时出错: {str(e)}")
            return {
                "success": False,
                "qr_status": "error",
                "error": f"解析二维码状态结果失败: {str(e)}"
            } 