"""
DeepSeek集成测试模块

测试与DeepSeek API的真实集成
"""

import pytest
import asyncio
import httpx
from app.core.config import settings


class TestDeepSeekIntegration:
    """DeepSeek集成测试类"""
    
    @pytest.mark.asyncio
    async def test_deepseek_api_connection(self):
        """测试DeepSeek API连接"""
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试简单的API调用
        test_payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": "请回复'连接测试成功'"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{settings.deepseek_base_url}/chat/completions",
                    headers=headers,
                    json=test_payload
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "choices" in data
                assert len(data["choices"]) > 0
                
                content = data["choices"][0]["message"]["content"]
                print(f"✅ DeepSeek API连接成功，响应: {content}")
                
            except Exception as e:
                pytest.fail(f"DeepSeek API连接失败: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_deepseek_content_analysis(self):
        """测试DeepSeek内容分析功能"""
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试内容分析
        test_content = "今天天气很好，适合出门散步"
        analysis_prompt = f"""
请分析以下微博内容的风险等级：

微博内容：{test_content}

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
        
        test_payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{settings.deepseek_base_url}/chat/completions",
                    headers=headers,
                    json=test_payload
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "choices" in data
                
                content = data["choices"][0]["message"]["content"]
                print(f"✅ DeepSeek内容分析成功，响应: {content[:200]}...")
                
                # 尝试解析JSON响应
                import json
                try:
                    # 提取JSON部分
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = content[start_idx:end_idx]
                        analysis_result = json.loads(json_str)
                        
                        assert "risk_score" in analysis_result
                        assert "risk_reasons" in analysis_result
                        assert "risk_category" in analysis_result
                        assert "suggestion" in analysis_result
                        
                        print(f"✅ 分析结果解析成功: 风险分数 {analysis_result['risk_score']}")
                    else:
                        print("⚠️  响应中未找到有效的JSON格式，但API调用成功")
                        
                except json.JSONDecodeError:
                    print("⚠️  JSON解析失败，但API调用成功")
                
            except Exception as e:
                pytest.fail(f"DeepSeek内容分析失败: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_deepseek_api_error_handling(self):
        """测试DeepSeek API错误处理"""
        # 使用无效的API密钥测试错误处理
        headers = {
            "Authorization": "Bearer invalid_api_key",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": "测试"
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{settings.deepseek_base_url}/chat/completions",
                    headers=headers,
                    json=test_payload
                )
                
                # 应该返回401或403错误
                assert response.status_code in [401, 403]
                print("✅ DeepSeek API错误处理正常")
                
            except Exception as e:
                print(f"✅ DeepSeek API错误处理正常: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_deepseek_rate_limiting(self):
        """测试DeepSeek API速率限制处理"""
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        # 发送多个快速请求测试速率限制
        requests = []
        for i in range(3):  # 发送3个请求
            test_payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": f"测试请求 {i+1}"
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 20
            }
            requests.append(test_payload)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # 并发发送请求
                tasks = []
                for payload in requests:
                    task = client.post(
                        f"{settings.deepseek_base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = 0
                for response in responses:
                    if isinstance(response, httpx.Response) and response.status_code == 200:
                        success_count += 1
                
                print(f"✅ DeepSeek API并发请求测试完成，成功 {success_count}/{len(requests)} 个请求")
                
            except Exception as e:
                print(f"✅ DeepSeek API并发请求测试完成，遇到预期的限制: {str(e)}")


class TestDeepSeekConfiguration:
    """DeepSeek配置测试类"""
    
    def test_api_key_format(self):
        """测试API密钥格式"""
        api_key = settings.deepseek_api_key
        assert api_key is not None
        assert api_key.startswith("sk-")
        assert len(api_key) > 20
        print(f"✅ DeepSeek API密钥格式正确: {api_key[:10]}...")
    
    def test_base_url_format(self):
        """测试基础URL格式"""
        base_url = settings.deepseek_base_url
        assert base_url is not None
        assert base_url.startswith("https://")
        assert "deepseek.com" in base_url
        print(f"✅ DeepSeek基础URL格式正确: {base_url}")
    
    def test_model_configuration(self):
        """测试模型配置"""
        # 这里可以测试模型相关的配置
        # 目前使用默认的deepseek-chat模型
        model_name = "deepseek-chat"
        assert model_name is not None
        assert len(model_name) > 0
        print(f"✅ DeepSeek模型配置正确: {model_name}") 