from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class TestCase(Base):
    """测试用例模型"""
    __tablename__ = "test_cases"
    
    id = Column(String, primary_key=True, index=True)  # 测试用例ID
    name = Column(String, nullable=False)  # 测试用例名称
    description = Column(Text)  # 测试用例描述
    device_type = Column(String, nullable=False)  # 设备类型
    protocol_id = Column(String, nullable=False)  # 协议ID
    steps = Column(Text, nullable=False)  # 测试步骤
    expected_result = Column(Text, nullable=False)  # 预期结果
    status = Column(String, default="created")  # 测试状态
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间


class TestRun(Base):
    """测试运行记录模型"""
    __tablename__ = "test_runs"
    
    id = Column(String, primary_key=True, index=True)  # 测试运行ID
    test_case_id = Column(String, nullable=False)  # 测试用例ID
    device_id = Column(String, nullable=False)  # 设备ID
    status = Column(String, default="running")  # 运行状态
    result = Column(Text)  # 测试结果
    started_at = Column(DateTime(timezone=True), server_default=func.now())  # 开始时间
    finished_at = Column(DateTime(timezone=True))  # 结束时间