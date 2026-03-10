import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """系统配置类"""
    # 应用配置
    APP_NAME: str = "StateMockTools"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./database/state_mock_new.db"
    
    # 缓存配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 消息队列配置
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # 会话配置
    SESSION_TIMEOUT: int = 3600  # 会话超时时间（秒）
    HEARTBEAT_INTERVAL: int = 30  # 心跳间隔（秒）
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # 服务配置
    SERVICES: Dict[str, Dict[str, str]] = {
        "session": {
            "host": "0.0.0.0",
            "port": "8000"
        },
        "device": {
            "host": "0.0.0.0",
            "port": "8001"
        },
        "protocol": {
            "host": "0.0.0.0",
            "port": "8002"
        },
        "automation": {
            "host": "0.0.0.0",
            "port": "8003"
        }
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """获取配置单例"""
    return Settings()


settings = get_settings()