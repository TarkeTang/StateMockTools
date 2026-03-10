from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    """设备基础模型"""
    id: str = Field(..., description="设备唯一标识")
    name: str = Field(..., description="设备名称")
    type: str = Field(..., description="设备类型")
    ip: str = Field(..., description="IP地址")
    port: int = Field(..., description="端口")
    description: Optional[str] = Field(None, description="设备描述")


class DeviceCreate(DeviceBase):
    """创建设备模型"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备模型"""
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None


class DeviceResponse(DeviceBase):
    """设备响应模型"""
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True