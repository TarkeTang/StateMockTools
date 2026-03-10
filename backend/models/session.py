from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Session(Base):
    """会话模型"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)  # 会话ID
    name = Column(String, nullable=False)  # 会话名称
    device_id = Column(String, ForeignKey("devices.id"))  # 设备ID
    device_type = Column(String, nullable=False)  # 设备类型
    ip = Column(String)  # IP地址
    port = Column(Integer)  # 端口
    timeout = Column(Integer, default=30)  # 超时时间
    reconnect_count = Column(Integer, default=3)  # 重连次数
    protocol_type = Column(String, nullable=False)  # 协议类型
    send_code = Column(String, nullable=False)  # 发送标识
    receive_code = Column(String, nullable=False)  # 接收标识
    heartbeat_interval = Column(Integer, default=30)  # 心跳间隔
    patrol_interval = Column(Integer, default=5)  # 巡视设备运行数据间隔
    drone_nest_interval = Column(Integer, default=10)  # 无人机机巢运行数据间隔
    weather_interval = Column(Integer, default=15)  # 微气象数据间隔
    description = Column(String)  # 描述
    status = Column(String, default="disconnected")  # 会话状态
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间


class SessionMessage(Base):
    """会话消息模型"""
    __tablename__ = "session_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 消息ID
    session_id = Column(String, ForeignKey("sessions.id"))  # 会话ID
    message_type = Column(String, nullable=False)  # 消息类型
    content = Column(String, nullable=False)  # 消息内容
    direction = Column(String, nullable=False)  # 消息方向（发送/接收）
    status = Column(String, default="sent")  # 消息状态
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间