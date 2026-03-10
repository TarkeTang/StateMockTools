from typing import List, Optional
from sqlalchemy.orm import Session
from models.protocol import Protocol
from schemas.protocol import ProtocolCreate, ProtocolUpdate
from config.logging import logger
import json


class ProtocolService:
    """协议服务类"""

    @staticmethod
    def get_protocols(db: Session, skip: int = 0, limit: int = 100) -> List[Protocol]:
        """获取协议列表"""
        logger.debug(f"获取协议列表，skip: {skip}, limit: {limit}")
        protocols = db.query(Protocol).offset(skip).limit(limit).all()

        # 转换 fields 字段回列表格式以便返回
        for protocol in protocols:
            if protocol.fields:
                try:
                    protocol.fields = json.loads(protocol.fields)
                except json.JSONDecodeError:
                    protocol.fields = []

        logger.debug(f"获取到 {len(protocols)} 个协议")
        return protocols

    @staticmethod
    def get_protocol(db: Session, protocol_id: str) -> Optional[Protocol]:
        """根据 ID 获取协议"""
        logger.debug(f"根据 ID 获取协议：{protocol_id}")
        protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()

        # 转换 fields 字段回列表格式以便返回
        if protocol and protocol.fields:
            try:
                protocol.fields = json.loads(protocol.fields)
            except json.JSONDecodeError:
                protocol.fields = []

        logger.debug(f"获取协议结果：{'成功' if protocol else '失败'}")
        return protocol

    @staticmethod
    def create_protocol(db: Session, protocol: ProtocolCreate) -> Protocol:
        """创建协议"""
        logger.debug(f"创建协议：{protocol.name}")

        # 处理字段数据，转换为 JSON 字符串
        protocol_data = protocol.model_dump()
        if 'fields' in protocol_data:
            protocol_data['fields'] = json.dumps(protocol_data['fields'])

        db_protocol = Protocol(**protocol_data)
        db.add(db_protocol)
        db.commit()
        db.refresh(db_protocol)

        # 转换 fields 字段回列表格式以便返回
        if db_protocol.fields:
            db_protocol.fields = json.loads(db_protocol.fields)

        logger.debug(f"协议创建成功：{db_protocol.id}")
        return db_protocol

    @staticmethod
    def update_protocol(db: Session, protocol_id: str, protocol_update: ProtocolUpdate) -> Optional[Protocol]:
        """更新协议"""
        logger.debug(f"更新协议：{protocol_id}")
        db_protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
        if db_protocol:
            update_data = protocol_update.model_dump(exclude_unset=True)

            # 处理 fields 字段，转换为 JSON 字符串
            if 'fields' in update_data:
                update_data['fields'] = json.dumps(update_data['fields'])

            for field, value in update_data.items():
                setattr(db_protocol, field, value)
            db.commit()
            db.refresh(db_protocol)

            # 转换 fields 字段回列表格式以便返回
            if db_protocol.fields:
                db_protocol.fields = json.loads(db_protocol.fields)

            logger.debug(f"协议更新成功：{protocol_id}")
        else:
            logger.debug(f"协议未找到：{protocol_id}")
        return db_protocol

    @staticmethod
    def delete_protocol(db: Session, protocol_id: str) -> bool:
        """删除协议"""
        logger.debug(f"删除协议：{protocol_id}")
        db_protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
        if db_protocol:
            db.delete(db_protocol)
            db.commit()
            logger.debug(f"协议删除成功：{protocol_id}")
            return True
        logger.debug(f"协议未找到：{protocol_id}")
        return False

    @staticmethod
    def get_protocols_by_device_type(db: Session, device_type: str) -> List[Protocol]:
        """根据设备类型获取协议列表"""
        logger.debug(f"根据设备类型获取协议列表：{device_type}")
        protocols = db.query(Protocol).filter(Protocol.device_type == device_type).all()

        # 转换 fields 字段回列表格式以便返回
        for protocol in protocols:
            if protocol.fields:
                try:
                    protocol.fields = json.loads(protocol.fields)
                except json.JSONDecodeError:
                    protocol.fields = []

        logger.debug(f"获取到 {len(protocols)} 个协议")
        return protocols

    @staticmethod
    def get_protocols_by_type(db: Session, protocol_type: str) -> List[Protocol]:
        """根据协议类型获取协议列表"""
        logger.debug(f"根据协议类型获取协议列表：{protocol_type}")
        protocols = db.query(Protocol).filter(Protocol.type == protocol_type).all()

        # 转换 fields 字段回列表格式以便返回
        for protocol in protocols:
            if protocol.fields:
                try:
                    protocol.fields = json.loads(protocol.fields)
                except json.JSONDecodeError:
                    protocol.fields = []

        logger.debug(f"获取到 {len(protocols)} 个协议")
        return protocols

    @staticmethod
    def get_protocols_grouped(db: Session) -> dict:
        """
        获取按设备类型和消息类型分组的协议列表
        返回结构：
        {
            "device_type_code": {
                "device_type_name": "中文设备类型",
                "protocol_types": {
                    "type_code": {
                        "type_name": "中文类型",
                        "protocols": [...]
                    }
                }
            }
        }
        """
        logger.info("获取分组协议列表")
        protocols = db.query(Protocol).all()
        
        # 转换 fields 字段回列表格式
        for protocol in protocols:
            if protocol.fields:
                try:
                    protocol.fields = json.loads(protocol.fields)
                except json.JSONDecodeError:
                    protocol.fields = []
        
        # 分组
        grouped = {}
        for protocol in protocols:
            device_type = protocol.device_type
            protocol_type = protocol.type
            
            if device_type not in grouped:
                grouped[device_type] = {
                    "device_type_code": device_type,
                    "device_type_name": device_type,  # 后续通过字典映射
                    "protocol_types": {}
                }
            
            if protocol_type not in grouped[device_type]["protocol_types"]:
                grouped[device_type]["protocol_types"][protocol_type] = {
                    "type_code": protocol_type,
                    "type_name": protocol_type,  # 后续通过字典映射
                    "protocols": []
                }
            
            grouped[device_type]["protocol_types"][protocol_type]["protocols"].append(protocol)
        
        logger.info(f"分组完成，共 {len(grouped)} 个设备类型")
        return grouped
