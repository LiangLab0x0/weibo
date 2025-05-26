"""
应用配置管理模块

使用pydantic-settings管理环境变量配置
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = Field(default="微博AI内容管理器", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="VERSION")
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./weibo_manager.db", 
        alias="DATABASE_URL"
    )
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
    # DeepSeek API配置
    deepseek_api_key: str = Field(alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", 
        alias="DEEPSEEK_BASE_URL"
    )
    
    # JWT配置
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, 
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # 微博操作限制
    max_delete_per_hour: int = Field(default=100, alias="MAX_DELETE_PER_HOUR")
    operation_delay_min: int = Field(default=2, alias="OPERATION_DELAY_MIN")
    operation_delay_max: int = Field(default=10, alias="OPERATION_DELAY_MAX")
    
    # 前端配置
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings() 