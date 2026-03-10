from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.sql import func
from database import Base


class Parameter(Base):
    """参数化配置模型"""
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 参数 ID
    name = Column(String, nullable=False, index=True)  # 参数名称（如 ${timestamp}）
    param_type = Column(String, nullable=False)  # 参数类型：timestamp/datetime/custom/random
    format = Column(String)  # 格式（如 %Y-%m-%d %H:%M:%S 或 yyyy-MM-dd HH:mm:ss）
    value = Column(String)  # 自定义值或随机值范围
    description = Column(Text)  # 参数描述
    enabled = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间
