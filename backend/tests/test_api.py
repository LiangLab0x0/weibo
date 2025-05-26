"""
API测试模块

测试所有微博管理API端点
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import LoginRequest, AnalysisRequest, DeleteRequest


client = TestClient(app)


class TestWeiboAPI:
    """微博API测试类"""
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ 健康检查端点正常")
    
    def test_api_docs_accessible(self):
        """测试API文档是否可访问"""
        response = client.get("/docs")
        assert response.status_code == 200
        print("✅ API文档可正常访问")
    
    def test_stats_endpoint(self):
        """测试统计信息端点"""
        response = client.get("/api/v1/weibo/stats")
        assert response.status_code == 200
        data = response.json()
        assert "active_tasks" in data
        assert "max_delete_per_hour" in data
        print(f"✅ 统计信息端点正常: {data}")
    
    def test_login_endpoint_validation(self):
        """测试登录端点参数验证"""
        # 测试空请求
        response = client.post("/api/v1/weibo/login", json={})
        assert response.status_code == 422  # 验证错误
        
        # 测试缺少密码
        response = client.post("/api/v1/weibo/login", json={"username": "test"})
        assert response.status_code == 422
        
        # 测试有效请求格式
        response = client.post("/api/v1/weibo/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        print(f"✅ 登录端点验证正常，任务ID: {data['task_id']}")
    
    def test_analyze_endpoint_validation(self):
        """测试分析端点参数验证"""
        # 测试空请求
        response = client.post("/api/v1/weibo/analyze", json={})
        assert response.status_code == 200  # 空请求应该使用默认值
        
        # 测试有效请求
        response = client.post("/api/v1/weibo/analyze", json={
            "time_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "keywords": ["测试", "关键词"],
            "max_posts": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        print(f"✅ 分析端点验证正常，任务ID: {data['task_id']}")
    
    def test_delete_endpoint_validation(self):
        """测试删除端点参数验证"""
        # 测试空请求
        response = client.post("/api/v1/weibo/delete", json={})
        assert response.status_code == 422
        
        # 测试未确认删除
        response = client.post("/api/v1/weibo/delete", json={
            "post_ids": ["test_id_1", "test_id_2"],
            "confirm": False
        })
        assert response.status_code == 400
        
        # 测试有效请求
        response = client.post("/api/v1/weibo/delete", json={
            "post_ids": ["test_id_1", "test_id_2"],
            "confirm": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        print(f"✅ 删除端点验证正常，任务ID: {data['task_id']}")
    
    def test_task_status_endpoint(self):
        """测试任务状态查询端点"""
        # 创建一个测试任务
        response = client.post("/api/v1/weibo/analyze", json={"max_posts": 10})
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # 查询任务状态
        response = client.get(f"/api/v1/weibo/task/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        print(f"✅ 任务状态查询正常: {data['status']}")
    
    def test_cancel_task_endpoint(self):
        """测试取消任务端点"""
        # 创建一个测试任务
        response = client.post("/api/v1/weibo/analyze", json={"max_posts": 10})
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # 取消任务
        response = client.delete(f"/api/v1/weibo/task/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"✅ 任务取消功能正常，任务ID: {task_id}")


class TestDataModels:
    """数据模型测试类"""
    
    def test_login_request_model(self):
        """测试登录请求模型"""
        # 有效数据
        data = {"username": "test_user", "password": "test_password"}
        request = LoginRequest(**data)
        assert request.username == "test_user"
        assert request.password == "test_password"
        print("✅ 登录请求模型验证正常")
    
    def test_analysis_request_model(self):
        """测试分析请求模型"""
        # 有效数据
        data = {
            "time_range": {"start_date": "2024-01-01", "end_date": "2024-12-31"},
            "keywords": ["测试"],
            "max_posts": 100
        }
        request = AnalysisRequest(**data)
        assert request.max_posts == 100
        assert len(request.keywords) == 1
        print("✅ 分析请求模型验证正常")
    
    def test_delete_request_model(self):
        """测试删除请求模型"""
        # 有效数据
        data = {"post_ids": ["id1", "id2"], "confirm": True}
        request = DeleteRequest(**data)
        assert len(request.post_ids) == 2
        assert request.confirm is True
        print("✅ 删除请求模型验证正常") 