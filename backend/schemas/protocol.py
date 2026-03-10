from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class FieldInfo(BaseModel):
    """字段信息模型"""
    name: str
    type: str
    length: str
    required: str
    description: str


class ProtocolBase(BaseModel):
    """协议基础模型"""
    id: str = Field(..., description="协议ID")
    name: str = Field(..., description="协议名称")
    type: str = Field(..., description="协议类型")
    device_type: str = Field(..., description="支持的设备类型")
    interaction_object: str = Field(..., description="交互对象")
    version: str = Field(..., description="协议版本")
    structure: str = Field(..., description="协议结构")
    fields: Optional[List[Dict[str, Any]]] = Field(None, description="字段说明")
    description: Optional[str] = Field(None, description="协议描述")


class ProtocolCreate(ProtocolBase):
    """创建协议模型"""
    pass


class ProtocolUpdate(BaseModel):
    """更新协议模型"""
    name: Optional[str] = None
    type: Optional[str] = None
    device_type: Optional[str] = None
    interaction_object: Optional[str] = None
    version: Optional[str] = None
    structure: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None


class ProtocolResponse(ProtocolBase):
    """协议响应模型"""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True