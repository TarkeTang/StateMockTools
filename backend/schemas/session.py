from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionBase(BaseModel):
    """会话基础模型"""
    id: str = Field(..., description="会话ID")
    name: str = Field(..., description="会话名称")
    device_id: str = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    ip: Optional[str] = Field(None, description="IP地址")
    port: Optional[int] = Field(None, description="端口")
    timeout: int = Field(default=30, description="超时时间")
    reconnect_count: int = Field(default=3, description="重连次数")
    protocol_type: str = Field(..., description="协议类型")
    send_code: str = Field(..., description="发送标识")
    receive_code: str = Field(..., description="接收标识")
    heartbeat_interval: int = Field(default=30, description="心跳间隔")
    patrol_interval: int = Field(default=5, description="巡视设备运行数据间隔")
    drone_nest_interval: int = Field(default=10, description="无人机机巢运行数据间隔")
    weather_interval: int = Field(default=15, description="微气象数据间隔")
    description: Optional[str] = Field(None, description="描述")


class SessionCreate(BaseModel):
    """创建会话模型"""
    name: str = Field(..., description="会话名称")
    device_id: str = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    ip: Optional[str] = Field(None, description="IP地址")
    port: Optional[int] = Field(None, description="端口")
    timeout: int = Field(default=30, description="超时时间")
    reconnect_count: int = Field(default=3, description="重连次数")
    protocol_type: str = Field(default="", description="协议类型")
    send_code: str = Field(default="", description="发送标识")
    receive_code: str = Field(default="", description="接收标识")
    heartbeat_interval: int = Field(default=30, description="心跳间隔")
    patrol_interval: int = Field(default=5, description="巡视设备运行数据间隔")
    drone_nest_interval: int = Field(default=10, description="无人机机巢运行数据间隔")
    weather_interval: int = Field(default=15, description="微气象数据间隔")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field(default="disconnected", description="会话状态")


class SessionUpdate(BaseModel):
    """更新会话模型"""
    name: Optional[str] = None
    device_type: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    timeout: Optional[int] = None
    reconnect_count: Optional[int] = None
    protocol_type: Optional[str] = None
    send_code: Optional[str] = None
    receive_code: Optional[str] = None
    heartbeat_interval: Optional[int] = None
    patrol_interval: Optional[int] = None
    drone_nest_interval: Optional[int] = None
    weather_interval: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(SessionBase):
    """会话响应模型"""
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SessionMessageBase(BaseModel):
    """会话消息基础模型"""
    session_id: str = Field(..., description="会话ID")
    message_type: str = Field(..., description="消息类型")
    content: str = Field(..., description="消息内容")
    direction: str = Field(..., description="消息方向")


class SessionMessageCreate(SessionMessageBase):
    """创建会话消息模型"""
    pass


class SessionMessageResponse(SessionMessageBase):
    """会话消息响应模型"""
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionWithMessages(SessionResponse):
    """包含消息的会话响应模型"""
    messages: List[SessionMessageResponse] = []


class SessionConnectRequest(BaseModel):
    """会话连接请求模型"""
    session_id: str = Field(..., description="会话 ID")
    ip: Optional[str] = Field(None, description="IP 地址")
    port: Optional[int] = Field(None, description="端口")
    protocol_type: Optional[str] = Field(None, description="协议类型")
    send_code: Optional[str] = Field(None, description="发送标识")
    receive_code: Optional[str] = Field(None, description="接收标识")


class SessionConnectResponse(BaseModel):
    """会话连接响应模型"""
    success: bool = Field(..., description="是否成功")
    session_id: str = Field(..., description="会话 ID")
    status: str = Field(..., description="连接状态")
    message: str = Field(..., description="消息")


class SessionMessagePush(BaseModel):
    """会话消息推送模型"""
    type: str = Field(..., description="消息类型：status/message/error")
    session_id: str = Field(..., description="会话 ID")
    content: Optional[str] = Field(None, description="消息内容")
    direction: Optional[str] = Field(None, description="消息方向：sent/received")
    status: Optional[str] = Field(None, description="连接状态：connecting/connected/disconnected/error")
    message: Optional[str] = Field(None, description="状态消息")
    timestamp: Optional[float] = Field(None, description="时间戳")