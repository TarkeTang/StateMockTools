from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Protocol(Base):
    """协议模型"""
    __tablename__ = "protocols"
    
    id = Column(String, primary_key=True, index=True)  # 协议ID
    name = Column(String, nullable=False)  # 协议名称
    type = Column(String, nullable=False)  # 协议类型
    device_type = Column(String, nullable=False)  # 支持的设备类型
    interaction_object = Column(String, nullable=False)  # 交互对象
    version = Column(String, nullable=False)  # 协议版本
    structure = Column(Text, nullable=False)  # 协议结构
    fields = Column(Text)  # 字段说明（JSON格式）
    description = Column(Text)  # 协议描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间