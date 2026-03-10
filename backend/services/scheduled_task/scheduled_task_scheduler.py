"""
周期任务调度管理器
负责管理所有运行中的周期任务
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
from config.logging import logger
from services.session.session_connection_manager import connection_manager
from services.scheduled_task.scheduled_task_service import ScheduledTaskService
from database import get_db


class TaskScheduler:
    """任务调度器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            # 运行中的任务 {task_id: asyncio.Task}
            self.running_tasks: Dict[int, asyncio.Task] = {}
            # 任务会话映射 {session_id: [task_id, ...]}
            self.session_tasks: Dict[str, list] = {}
            self._initialized = True
            logger.info("TaskScheduler 初始化完成")
    
    async def start_task(self, task_id: int, session_id: str, interval: int, message: str):
        """启动单个任务"""
        if task_id in self.running_tasks:
            logger.warning(f"任务已在运行：{task_id}")
            return
        
        logger.info(f"启动周期任务：{task_id}, 会话：{session_id}, 周期：{interval}秒")
        
        # 创建异步任务
        task = asyncio.create_task(
            self._run_periodic_task(task_id, session_id, interval, message)
        )
        self.running_tasks[task_id] = task
        
        # 添加到会话映射
        if session_id not in self.session_tasks:
            self.session_tasks[session_id] = []
        if task_id not in self.session_tasks[session_id]:
            self.session_tasks[session_id].append(task_id)
        
        logger.info(f"周期任务已启动：{task_id}")
    
    async def stop_task(self, task_id: int):
        """停止单个任务"""
        if task_id not in self.running_tasks:
            logger.warning(f"任务未运行：{task_id}")
            return
        
        logger.info(f"停止周期任务：{task_id}")
        
        # 取消任务
        task = self.running_tasks[task_id]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.running_tasks[task_id]
        logger.info(f"周期任务已停止：{task_id}")
    
    async def stop_session_tasks(self, session_id: str):
        """停止会话的所有任务"""
        if session_id in self.session_tasks:
            task_ids = self.session_tasks[session_id].copy()
            for task_id in task_ids:
                await self.stop_task(task_id)
            del self.session_tasks[session_id]
            logger.info(f"会话 {session_id} 的所有周期任务已停止")
    
    async def _run_periodic_task(self, task_id: int, session_id: str, interval: int, message: str):
        """运行周期任务"""
        logger.info(f"周期任务开始运行：{task_id}, 周期：{interval}秒")
        
        try:
            while True:
                # 等待到下次执行时间
                await asyncio.sleep(interval)
                
                # 检查会话是否连接
                if not connection_manager.is_connected(session_id):
                    logger.debug(f"会话未连接，跳过执行：{task_id}, 会话：{session_id}")
                    continue
                
                # 发送消息
                try:
                    await connection_manager.send_message_to_device(session_id, message)
                    logger.debug(f"周期任务执行成功：{task_id}")
                    
                    # 记录执行
                    db_gen = get_db()
                    db = next(db_gen)
                    try:
                        ScheduledTaskService.record_execution(db, task_id)
                    finally:
                        db_gen.close()
                        
                except Exception as e:
                    logger.error(f"周期任务执行失败：{task_id}, 错误：{str(e)}")
                    
        except asyncio.CancelledError:
            logger.info(f"周期任务被取消：{task_id}")
        except Exception as e:
            logger.error(f"周期任务异常：{task_id}, 错误：{str(e)}")
    
    def get_running_count(self) -> int:
        """获取运行中的任务数量"""
        return len(self.running_tasks)
    
    def is_task_running(self, task_id: int) -> bool:
        """检查任务是否运行中"""
        return task_id in self.running_tasks


# 全局单例
scheduler = TaskScheduler()
