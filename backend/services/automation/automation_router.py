from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.automation import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    TestRunCreate, TestRunUpdate, TestRunResponse
)
from services.automation.automation_service import AutomationService
from config.logging import logger

router = APIRouter(
    prefix="/api/automation",
    tags=["automation"],
    responses={404: {"description": "Not found"}},
)


@router.get("/test-cases", response_model=List[TestCaseResponse])
def get_test_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取测试用例列表"""
    logger.info(f"获取测试用例列表，skip: {skip}, limit: {limit}")
    test_cases = AutomationService.get_test_cases(db, skip=skip, limit=limit)
    logger.info(f"获取到 {len(test_cases)} 个测试用例")
    return test_cases


@router.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
def get_test_case(test_case_id: str, db: Session = Depends(get_db)):
    """根据ID获取测试用例"""
    logger.info(f"根据ID获取测试用例: {test_case_id}")
    test_case = AutomationService.get_test_case(db, test_case_id=test_case_id)
    if test_case is None:
        logger.warning(f"测试用例未找到: {test_case_id}")
        raise HTTPException(status_code=404, detail="Test case not found")
    logger.info(f"获取测试用例成功: {test_case_id}")
    return test_case


@router.post("/test-cases", response_model=TestCaseResponse)
def create_test_case(test_case: TestCaseCreate, db: Session = Depends(get_db)):
    """创建测试用例"""
    logger.info(f"创建测试用例请求: {test_case.model_dump()}")
    created_test_case = AutomationService.create_test_case(db=db, test_case=test_case)
    logger.info(f"测试用例创建成功: {created_test_case.id}, 响应: {created_test_case.model_dump()}")
    return created_test_case


@router.put("/test-cases/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(test_case_id: str, test_case: TestCaseUpdate, db: Session = Depends(get_db)):
    """更新测试用例"""
    logger.info(f"更新测试用例请求: test_case_id={test_case_id}, data={test_case.model_dump(exclude_unset=True)}")
    db_test_case = AutomationService.update_test_case(db=db, test_case_id=test_case_id, test_case_update=test_case)
    if db_test_case is None:
        logger.warning(f"测试用例未找到: {test_case_id}")
        raise HTTPException(status_code=404, detail="Test case not found")
    logger.info(f"测试用例更新成功: {test_case_id}, 响应: {db_test_case.model_dump()}")
    return db_test_case


@router.delete("/test-cases/{test_case_id}")
def delete_test_case(test_case_id: str, db: Session = Depends(get_db)):
    """删除测试用例"""
    logger.info(f"删除测试用例: {test_case_id}")
    success = AutomationService.delete_test_case(db=db, test_case_id=test_case_id)
    if not success:
        logger.warning(f"测试用例未找到: {test_case_id}")
        raise HTTPException(status_code=404, detail="Test case not found")
    logger.info(f"测试用例删除成功: {test_case_id}")
    return {"message": "Test case deleted successfully"}


@router.get("/test-runs", response_model=List[TestRunResponse])
def get_test_runs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取测试运行记录列表"""
    logger.info(f"获取测试运行记录列表，skip: {skip}, limit: {limit}")
    test_runs = AutomationService.get_test_runs(db, skip=skip, limit=limit)
    logger.info(f"获取到 {len(test_runs)} 条测试运行记录")
    return test_runs


@router.get("/test-runs/{test_run_id}", response_model=TestRunResponse)
def get_test_run(test_run_id: str, db: Session = Depends(get_db)):
    """根据ID获取测试运行记录"""
    logger.info(f"根据ID获取测试运行记录: {test_run_id}")
    test_run = AutomationService.get_test_run(db, test_run_id=test_run_id)
    if test_run is None:
        logger.warning(f"测试运行记录未找到: {test_run_id}")
        raise HTTPException(status_code=404, detail="Test run not found")
    logger.info(f"获取测试运行记录成功: {test_run_id}")
    return test_run


@router.post("/test-runs", response_model=TestRunResponse)
def create_test_run(test_run: TestRunCreate, db: Session = Depends(get_db)):
    """创建测试运行记录"""
    logger.info(f"创建测试运行记录: {test_run.test_case_id}")
    created_test_run = AutomationService.create_test_run(db=db, test_run=test_run)
    logger.info(f"测试运行记录创建成功: {created_test_run.id}")
    return created_test_run


@router.put("/test-runs/{test_run_id}", response_model=TestRunResponse)
def update_test_run(test_run_id: str, test_run: TestRunUpdate, db: Session = Depends(get_db)):
    """更新测试运行记录"""
    logger.info(f"更新测试运行记录: {test_run_id}")
    db_test_run = AutomationService.update_test_run(db=db, test_run_id=test_run_id, test_run_update=test_run)
    if db_test_run is None:
        logger.warning(f"测试运行记录未找到: {test_run_id}")
        raise HTTPException(status_code=404, detail="Test run not found")
    logger.info(f"测试运行记录更新成功: {test_run_id}")
    return db_test_run


@router.get("/test-cases/{test_case_id}/runs", response_model=List[TestRunResponse])
def get_test_runs_by_test_case(test_case_id: str, db: Session = Depends(get_db)):
    """根据测试用例ID获取测试运行记录列表"""
    logger.info(f"根据测试用例ID获取测试运行记录列表: {test_case_id}")
    test_runs = AutomationService.get_test_runs_by_test_case(db, test_case_id=test_case_id)
    logger.info(f"获取到 {len(test_runs)} 条测试运行记录")
    return test_runs


@router.get("/devices/{device_id}/runs", response_model=List[TestRunResponse])
def get_test_runs_by_device(device_id: str, db: Session = Depends(get_db)):
    """根据设备ID获取测试运行记录列表"""
    logger.info(f"根据设备ID获取测试运行记录列表: {device_id}")
    test_runs = AutomationService.get_test_runs_by_device(db, device_id=device_id)
    logger.info(f"获取到 {len(test_runs)} 条测试运行记录")
    return test_runs


@router.post("/test-cases/{test_case_id}/execute", response_model=TestRunResponse)
def execute_test_case(test_case_id: str, device_id: str, db: Session = Depends(get_db)):
    """执行测试用例"""
    logger.info(f"执行测试用例: {test_case_id}, 设备: {device_id}")
    # 验证测试用例是否存在
    test_case = AutomationService.get_test_case(db, test_case_id=test_case_id)
    if test_case is None:
        logger.warning(f"测试用例未找到: {test_case_id}")
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # 执行测试用例
    test_run = AutomationService.execute_test_case(db, test_case_id=test_case_id, device_id=device_id)
    logger.info(f"测试用例执行成功: {test_case_id}, 运行ID: {test_run.id}")
    return test_run