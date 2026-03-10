from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from database import Base


class Dictionary(Base):
    """字典表模型"""
    __tablename__ = "dictionary"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 序号
    type = Column(String, nullable=False, index=True)  # 类型
    code = Column(String, nullable=False, index=True)  # 编码
    name = Column(String, nullable=False)  # 名称
    description = Column(String, nullable=True)  # 描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间
