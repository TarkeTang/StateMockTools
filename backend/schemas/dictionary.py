from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DictionaryBase(BaseModel):
    """字典基础模型"""
    type: str = Field(..., description="类型")
    code: str = Field(..., description="编码")
    name: str = Field(..., description="名称")
    description: Optional[str] = Field(None, description="描述")


class DictionaryCreate(DictionaryBase):
    """创建字典模型"""
    pass


class DictionaryUpdate(BaseModel):
    """更新字典模型"""
    type: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class DictionaryResponse(DictionaryBase):
    """字典响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
