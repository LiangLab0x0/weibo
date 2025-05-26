"""
AI代理测试模块

测试微博代理的核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.weibo_agent import WeiboAgent
from app.agents.base_agent import BaseAgent


class TestBaseAgent:
    """基础代理测试类"""
    
    def test_base_agent_initialization(self):
        """测试基础代理初始化"""
        agent = BaseAgent(
            task_description="测试代理",
            temperature=0.1,
            max_retries=3
        )
        assert agent.task_description == "测试代理"
        assert agent.temperature == 0.1
        assert agent.max_retries == 3
        print("✅ 基础代理初始化正常")


class TestWeiboAgent:
    """微博代理测试类"""
    
    def test_weibo_agent_initialization(self):
        """测试微博代理初始化"""
        agent = WeiboAgent()
        assert agent.task_description == "微博内容智能管理代理"
        assert agent.temperature == 0.1
        assert agent.max_retries == 3
        assert agent.is_logged_in is False
        assert agent.user_info == {}
        print("✅ 微博代理初始化正常")
    
    def test_parse_login_result_valid_json(self):
        """测试解析有效的登录结果JSON"""
        agent = WeiboAgent()
        
        # 测试有效的JSON字符串
        raw_result = '{"success": true, "user_info": {"nickname": "测试用户", "followers_count": "100"}}'
        result = agent._parse_login_result(raw_result)
        
        assert result["success"] is True
        assert result["user_info"]["nickname"] == "测试用户"
        print("✅ 登录结果JSON解析正常")
    
    def test_parse_login_result_embedded_json(self):
        """测试解析嵌入在文本中的JSON"""
        agent = WeiboAgent()
        
        # 测试嵌入在文本中的JSON
        raw_result = '这是一些前置文本 {"success": true, "user_info": {"nickname": "测试用户"}} 这是一些后置文本'
        result = agent._parse_login_result(raw_result)
        
        assert result["success"] is True
        assert result["user_info"]["nickname"] == "测试用户"
        print("✅ 嵌入式JSON解析正常")
    
    def test_parse_login_result_invalid_json(self):
        """测试解析无效的JSON"""
        agent = WeiboAgent()
        
        # 测试无效的JSON
        raw_result = "这不是有效的JSON数据"
        result = agent._parse_login_result(raw_result)
        
        assert result["success"] is False
        assert "error" in result
        print("✅ 无效JSON错误处理正常")
    
    def test_parse_weibos_result_valid(self):
        """测试解析有效的微博列表结果"""
        agent = WeiboAgent()
        
        raw_result = {
            "success": True,
            "weibos": [
                {
                    "id": "test_id_1",
                    "content": "测试微博内容1",
                    "publish_time": "2024-01-01 12:00:00",
                    "repost_count": 10,
                    "comment_count": 5,
                    "like_count": 20,
                    "has_media": False,
                    "url": "https://weibo.com/test1"
                },
                {
                    "id": "test_id_2",
                    "content": "测试微博内容2",
                    "publish_time": "2024-01-02 12:00:00",
                    "repost_count": 15,
                    "comment_count": 8,
                    "like_count": 25,
                    "has_media": True,
                    "url": "https://weibo.com/test2"
                }
            ]
        }
        
        result = agent._parse_weibos_result(raw_result)
        
        assert result["success"] is True
        assert len(result["weibos"]) == 2
        assert result["weibos"][0]["id"] == "test_id_1"
        assert result["weibos"][1]["has_media"] is True
        print("✅ 微博列表解析正常")
    
    def test_parse_analysis_result_valid(self):
        """测试解析有效的分析结果"""
        agent = WeiboAgent()
        
        raw_result = {
            "risk_score": 7.5,
            "risk_reasons": ["包含敏感词汇", "可能引起争议"],
            "risk_category": "政治敏感",
            "suggestion": "建议删除"
        }
        
        result = agent._parse_analysis_result(raw_result)
        
        assert result["risk_score"] == 7.5
        assert len(result["risk_reasons"]) == 2
        assert result["risk_category"] == "政治敏感"
        assert result["suggestion"] == "建议删除"
        print("✅ 分析结果解析正常")
    
    def test_parse_analysis_result_score_bounds(self):
        """测试分析结果分数边界处理"""
        agent = WeiboAgent()
        
        # 测试超出上限的分数
        raw_result = {"risk_score": 15.0}
        result = agent._parse_analysis_result(raw_result)
        assert result["risk_score"] == 10.0
        
        # 测试低于下限的分数
        raw_result = {"risk_score": -5.0}
        result = agent._parse_analysis_result(raw_result)
        assert result["risk_score"] == 0.0
        
        print("✅ 分析结果分数边界处理正常")
    
    def test_simple_risk_analysis(self):
        """测试简单风险分析功能"""
        agent = WeiboAgent()
        
        # 测试高风险关键词
        weibo = {
            "id": "test_id",
            "content": "这是一条包含政治敏感内容的微博",
            "publish_time": "2024-01-01 12:00:00"
        }
        
        result = agent._simple_risk_analysis(weibo)
        
        assert result["risk_score"] >= 7  # 高风险
        assert "政治" in result["risk_reason"]
        print("✅ 简单风险分析功能正常")
    
    def test_simple_risk_analysis_safe_content(self):
        """测试安全内容的风险分析"""
        agent = WeiboAgent()
        
        # 测试安全内容
        weibo = {
            "id": "test_id",
            "content": "今天天气真好，心情很愉快",
            "publish_time": "2024-01-01 12:00:00"
        }
        
        result = agent._simple_risk_analysis(weibo)
        
        assert result["risk_score"] <= 3  # 低风险
        assert "安全" in result["risk_reason"]
        print("✅ 安全内容风险分析正常")


class TestAgentIntegration:
    """代理集成测试类"""
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """测试代理错误处理"""
        agent = WeiboAgent()
        
        # 测试未登录状态下的操作
        result = await agent.get_user_weibos()
        assert result["success"] is False
        assert "请先登录" in result["error"]
        print("✅ 未登录状态错误处理正常")
    
    def test_agent_state_management(self):
        """测试代理状态管理"""
        agent = WeiboAgent()
        
        # 初始状态
        assert agent.is_logged_in is False
        assert agent.user_info == {}
        
        # 模拟登录成功
        agent.is_logged_in = True
        agent.user_info = {"nickname": "测试用户"}
        
        assert agent.is_logged_in is True
        assert agent.user_info["nickname"] == "测试用户"
        print("✅ 代理状态管理正常") 