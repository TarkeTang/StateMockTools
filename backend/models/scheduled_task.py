from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from database import Base


class ScheduledTask(Base):
    """周期任务模型"""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 任务 ID
    name = Column(String, nullable=False)  # 任务名称
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)  # 关联会话 ID
    interval = Column(Integer, nullable=False, default=5)  # 周期时间（秒）
    message = Column(Text, nullable=False)  # 预设消息内容
    enabled = Column(Boolean, default=True)  # 是否启用
    running = Column(Boolean, default=False)  # 是否运行中
    last_run = Column(DateTime(timezone=True), nullable=True)  # 最后执行时间
    next_run = Column(DateTime(timezone=True), nullable=True)  # 下次执行时间
    execution_count = Column(Integer, default=0)  # 执行次数
    description = Column(Text, nullable=True)  # 任务描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间
