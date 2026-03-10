from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ScheduledTaskBase(BaseModel):
    """周期任务基础模型"""
    name: str = Field(..., description="任务名称")
    session_id: str = Field(..., description="关联会话 ID")
    interval: int = Field(..., ge=1, le=86400, description="周期时间（秒）")
    message: str = Field(..., description="预设消息内容")
    description: Optional[str] = Field(None, description="任务描述")
    enabled: bool = Field(True, description="是否启用")


class ScheduledTaskCreate(ScheduledTaskBase):
    """创建周期任务模型"""
    pass


class ScheduledTaskUpdate(BaseModel):
    """更新周期任务模型"""
    name: Optional[str] = None
    session_id: Optional[str] = None
    interval: Optional[int] = None
    message: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    running: Optional[bool] = None


class ScheduledTaskResponse(ScheduledTaskBase):
    """周期任务响应模型"""
    id: int
    running: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    execution_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduledTaskStartRequest(BaseModel):
    """启动任务请求"""
    session_id: str = Field(..., description="会话 ID")
