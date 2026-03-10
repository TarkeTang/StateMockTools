from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TestCaseBase(BaseModel):
    """测试用例基础模型"""
    id: str = Field(..., description="测试用例ID")
    name: str = Field(..., description="测试用例名称")
    description: Optional[str] = Field(None, description="测试用例描述")
    device_type: str = Field(..., description="设备类型")
    protocol_id: str = Field(..., description="协议ID")
    steps: str = Field(..., description="测试步骤")
    expected_result: str = Field(..., description="预期结果")


class TestCaseCreate(TestCaseBase):
    """创建测试用例模型"""
    pass


class TestCaseUpdate(BaseModel):
    """更新测试用例模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    device_type: Optional[str] = None
    protocol_id: Optional[str] = None
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    status: Optional[str] = None


class TestCaseResponse(TestCaseBase):
    """测试用例响应模型"""
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TestRunBase(BaseModel):
    """测试运行基础模型"""
    id: str = Field(..., description="测试运行ID")
    test_case_id: str = Field(..., description="测试用例ID")
    device_id: str = Field(..., description="设备ID")


class TestRunCreate(TestRunBase):
    """创建测试运行模型"""
    pass


class TestRunUpdate(BaseModel):
    """更新测试运行模型"""
    status: Optional[str] = None
    result: Optional[str] = None
    finished_at: Optional[datetime] = None


class TestRunResponse(TestRunBase):
    """测试运行响应模型"""
    status: str
    result: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True