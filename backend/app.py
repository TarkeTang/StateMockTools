from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from config.logging import logger
from database import engine, Base
from services.device.device_router import router as device_router
from services.session.session_router import router as session_router, router_ws as session_router_ws
from services.protocol.protocol_router import router as protocol_router
from services.automation.automation_router import router as automation_router
from services.dictionary.dictionary_router import router as dictionary_router
from services.parameter.parameter_router import router as parameter_router
from services.scheduled_task.scheduled_task_router import router as scheduled_task_router
import json
import asyncio

# 创建数据库表
Base.metadata.create_all(bind=engine)

logger.info("正在启动 StateMockTools 后端服务...")

app = FastAPI(
    title=settings.APP_NAME,
    description="StateMockTools 后端服务",
    version=settings.APP_VERSION
)

logger.info(f"StateMockTools 后端服务启动成功，版本: {settings.APP_VERSION}")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(device_router)
app.include_router(session_router)
app.include_router(session_router_ws)  # WebSocket 路由
app.include_router(protocol_router)
app.include_router(automation_router)
app.include_router(dictionary_router)
app.include_router(parameter_router)  # 参数设置路由
app.include_router(scheduled_task_router)  # 周期任务路由


@app.get("/")
def read_root():
    """根路径"""
    logger.info("访问根路径")
    return {
        "message": "StateMockTools 后端服务",
        "version": settings.APP_VERSION,
        "services": [
            {"name": "设备管理", "path": "/api/devices"},
            {"name": "会话管理", "path": "/api/sessions"},
            {"name": "协议管理", "path": "/api/protocols"},
            {"name": "自动化测试", "path": "/api/automation"}
        ]
    }


@app.get("/health")
def health_check():
    """健康检查"""
    logger.info("健康检查请求")
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )