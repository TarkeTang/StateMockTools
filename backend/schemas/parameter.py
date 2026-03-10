from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ParameterBase(BaseModel):
    """参数基础模型"""
    name: str = Field(..., description="参数名称（如 ${timestamp}）")
    param_type: str = Field(..., description="参数类型：timestamp/datetime/custom/random")
    format: Optional[str] = Field(None, description="格式（如 %Y-%m-%d %H:%M:%S）")
    value: Optional[str] = Field(None, description="自定义值或随机值范围")
    description: Optional[str] = Field(None, description="参数描述")
    enabled: bool = Field(True, description="是否启用")


class ParameterCreate(ParameterBase):
    """创建参数模型"""
    pass


class ParameterUpdate(BaseModel):
    """更新参数模型"""
    name: Optional[str] = None
    param_type: Optional[str] = None
    format: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class ParameterResponse(ParameterBase):
    """参数响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParameterTestRequest(BaseModel):
    """参数测试请求"""
    content: str = Field(..., description="包含参数的消息内容")


class ParameterTestResponse(BaseModel):
    """参数测试响应"""
    original: str = Field(..., description="原始内容")
    replaced: str = Field(..., description="替换后内容")
    parameters: list = Field(default_factory=list, description="使用的参数列表")
