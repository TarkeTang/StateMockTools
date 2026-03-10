from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class Device(Base):
    """设备模型"""
    __tablename__ = "devices"
    
    id = Column(String, primary_key=True, index=True)  # 设备唯一标识
    name = Column(String, nullable=False)  # 设备名称
    type = Column(String, nullable=False)  # 设备类型
    ip = Column(String, nullable=False)  # IP地址
    port = Column(Integer, nullable=False)  # 端口
    status = Column(String, default="offline")  # 设备状态
    description = Column(String, nullable=True)  # 设备描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间