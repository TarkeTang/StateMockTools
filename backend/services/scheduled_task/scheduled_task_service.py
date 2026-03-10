from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from models.scheduled_task import ScheduledTask
from schemas.scheduled_task import ScheduledTaskCreate, ScheduledTaskUpdate
from config.logging import logger
from datetime import datetime, timedelta
import asyncio


class ScheduledTaskService:
    """周期任务服务类"""

    @staticmethod
    def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[ScheduledTask]:
        """获取任务列表"""
        logger.debug(f"获取任务列表，skip: {skip}, limit: {limit}")
        tasks = db.query(ScheduledTask).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(tasks)} 个任务")
        return tasks

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[ScheduledTask]:
        """根据 ID 获取任务"""
        logger.debug(f"根据 ID 获取任务：{task_id}")
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        logger.debug(f"获取任务结果：{'成功' if task else '失败'}")
        return task

    @staticmethod
    def get_tasks_by_session(db: Session, session_id: str) -> List[ScheduledTask]:
        """根据会话 ID 获取任务"""
        logger.debug(f"根据会话 ID 获取任务：{session_id}")
        tasks = db.query(ScheduledTask).filter(ScheduledTask.session_id == session_id).all()
        logger.debug(f"获取到 {len(tasks)} 个任务")
        return tasks

    @staticmethod
    def get_enabled_tasks(db: Session) -> List[ScheduledTask]:
        """获取所有启用的任务"""
        logger.debug("获取启用的任务")
        tasks = db.query(ScheduledTask).filter(
            ScheduledTask.enabled == True,
            ScheduledTask.running == True
        ).all()
        logger.debug(f"获取到 {len(tasks)} 个启用的任务")
        return tasks

    @staticmethod
    def create_task(db: Session, task: ScheduledTaskCreate) -> ScheduledTask:
        """创建任务"""
        logger.debug(f"创建任务：{task.name}")
        db_task = ScheduledTask(**task.model_dump())
        # 计算下次执行时间
        db_task.next_run = datetime.now() + timedelta(seconds=task.interval)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        logger.debug(f"任务创建成功：{db_task.id}")
        return db_task

    @staticmethod
    def update_task(db: Session, task_id: int, task_update: ScheduledTaskUpdate) -> Optional[ScheduledTask]:
        """更新任务"""
        logger.debug(f"更新任务：{task_id}")
        db_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if db_task:
            update_data = task_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_task, field, value)
            db.commit()
            db.refresh(db_task)
            logger.debug(f"任务更新成功：{task_id}")
        else:
            logger.debug(f"任务未找到：{task_id}")
        return db_task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """删除任务"""
        logger.debug(f"删除任务：{task_id}")
        db_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if db_task:
            db.delete(db_task)
            db.commit()
            logger.debug(f"任务删除成功：{task_id}")
            return True
        logger.debug(f"任务未找到：{task_id}")
        return False

    @staticmethod
    def start_task(db: Session, task_id: int) -> Optional[ScheduledTask]:
        """启动任务"""
        logger.debug(f"启动任务：{task_id}")
        db_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if db_task:
            db_task.running = True
            db_task.next_run = datetime.now() + timedelta(seconds=db_task.interval)
            db.commit()
            db.refresh(db_task)
            logger.debug(f"任务启动成功：{task_id}")
        else:
            logger.debug(f"任务未找到：{task_id}")
        return db_task

    @staticmethod
    def stop_task(db: Session, task_id: int) -> Optional[ScheduledTask]:
        """停止任务"""
        logger.debug(f"停止任务：{task_id}")
        db_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if db_task:
            db_task.running = False
            db_task.next_run = None
            db.commit()
            db.refresh(db_task)
            logger.debug(f"任务停止成功：{task_id}")
        else:
            logger.debug(f"任务未找到：{task_id}")
        return db_task

    @staticmethod
    def record_execution(db: Session, task_id: int):
        """记录任务执行"""
        logger.debug(f"记录任务执行：{task_id}")
        db_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if db_task:
            db_task.last_run = datetime.now()
            db_task.next_run = datetime.now() + timedelta(seconds=db_task.interval)
            db_task.execution_count += 1
            db.commit()
            logger.debug(f"任务执行记录成功：{task_id}")
