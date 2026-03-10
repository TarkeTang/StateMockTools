from typing import List, Optional
from sqlalchemy.orm import Session
from models.automation import TestCase, TestRun
from schemas.automation import TestCaseCreate, TestCaseUpdate, TestRunCreate, TestRunUpdate
from config.logging import logger
import time


class AutomationService:
    """自动化测试服务类"""
    
    @staticmethod
    def get_test_cases(db: Session, skip: int = 0, limit: int = 100) -> List[TestCase]:
        """获取测试用例列表"""
        logger.debug(f"获取测试用例列表，skip: {skip}, limit: {limit}")
        test_cases = db.query(TestCase).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(test_cases)} 个测试用例")
        return test_cases
    
    @staticmethod
    def get_test_case(db: Session, test_case_id: str) -> Optional[TestCase]:
        """根据ID获取测试用例"""
        logger.debug(f"根据ID获取测试用例: {test_case_id}")
        test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        logger.debug(f"获取测试用例结果: {'成功' if test_case else '失败'}")
        return test_case
    
    @staticmethod
    def create_test_case(db: Session, test_case: TestCaseCreate) -> TestCase:
        """创建测试用例"""
        logger.debug(f"创建测试用例: {test_case.name}")
        db_test_case = TestCase(**test_case.model_dump())
        db.add(db_test_case)
        db.commit()
        db.refresh(db_test_case)
        logger.debug(f"测试用例创建成功: {db_test_case.id}")
        return db_test_case
    
    @staticmethod
    def update_test_case(db: Session, test_case_id: str, test_case_update: TestCaseUpdate) -> Optional[TestCase]:
        """更新测试用例"""
        logger.debug(f"更新测试用例: {test_case_id}")
        db_test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        if db_test_case:
            update_data = test_case_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_test_case, field, value)
            db.commit()
            db.refresh(db_test_case)
            logger.debug(f"测试用例更新成功: {test_case_id}")
        else:
            logger.debug(f"测试用例未找到: {test_case_id}")
        return db_test_case
    
    @staticmethod
    def delete_test_case(db: Session, test_case_id: str) -> bool:
        """删除测试用例"""
        logger.debug(f"删除测试用例: {test_case_id}")
        db_test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        if db_test_case:
            # 先删除相关的测试运行记录
            db.query(TestRun).filter(TestRun.test_case_id == test_case_id).delete()
            db.delete(db_test_case)
            db.commit()
            logger.debug(f"测试用例删除成功: {test_case_id}")
            return True
        logger.debug(f"测试用例未找到: {test_case_id}")
        return False
    
    @staticmethod
    def get_test_runs(db: Session, skip: int = 0, limit: int = 100) -> List[TestRun]:
        """获取测试运行记录列表"""
        logger.debug(f"获取测试运行记录列表，skip: {skip}, limit: {limit}")
        test_runs = db.query(TestRun).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(test_runs)} 条测试运行记录")
        return test_runs
    
    @staticmethod
    def get_test_run(db: Session, test_run_id: str) -> Optional[TestRun]:
        """根据ID获取测试运行记录"""
        logger.debug(f"根据ID获取测试运行记录: {test_run_id}")
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        logger.debug(f"获取测试运行记录结果: {'成功' if test_run else '失败'}")
        return test_run
    
    @staticmethod
    def create_test_run(db: Session, test_run: TestRunCreate) -> TestRun:
        """创建测试运行记录"""
        logger.debug(f"创建测试运行记录: {test_run.test_case_id}")
        db_test_run = TestRun(**test_run.model_dump())
        db.add(db_test_run)
        db.commit()
        db.refresh(db_test_run)
        logger.debug(f"测试运行记录创建成功: {db_test_run.id}")
        return db_test_run
    
    @staticmethod
    def update_test_run(db: Session, test_run_id: str, test_run_update: TestRunUpdate) -> Optional[TestRun]:
        """更新测试运行记录"""
        logger.debug(f"更新测试运行记录: {test_run_id}")
        db_test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if db_test_run:
            update_data = test_run_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_test_run, field, value)
            db.commit()
            db.refresh(db_test_run)
            logger.debug(f"测试运行记录更新成功: {test_run_id}")
        else:
            logger.debug(f"测试运行记录未找到: {test_run_id}")
        return db_test_run
    
    @staticmethod
    def get_test_runs_by_test_case(db: Session, test_case_id: str) -> List[TestRun]:
        """根据测试用例ID获取测试运行记录列表"""
        logger.debug(f"根据测试用例ID获取测试运行记录列表: {test_case_id}")
        test_runs = db.query(TestRun).filter(TestRun.test_case_id == test_case_id).all()
        logger.debug(f"获取到 {len(test_runs)} 条测试运行记录")
        return test_runs
    
    @staticmethod
    def get_test_runs_by_device(db: Session, device_id: str) -> List[TestRun]:
        """根据设备ID获取测试运行记录列表"""
        logger.debug(f"根据设备ID获取测试运行记录列表: {device_id}")
        test_runs = db.query(TestRun).filter(TestRun.device_id == device_id).all()
        logger.debug(f"获取到 {len(test_runs)} 条测试运行记录")
        return test_runs
    
    @staticmethod
    def execute_test_case(db: Session, test_case_id: str, device_id: str) -> TestRun:
        """执行测试用例"""
        logger.info(f"执行测试用例: {test_case_id}, 设备: {device_id}")
        # 创建测试运行记录
        test_run_id = f"RUN-{int(time.time() * 1000)}"
        test_run = TestRunCreate(
            id=test_run_id,
            test_case_id=test_case_id,
            device_id=device_id
        )
        db_test_run = AutomationService.create_test_run(db, test_run)
        
        # 这里可以添加测试执行逻辑
        # 例如发送测试指令、接收响应、验证结果等
        
        # 模拟测试执行
        logger.debug("开始执行测试用例")
        import time
        time.sleep(2)  # 模拟测试执行时间
        logger.debug("测试用例执行完成")
        
        # 更新测试运行状态
        test_run_update = TestRunUpdate(
            status="completed",
            result="测试通过",
            finished_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        db_test_run = AutomationService.update_test_run(db, test_run_id, test_run_update)
        
        logger.info(f"测试用例执行成功: {test_case_id}, 运行ID: {test_run_id}")
        return db_test_run