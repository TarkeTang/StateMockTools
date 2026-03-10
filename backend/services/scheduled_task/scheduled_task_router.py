from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.scheduled_task import (
    ScheduledTaskCreate, ScheduledTaskUpdate, ScheduledTaskResponse
)
from services.scheduled_task.scheduled_task_service import ScheduledTaskService
from services.scheduled_task.scheduled_task_scheduler import scheduler
from config.logging import logger

router = APIRouter(
    prefix="/api/scheduled-tasks",
    tags=["scheduled_task"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[ScheduledTaskResponse])
def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取周期任务列表"""
    logger.info(f"获取周期任务列表，skip: {skip}, limit: {limit}")
    tasks = ScheduledTaskService.get_tasks(db, skip=skip, limit=limit)
    
    # 添加运行状态
    for task in tasks:
        task._running = scheduler.is_task_running(task.id)
    
    logger.info(f"获取到 {len(tasks)} 个周期任务")
    return tasks


@router.get("/session/{session_id}", response_model=List[ScheduledTaskResponse])
def get_tasks_by_session(session_id: str, db: Session = Depends(get_db)):
    """根据会话 ID 获取周期任务"""
    logger.info(f"根据会话 ID 获取周期任务：{session_id}")
    tasks = ScheduledTaskService.get_tasks_by_session(db, session_id=session_id)
    
    # 添加运行状态
    for task in tasks:
        task._running = scheduler.is_task_running(task.id)
    
    logger.info(f"获取到 {len(tasks)} 个周期任务")
    return tasks


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """根据 ID 获取周期任务"""
    logger.info(f"根据 ID 获取周期任务：{task_id}")
    task = ScheduledTaskService.get_task_by_id(db, task_id=task_id)
    if task is None:
        logger.warning(f"周期任务未找到：{task_id}")
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    
    task._running = scheduler.is_task_running(task.id)
    logger.info(f"获取周期任务成功：{task_id}")
    return task


@router.post("", response_model=ScheduledTaskResponse)
def create_task(task: ScheduledTaskCreate, db: Session = Depends(get_db)):
    """创建周期任务"""
    logger.info(f"创建周期任务请求：{task.model_dump()}")
    created_task = ScheduledTaskService.create_task(db=db, task=task)
    logger.info(f"周期任务创建成功：{created_task.id}")
    return created_task


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
def update_task(task_id: int, task: ScheduledTaskUpdate, db: Session = Depends(get_db)):
    """更新周期任务"""
    logger.info(f"更新周期任务请求：task_id={task_id}, data={task.model_dump(exclude_unset=True)}")
    db_task = ScheduledTaskService.update_task(db=db, task_id=task_id, task_update=task)
    if db_task is None:
        logger.warning(f"周期任务未找到：{task_id}")
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    logger.info(f"周期任务更新成功：{task_id}")
    return db_task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除周期任务"""
    logger.info(f"删除周期任务：{task_id}")
    
    # 如果任务在运行，先停止
    if scheduler.is_task_running(task_id):
        import asyncio
        asyncio.create_task(scheduler.stop_task(task_id))
    
    success = ScheduledTaskService.delete_task(db=db, task_id=task_id)
    if not success:
        logger.warning(f"周期任务未找到：{task_id}")
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    logger.info(f"周期任务删除成功：{task_id}")
    return {"message": "Scheduled task deleted successfully"}


@router.post("/{task_id}/start")
def start_task(task_id: int, db: Session = Depends(get_db)):
    """启动周期任务"""
    logger.info(f"启动周期任务：{task_id}")
    
    task = ScheduledTaskService.get_task_by_id(db, task_id=task_id)
    if task is None:
        logger.warning(f"周期任务未找到：{task_id}")
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    
    if not task.enabled:
        raise HTTPException(status_code=400, detail="任务未启用，请先启用任务")
    
    # 启动任务
    import asyncio
    asyncio.create_task(
        scheduler.start_task(task_id, task.session_id, task.interval, task.message)
    )
    
    # 更新数据库状态
    ScheduledTaskService.start_task(db, task_id=task_id)
    
    logger.info(f"周期任务已启动：{task_id}")
    return {"message": "Task started successfully", "task_id": task_id}


@router.post("/{task_id}/stop")
def stop_task(task_id: int, db: Session = Depends(get_db)):
    """停止周期任务"""
    logger.info(f"停止周期任务：{task_id}")
    
    task = ScheduledTaskService.get_task_by_id(db, task_id=task_id)
    if task is None:
        logger.warning(f"周期任务未找到：{task_id}")
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    
    # 停止任务
    import asyncio
    asyncio.create_task(scheduler.stop_task(task_id))
    
    # 更新数据库状态
    ScheduledTaskService.stop_task(db, task_id=task_id)
    
    logger.info(f"周期任务已停止：{task_id}")
    return {"message": "Task stopped successfully", "task_id": task_id}
