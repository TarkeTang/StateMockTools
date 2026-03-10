from typing import List, Optional
from sqlalchemy.orm import Session
from models.device import Device
from models.session import Session
from schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from schemas.session import SessionCreate
from config.logging import logger


class DeviceService:
    """设备服务类"""
    
    @staticmethod
    def get_devices(db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
        """获取设备列表"""
        logger.debug(f"获取设备列表，skip: {skip}, limit: {limit}")
        devices = db.query(Device).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(devices)} 个设备")
        return devices
    
    @staticmethod
    def get_device(db: Session, device_id: str) -> Optional[Device]:
        """根据ID获取设备"""
        logger.debug(f"根据ID获取设备: {device_id}")
        device = db.query(Device).filter(Device.id == device_id).first()
        logger.debug(f"获取设备结果: {'成功' if device else '失败'}")
        return device
    
    @staticmethod
    def create_device(db: Session, device: DeviceCreate) -> Device:
        """创建设备"""
        logger.debug(f"创建设备: {device.name}")
        db_device = Device(**device.model_dump())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        logger.debug(f"设备创建成功: {db_device.id}")
        
        # 默认添加一条会话信息
        import uuid
        session_id = f"SESSION-{uuid.uuid4()}"
        session_data = {
            "id": session_id,
            "name": f"会话-{db_device.name}",
            "device_id": db_device.id,
            "device_type": db_device.type,
            "ip": db_device.ip,
            "port": db_device.port,
            "protocol_type": "",
            "send_code": "",
            "receive_code": "",
            "status": "disconnected"
        }
        db_session = Session(**session_data)
        db.add(db_session)
        db.commit()
        logger.debug(f"默认会话创建成功: {session_id}")
        
        return db_device
    
    @staticmethod
    def update_device(db: Session, device_id: str, device_update: DeviceUpdate) -> Optional[Device]:
        """更新设备"""
        logger.debug(f"更新设备: {device_id}")
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if db_device:
            update_data = device_update.model_dump(exclude_unset=True)
            
            # 检查是否更新了设备ID
            new_device_id = update_data.get('id')
            if new_device_id and new_device_id != device_id:
                # 更新相关的会话信息
                sessions = db.query(Session).filter(Session.device_id == device_id).all()
                for session in sessions:
                    session.device_id = new_device_id
                logger.debug(f"更新了 {len(sessions)} 个会话的设备ID")
            
            # 更新设备属性
            for field, value in update_data.items():
                setattr(db_device, field, value)
            
            db.commit()
            db.refresh(db_device)
            logger.debug(f"设备更新成功: {device_id}")
        else:
            logger.debug(f"设备未找到: {device_id}")
        return db_device
    
    @staticmethod
    def delete_device(db: Session, device_id: str) -> bool:
        """删除设备"""
        logger.debug(f"删除设备: {device_id}")
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if db_device:
            # 先删除与该设备相关的所有会话
            db.query(Session).filter(Session.device_id == device_id).delete()
            # 再删除设备
            db.delete(db_device)
            db.commit()
            logger.debug(f"设备删除成功: {device_id}")
            return True
        logger.debug(f"设备未找到: {device_id}")
        return False
    
    @staticmethod
    def get_devices_by_type(db: Session, device_type: str) -> List[Device]:
        """根据设备类型获取设备列表"""
        logger.debug(f"根据设备类型获取设备列表: {device_type}")
        devices = db.query(Device).filter(Device.type == device_type).all()
        logger.debug(f"获取到 {len(devices)} 个设备")
        return devices