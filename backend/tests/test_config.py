"""
配置测试模块

测试应用配置和环境变量加载
"""

import pytest
import os
from app.core.config import settings


class TestConfig:
    """配置测试类"""
    
    def test_deepseek_api_key_loaded(self):
        """测试DeepSeek API密钥是否正确加载"""
        assert settings.deepseek_api_key is not None
        assert settings.deepseek_api_key != "your_deepseek_api_key_here"
        assert settings.deepseek_api_key.startswith("sk-")
        print(f"✅ DeepSeek API密钥已正确配置: {settings.deepseek_api_key[:10]}...")
    
    def test_secret_key_loaded(self):
        """测试安全密钥是否正确加载"""
        assert settings.secret_key is not None
        assert settings.secret_key != "your_secret_key_here"
        assert len(settings.secret_key) > 10
        print(f"✅ 安全密钥已正确配置: {settings.secret_key[:10]}...")
    
    def test_redis_url_configured(self):
        """测试Redis URL配置"""
        assert settings.redis_url is not None
        assert "redis://" in settings.redis_url
        print(f"✅ Redis URL已配置: {settings.redis_url}")
    
    def test_operation_limits(self):
        """测试操作限制配置"""
        assert settings.max_delete_per_hour > 0
        assert settings.operation_delay_min >= 0
        assert settings.operation_delay_max > settings.operation_delay_min
        print(f"✅ 操作限制配置正确: 每小时最大删除{settings.max_delete_per_hour}条，延迟{settings.operation_delay_min}-{settings.operation_delay_max}秒")
    
    def test_deepseek_base_url(self):
        """测试DeepSeek基础URL配置"""
        assert settings.deepseek_base_url is not None
        assert "deepseek.com" in settings.deepseek_base_url
        print(f"✅ DeepSeek基础URL已配置: {settings.deepseek_base_url}") 