from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from services.device.device_service import DeviceService
from config.logging import logger

router = APIRouter(
    prefix="/api/devices",
    tags=["device"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[DeviceResponse])
def get_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取设备列表"""
    logger.info(f"获取设备列表，skip: {skip}, limit: {limit}")
    devices = DeviceService.get_devices(db, skip=skip, limit=limit)
    logger.info(f"获取到 {len(devices)} 个设备")
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    """根据ID获取设备"""
    logger.info(f"根据ID获取设备: {device_id}")
    device = DeviceService.get_device(db, device_id=device_id)
    if device is None:
        logger.warning(f"设备未找到: {device_id}")
        raise HTTPException(status_code=404, detail="Device not found")
    logger.info(f"获取设备成功: {device_id}")
    return device


@router.post("", response_model=DeviceResponse)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """创建设备"""
    logger.info(f"创建设备请求: {device.model_dump()}")
    created_device = DeviceService.create_device(db=db, device=device)
    logger.info(f"设备创建成功: {created_device.id}, 响应: {created_device.model_dump()}")
    return created_device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: str, device: DeviceUpdate, db: Session = Depends(get_db)):
    """更新设备"""
    logger.info(f"更新设备请求: device_id={device_id}, data={device.model_dump(exclude_unset=True)}")
    db_device = DeviceService.update_device(db=db, device_id=device_id, device_update=device)
    if db_device is None:
        logger.warning(f"设备未找到: {device_id}")
        raise HTTPException(status_code=404, detail="Device not found")
    logger.info(f"设备更新成功: {device_id}, 响应: 设备ID={db_device.id}, 名称={db_device.name}, 类型={db_device.type}")
    return db_device


@router.delete("/{device_id}")
def delete_device(device_id: str, db: Session = Depends(get_db)):
    """删除设备"""
    logger.info(f"删除设备: {device_id}")
    success = DeviceService.delete_device(db=db, device_id=device_id)
    if not success:
        logger.warning(f"设备未找到: {device_id}")
        raise HTTPException(status_code=404, detail="Device not found")
    logger.info(f"设备删除成功: {device_id}")
    return {"message": "Device deleted successfully"}


@router.get("/type/{device_type}", response_model=List[DeviceResponse])
def get_devices_by_type(device_type: str, db: Session = Depends(get_db)):
    """根据设备类型获取设备列表"""
    logger.info(f"根据设备类型获取设备列表: {device_type}")
    devices = DeviceService.get_devices_by_type(db, device_type=device_type)
    logger.info(f"获取到 {len(devices)} 个设备")
    return devices