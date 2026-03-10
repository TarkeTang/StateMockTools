from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db, SessionLocal
from schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionMessageCreate,
    SessionMessageResponse, SessionWithMessages, SessionConnectResponse
)
from services.session.session_service import SessionService
from services.session.session_connection_manager import connection_manager
from config.logging import logger
import json
import asyncio

router = APIRouter(
    prefix="/api/sessions",
    tags=["session"],
    responses={404: {"description": "Not found"}},
)

# WebSocket 路由不使用 prefix，单独注册
router_ws = APIRouter(tags=["session"])

# 存储活跃的 WebSocket 连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket 连接建立：{session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket 连接断开：{session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)
            logger.debug(f"发送消息到会话：{session_id}")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
        logger.debug(f"广播消息到所有连接")

manager = ConnectionManager()


@router.get("", response_model=List[SessionResponse])
def get_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取会话列表"""
    logger.info(f"获取会话列表，skip: {skip}, limit: {limit}")
    sessions = SessionService.get_sessions(db, skip=skip, limit=limit)
    logger.info(f"获取到 {len(sessions)} 个会话")
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """根据 ID 获取会话"""
    logger.info(f"根据 ID 获取会话：{session_id}")
    session = SessionService.get_session(db, session_id=session_id)
    if session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"获取会话成功：{session_id}")
    return session


@router.post("", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    """创建会话"""
    logger.info(f"创建会话请求：{session.model_dump()}")
    created_session = SessionService.create_session(db=db, session=session)
    logger.info(f"会话创建成功：{created_session.id}, 响应：{created_session.model_dump()}")
    return created_session


@router.put("/{session_id}", response_model=SessionResponse)
def update_session(session_id: str, session: SessionUpdate, db: Session = Depends(get_db)):
    """更新会话"""
    logger.info(f"更新会话请求：session_id={session_id}, data={session.model_dump(exclude_unset=True)}")
    db_session = SessionService.update_session(db=db, session_id=session_id, session_update=session)
    if db_session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"会话更新成功：{session_id}, 响应：{db_session.model_dump()}")
    return db_session


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    logger.info(f"删除会话：{session_id}")
    success = SessionService.delete_session(db=db, session_id=session_id)
    if not success:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"会话删除成功：{session_id}")
    return {"message": "Session deleted successfully"}


@router.post("/{session_id}/connect")
def connect_session(session_id: str, db: Session = Depends(get_db)):
    """连接会话（旧接口，保留兼容）"""
    logger.info(f"连接会话：{session_id}")
    session = SessionService.get_session(db, session_id=session_id)
    if session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # 更新会话状态为已连接
    session.status = "connected"
    db.commit()
    db.refresh(session)

    # 广播会话状态变更
    asyncio.create_task(manager.broadcast(
        json.dumps({
            "type": "session_status_change",
            "sessionId": session_id,
            "status": "connected"
        })
    ))

    logger.info(f"会话连接成功：{session_id}")
    return {"message": "Session connected successfully", "session": session}


@router.post("/{session_id}/disconnect")
def disconnect_session(session_id: str, db: Session = Depends(get_db)):
    """断开会话（旧接口，保留兼容）"""
    logger.info(f"断开会话：{session_id}")
    session = SessionService.get_session(db, session_id=session_id)
    if session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # 更新会话状态为已断开
    session.status = "disconnected"
    db.commit()
    db.refresh(session)

    # 广播会话状态变更
    asyncio.create_task(manager.broadcast(
        json.dumps({
            "type": "session_status_change",
            "sessionId": session_id,
            "status": "disconnected"
        })
    ))

    logger.info(f"会话断开成功：{session_id}")
    return {"message": "Session disconnected successfully", "session": session}


@router.get("/{session_id}/messages", response_model=List[SessionMessageResponse])
def get_session_messages(session_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取会话消息列表"""
    logger.info(f"获取会话消息列表：{session_id}, skip: {skip}, limit: {limit}")
    messages = SessionService.get_session_messages(db, session_id=session_id, skip=skip, limit=limit)
    logger.info(f"获取到 {len(messages)} 条消息")
    return messages


@router.post("/{session_id}/messages", response_model=SessionMessageResponse)
def create_session_message(session_id: str, message: SessionMessageCreate, db: Session = Depends(get_db)):
    """创建会话消息（旧接口，保留兼容）"""
    logger.info(f"创建会话消息：{session_id}")
    # 验证会话是否存在
    session = SessionService.get_session(db, session_id=session_id)
    if session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # 验证消息格式
    if not SessionService.validate_message(message.content):
        logger.warning(f"消息格式无效：{session_id}")
        raise HTTPException(status_code=400, detail="Invalid message format")

    # 创建消息
    db_message = SessionService.create_session_message(db=db, message=message)

    # 广播消息给 WebSocket 连接
    asyncio.create_task(manager.send_personal_message(
        json.dumps({
            "type": "message",
            "session_id": session_id,
            "message": db_message.content,
            "direction": db_message.direction,
            "created_at": db_message.created_at.isoformat()
        }),
        session_id
    ))

    logger.info(f"消息创建成功：{session_id}")
    return db_message


# 旧的 WebSocket 接口已废弃，请使用 /ws/session/{session_id}
# @router.websocket("/ws/{session_id}")
# async def websocket_endpoint(websocket: WebSocket, session_id: str):
#     """WebSocket 接口，用于实时会话消息（旧接口，保留兼容）"""
#     await manager.connect(websocket, session_id)
#     try:
#         while True:
#             # 接收客户端消息
#             data = await websocket.receive_text()
#
#             # 解析消息
#             try:
#                 message_data = json.loads(data)
#                 # 处理消息
#                 logger.info(f"收到来自会话 {session_id} 的消息")
#
#                 # 广播消息给所有客户端
#                 await manager.send_personal_message(json.dumps({
#                     "type": "message",
#                     "session_id": session_id,
#                     "message": message_data["content"],
#                     "direction": "sent",
#                     "created_at": message_data.get("created_at", "")
#                 }), session_id)
#             except json.JSONDecodeError:
#                 logger.warning(f"无效的消息格式：{session_id}")
#                 await websocket.send_text(json.dumps({"type": "error", "content": "无效的消息格式"}))
#     except WebSocketDisconnect:
#         manager.disconnect(session_id)
#         # 广播客户端断开连接的消息
#         await manager.broadcast(json.dumps({
#             "type": "system",
#             "content": f"会话 {session_id} 已断开连接"
#         }))
#         logger.info(f"WebSocket 连接断开：{session_id}")


# ==================== 新增实时会话连接接口 ====================

@router.post("/{session_id}/establish-connection", response_model=SessionConnectResponse)
async def establish_connection(session_id: str, force: bool = True, db: Session = Depends(get_db)):
    """
    建立会话连接 - 连接设备并建立实时通信

    Args:
        session_id: 会话 ID
        force: 是否强制重新连接（默认 True，总是尝试新连接）
    """
    logger.info(f"====== 建立会话连接请求：{session_id}, force={force} ======")

    try:
        # 获取会话配置
        logger.info(f"正在获取会话配置：{session_id}")
        session_config = SessionService.get_session_config(db, session_id)

        if not session_config:
            logger.error(f"会话未找到：{session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"获取会话配置成功：IP={session_config.get('ip')}, Port={session_config.get('port')}")

        # 建立设备连接（会自动清理旧连接）
        logger.info(f"开始建立设备连接：{session_id} -> {session_config.get('ip')}:{session_config.get('port')}")
        success = await connection_manager.establish_device_connection(session_id, session_config)

        if success:
            # 更新数据库状态
            SessionService.update_session_status(db, session_id, "connected")
            logger.info(f"会话连接建立成功：{session_id}")
            
            # 启动关联的周期任务
            try:
                from services.scheduled_task.scheduled_task_service import ScheduledTaskService
                from services.scheduled_task.scheduled_task_scheduler import scheduler
                
                tasks = ScheduledTaskService.get_tasks_by_session(db, session_id)
                for task in tasks:
                    if task.enabled and task.running:
                        logger.info(f"启动关联的周期任务：{task.id}")
                        import asyncio
                        asyncio.create_task(
                            scheduler.start_task(task.id, task.session_id, task.interval, task.message)
                        )
            except Exception as e:
                logger.warning(f"启动周期任务失败：{str(e)}")
            
            return SessionConnectResponse(
                success=True,
                session_id=session_id,
                status="connected",
                message=f"成功连接到 {session_config['ip']}:{session_config['port']}"
            )
        else:
            # 更新数据库状态
            SessionService.update_session_status(db, session_id, "error")
            logger.error(f"会话连接建立失败：{session_id}")
            raise HTTPException(status_code=500, detail="Failed to establish connection")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"建立会话连接异常：{session_id}, 错误：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/{session_id}/close-connection")
async def close_connection(session_id: str, db: Session = Depends(get_db)):
    """关闭会话连接"""
    logger.info(f"关闭会话连接请求：{session_id}")

    # 验证会话是否存在
    session = SessionService.get_session(db, session_id=session_id)
    if session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # 停止关联的周期任务
    try:
        from services.scheduled_task.scheduled_task_scheduler import scheduler
        await scheduler.stop_session_tasks(session_id)
        logger.info(f"已停止会话 {session_id} 的所有周期任务")
    except Exception as e:
        logger.warning(f"停止周期任务失败：{str(e)}")

    # 关闭设备连接
    await connection_manager.close_device_connection(session_id)

    # 更新数据库状态
    SessionService.update_session_status(db, session_id, "disconnected")

    logger.info(f"会话连接关闭：{session_id}")
    return {"message": "Connection closed successfully", "session_id": session_id}


@router.post("/{session_id}/send-message")
async def send_message(session_id: str, content: str, db: Session = Depends(get_db)):
    """发送消息到设备（支持参数替换）"""
    logger.info(f"发送消息请求：{session_id}, 内容：{content}")

    # 验证会话是否存在
    session = SessionService.get_session(db, session_id=session_id)
    if session is None:
        logger.warning(f"会话未找到：{session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # 检查是否已连接
    if not connection_manager.is_connected(session_id):
        logger.warning(f"会话未连接：{session_id}")
        raise HTTPException(status_code=400, detail="Session not connected")

    # 参数替换
    original_content = content
    try:
        from services.parameter.parameter_service import ParameterService
        content = ParameterService.replace_parameters_with_db(content, db)
        if original_content != content:
            logger.info(f"参数替换：{original_content} -> {content}")
    except Exception as e:
        logger.warning(f"参数替换失败：{str(e)}")

    # 发送消息
    success = await connection_manager.send_message_to_device(session_id, content)

    if success:
        # 保存消息到数据库（保存原始内容）
        SessionService.save_session_message(db, session_id, original_content, "sent")
        return {"message": "Message sent successfully", "session_id": session_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


@router_ws.websocket("/ws/session/{session_id}")
async def session_websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 接口，用于实时推送会话状态和消息到前端"""
    # 在 accept 之前记录日志，帮助调试
    print(f"[WebSocket Debug] 路由被调用：/ws/session/{session_id}")
    print(f"[WebSocket Debug] WebSocket 对象：{websocket}")
    print(f"[WebSocket Debug] session_id: {session_id}")
    
    try:
        # 先接受 WebSocket 连接 - 这必须在任何异常之前调用
        print(f"[WebSocket Debug] 准备 accept...")
        await websocket.accept()
        print(f"[WebSocket Debug] accept 成功")
        logger.info(f"WebSocket 已接受：{session_id}")
        
        # 建立前端连接（最简单操作，不应该失败）
        try:
            await connection_manager.connect_frontend(websocket, session_id)
            logger.info(f"前端连接已建立：{session_id}")
        except Exception as e:
            logger.error(f"建立前端连接失败：{session_id}, 错误：{str(e)}")
            # 继续，不影响连接
        
        # 发送当前连接状态
        try:
            current_status = connection_manager.get_connection_status(session_id)
            await websocket.send_json({
                "type": "status",
                "session_id": session_id,
                "status": current_status,
                "message": f"当前连接状态：{current_status}"
            })
            logger.info(f"已发送初始状态到前端：{session_id}, status={current_status}")
        except Exception as e:
            logger.error(f"发送初始状态失败：{session_id}, 错误：{str(e)}")
        
        # 保持连接，等待前端断开
        while True:
            try:
                # 接收前端消息（可选，用于心跳等）
                data = await websocket.receive_text()
                logger.debug(f"收到前端消息：{session_id}, {data}")
            except WebSocketDisconnect:
                logger.info(f"前端 WebSocket 断开：{session_id}")
                break
            except Exception as e:
                logger.warning(f"接收前端消息异常：{session_id}, {str(e)}")
                break
                
    except Exception as e:
        print(f"[WebSocket Debug] 异常：{type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"WebSocket 连接异常：{session_id}, 错误：{str(e)}", exc_info=True)
        # 尝试关闭连接（可能已经关闭）
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass
    finally:
        # 清理前端连接
        try:
            connection_manager.disconnect_frontend(websocket, session_id)
            logger.info(f"前端连接已清理：{session_id}")
        except:
            pass
