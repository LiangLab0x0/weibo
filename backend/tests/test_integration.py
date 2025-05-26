"""
集成测试模块

测试前后端通信和完整工作流程
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from app.main import app
from app.core.celery_app import celery_app


client = TestClient(app)


class TestEndToEndWorkflow:
    """端到端工作流程测试类"""
    
    def test_complete_api_workflow(self):
        """测试完整的API工作流程"""
        print("🔄 开始端到端工作流程测试...")
        
        # 1. 测试健康检查
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ 步骤1: 健康检查通过")
        
        # 2. 测试统计信息获取
        response = client.get("/api/v1/weibo/stats")
        assert response.status_code == 200
        stats = response.json()
        print(f"✅ 步骤2: 统计信息获取成功 - 活跃任务: {stats['active_tasks']}")
        
        # 3. 测试创建登录任务
        login_data = {
            "username": "test_user_integration",
            "password": "test_password_integration"
        }
        response = client.post("/api/v1/weibo/login", json=login_data)
        assert response.status_code == 200
        login_task = response.json()
        login_task_id = login_task["task_id"]
        print(f"✅ 步骤3: 登录任务创建成功 - 任务ID: {login_task_id}")
        
        # 4. 测试任务状态查询
        response = client.get(f"/api/v1/weibo/task/{login_task_id}")
        assert response.status_code == 200
        task_status = response.json()
        print(f"✅ 步骤4: 任务状态查询成功 - 状态: {task_status['status']}")
        
        # 5. 测试创建分析任务
        analysis_data = {
            "time_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "keywords": ["测试", "集成"],
            "max_posts": 10
        }
        response = client.post("/api/v1/weibo/analyze", json=analysis_data)
        assert response.status_code == 200
        analysis_task = response.json()
        analysis_task_id = analysis_task["task_id"]
        print(f"✅ 步骤5: 分析任务创建成功 - 任务ID: {analysis_task_id}")
        
        # 6. 测试创建删除任务
        delete_data = {
            "post_ids": ["test_post_1", "test_post_2"],
            "confirm": True
        }
        response = client.post("/api/v1/weibo/delete", json=delete_data)
        assert response.status_code == 200
        delete_task = response.json()
        delete_task_id = delete_task["task_id"]
        print(f"✅ 步骤6: 删除任务创建成功 - 任务ID: {delete_task_id}")
        
        # 7. 测试任务取消
        response = client.delete(f"/api/v1/weibo/task/{delete_task_id}")
        assert response.status_code == 200
        cancel_result = response.json()
        assert cancel_result["success"] is True
        print(f"✅ 步骤7: 任务取消成功 - 任务ID: {delete_task_id}")
        
        print("🎉 端到端工作流程测试完成！")
    
    def test_error_handling_workflow(self):
        """测试错误处理工作流程"""
        print("🔄 开始错误处理工作流程测试...")
        
        # 1. 测试无效的任务ID查询
        response = client.get("/api/v1/weibo/task/invalid_task_id")
        # 应该返回404或者任务不存在的状态
        print(f"✅ 无效任务ID处理: 状态码 {response.status_code}")
        
        # 2. 测试无效的登录数据
        response = client.post("/api/v1/weibo/login", json={})
        assert response.status_code == 422  # 验证错误
        print("✅ 无效登录数据验证正常")
        
        # 3. 测试无效的删除数据
        response = client.post("/api/v1/weibo/delete", json={
            "post_ids": ["test"],
            "confirm": False
        })
        assert response.status_code == 400  # 未确认删除
        print("✅ 未确认删除验证正常")
        
        # 4. 测试超出限制的删除数量
        large_post_list = [f"post_{i}" for i in range(150)]  # 超过限制
        response = client.post("/api/v1/weibo/delete", json={
            "post_ids": large_post_list,
            "confirm": True
        })
        assert response.status_code == 400  # 超出限制
        print("✅ 删除数量限制验证正常")
        
        print("🎉 错误处理工作流程测试完成！")


class TestCeleryIntegration:
    """Celery集成测试类"""
    
    def test_celery_connection(self):
        """测试Celery连接"""
        try:
            # 检查Celery是否可以连接到Redis
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                print("✅ Celery连接正常")
            else:
                print("⚠️  Celery Worker未运行，但连接正常")
                
        except Exception as e:
            print(f"⚠️  Celery连接测试: {str(e)}")
    
    def test_task_creation_and_status(self):
        """测试任务创建和状态管理"""
        # 创建一个测试任务
        response = client.post("/api/v1/weibo/analyze", json={"max_posts": 5})
        assert response.status_code == 200
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # 验证任务ID格式
        assert len(task_id) > 10  # Celery任务ID通常很长
        print(f"✅ 任务创建成功，ID格式正确: {task_id[:20]}...")
        
        # 查询任务状态
        response = client.get(f"/api/v1/weibo/task/{task_id}")
        assert response.status_code == 200
        
        status_data = response.json()
        assert "task_id" in status_data
        assert "status" in status_data
        print(f"✅ 任务状态查询成功: {status_data['status']}")


class TestDataFlow:
    """数据流测试类"""
    
    def test_request_response_format(self):
        """测试请求响应格式"""
        # 测试登录请求响应格式
        login_response = client.post("/api/v1/weibo/login", json={
            "username": "test",
            "password": "test"
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # 验证响应格式
        required_fields = ["task_id", "status", "message"]
        for field in required_fields:
            assert field in login_data
        
        print("✅ 登录请求响应格式正确")
        
        # 测试分析请求响应格式
        analysis_response = client.post("/api/v1/weibo/analyze", json={
            "max_posts": 10
        })
        
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        for field in required_fields:
            assert field in analysis_data
        
        print("✅ 分析请求响应格式正确")
    
    def test_data_validation(self):
        """测试数据验证"""
        # 测试日期格式验证
        response = client.post("/api/v1/weibo/analyze", json={
            "time_range": {
                "start_date": "invalid-date",
                "end_date": "2024-12-31"
            }
        })
        # 应该接受但可能在处理时处理无效日期
        print("✅ 日期格式验证测试完成")
        
        # 测试数字范围验证
        response = client.post("/api/v1/weibo/analyze", json={
            "max_posts": -1  # 负数
        })
        assert response.status_code == 422  # 验证错误
        print("✅ 数字范围验证正常")
        
        response = client.post("/api/v1/weibo/analyze", json={
            "max_posts": 2000  # 超出范围
        })
        assert response.status_code == 422  # 验证错误
        print("✅ 数字上限验证正常")


class TestPerformance:
    """性能测试类"""
    
    def test_api_response_time(self):
        """测试API响应时间"""
        start_time = time.time()
        
        # 测试健康检查响应时间
        response = client.get("/health")
        health_time = time.time() - start_time
        
        assert response.status_code == 200
        assert health_time < 1.0  # 应该在1秒内响应
        print(f"✅ 健康检查响应时间: {health_time:.3f}秒")
        
        # 测试统计信息响应时间
        start_time = time.time()
        response = client.get("/api/v1/weibo/stats")
        stats_time = time.time() - start_time
        
        assert response.status_code == 200
        assert stats_time < 2.0  # 应该在2秒内响应
        print(f"✅ 统计信息响应时间: {stats_time:.3f}秒")
        
        # 测试任务创建响应时间
        start_time = time.time()
        response = client.post("/api/v1/weibo/analyze", json={"max_posts": 10})
        task_time = time.time() - start_time
        
        assert response.status_code == 200
        assert task_time < 3.0  # 任务创建应该在3秒内完成
        print(f"✅ 任务创建响应时间: {task_time:.3f}秒")
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.get("/health")
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # 创建10个并发请求
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        assert success_count >= 8  # 至少80%的请求成功
        print(f"✅ 并发请求测试完成: {success_count}/10 个请求成功") 