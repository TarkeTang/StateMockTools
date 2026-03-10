from typing import List, Optional
from sqlalchemy.orm import Session
from models.session import Session, SessionMessage
from schemas.session import SessionCreate, SessionUpdate, SessionMessageCreate
from config.logging import logger
import json
import time
import struct
import binascii


class SessionService:
    """会话服务类"""
    
    @staticmethod
    def get_sessions(db: Session, skip: int = 0, limit: int = 100) -> List[Session]:
        """获取会话列表"""
        logger.debug(f"获取会话列表，skip: {skip}, limit: {limit}")
        sessions = db.query(Session).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(sessions)} 个会话")
        return sessions
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[Session]:
        """根据ID获取会话"""
        logger.debug(f"根据ID获取会话: {session_id}")
        session = db.query(Session).filter(Session.id == session_id).first()
        logger.debug(f"获取会话结果: {'成功' if session else '失败'}")
        return session
    
    @staticmethod
    def create_session(db: Session, session: SessionCreate) -> Session:
        """创建会话"""
        logger.debug(f"创建会话: {session.name}")
        db_session = Session(**session.model_dump())
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        logger.debug(f"会话创建成功: {db_session.id}")
        return db_session
    
    @staticmethod
    def update_session(db: Session, session_id: str, session_update: SessionUpdate) -> Optional[Session]:
        """更新会话"""
        logger.debug(f"更新会话: {session_id}")
        db_session = db.query(Session).filter(Session.id == session_id).first()
        if db_session:
            update_data = session_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_session, field, value)
            db.commit()
            db.refresh(db_session)
            logger.debug(f"会话更新成功: {session_id}")
        else:
            logger.debug(f"会话未找到: {session_id}")
        return db_session
    
    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        """删除会话"""
        logger.debug(f"删除会话: {session_id}")
        db_session = db.query(Session).filter(Session.id == session_id).first()
        if db_session:
            # 先删除相关的消息
            db.query(SessionMessage).filter(SessionMessage.session_id == session_id).delete()
            db.delete(db_session)
            db.commit()
            logger.debug(f"会话删除成功: {session_id}")
            return True
        logger.debug(f"会话未找到: {session_id}")
        return False
    
    @staticmethod
    def get_session_messages(db: Session, session_id: str, skip: int = 0, limit: int = 100) -> List[SessionMessage]:
        """获取会话消息列表"""
        logger.debug(f"获取会话消息列表: {session_id}, skip: {skip}, limit: {limit}")
        messages = db.query(SessionMessage).filter(SessionMessage.session_id == session_id).offset(skip).limit(limit).all()
        logger.debug(f"获取到 {len(messages)} 条消息")
        return messages
    
    @staticmethod
    def create_session_message(db: Session, message: SessionMessageCreate) -> SessionMessage:
        """创建会话消息"""
        logger.debug(f"创建会话消息: {message.session_id}")
        db_message = SessionMessage(**message.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        logger.debug(f"消息创建成功: {db_message.id}")
        return db_message
    
    @staticmethod
    def validate_message(content: str) -> bool:
        """校验消息格式"""
        logger.debug("校验消息格式")
        try:
            # 这里可以添加具体的消息校验逻辑
            # 例如校验XML格式、消息长度等
            logger.debug("消息格式校验成功")
            return True
        except Exception as e:
            logger.warning(f"消息格式校验失败: {str(e)}")
            return False
    
    @staticmethod
    def packetize_message(session_source: str, session_num: str, xml_content: str) -> bytes:
        """打包消息"""
        logger.debug(f"打包消息: {session_source}, {session_num}")
        # sessionSourceId：会话标识--------------请求 00，接收响应 01
        if session_source == "请求":
            session_source_id = '00'
            send_session_num = session_num
            receive_session_num = '0'
        elif session_source == "响应":
            session_source_id = '01'
            send_session_num = '0'
            receive_session_num = session_num
        else:
            send_session_num = '66666'
            receive_session_num = '66666'
            session_source_id = '02'
        # 发送会话序列号
        send_session_num = struct.pack('q', int(send_session_num)).hex()
        # 接收会话序列号
        receive_session_num = struct.pack('q', int(receive_session_num)).hex()
        # xml长度
        xml_len = struct.pack('i', len(xml_content.encode())).hex()
        # xml内容
        xml_content = binascii.hexlify(xml_content.encode()).decode('utf8', 'ignore')
        # 拼接报文
        message = 'EB90' + send_session_num + receive_session_num + session_source_id + xml_len + xml_content + 'EB90'
        message = binascii.unhexlify(message)
        logger.debug("消息打包成功")
        return message
    
    @staticmethod
    def depacketize_message(message: bytes) -> dict:
        """解包消息"""
        logger.debug("解包消息")
        receive_pack = message.hex()
        receive_pack = receive_pack.upper()
        # 发送会话号
        send_session_num = receive_pack[0:16]
        send_session_num = int.from_bytes(binascii.unhexlify(send_session_num), 'little')
        # 接收会话号
        receive_session_num = receive_pack[16:32]
        receive_session_num = int.from_bytes(binascii.unhexlify(receive_session_num), 'little')
        # 会话标识：00请求  01接收响应
        session_source_id = receive_pack[32:34]
        # xml长度
        xml_len = receive_pack[34:42]
        xml_len = int.from_bytes(binascii.unhexlify(xml_len), 'little')
        # xml内容
        xml_content = receive_pack[42:]
        xml_content = binascii.unhexlify(xml_content).decode()
        result = {
            'sendSessionNum': send_session_num,
            'receiveSessionNum': receive_session_num,
            'sessionSourceId': session_source_id,
            'receiveXmlContent': xml_content
        }
        logger.debug("消息解包成功")
        return result

    @staticmethod
    def get_session_config(db: Session, session_id: str) -> Optional[dict]:
        """获取会话配置信息"""
        logger.info(f"获取会话配置：{session_id}")
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                config = {
                    "id": session.id,
                    "name": session.name,
                    "ip": session.ip,
                    "port": session.port,
                    "protocol_type": session.protocol_type,
                    "send_code": session.send_code,
                    "receive_code": session.receive_code,
                    "timeout": session.timeout,
                    "status": session.status
                }
                logger.info(f"获取会话配置成功：{config}")
                return config
            else:
                logger.warning(f"会话未找到：{session_id}, 数据库中无此记录")
                return None
        except Exception as e:
            logger.error(f"获取会话配置异常：{session_id}, 错误：{str(e)}")
            return None

    @staticmethod
    def update_session_status(db: Session, session_id: str, status: str) -> bool:
        """更新会话状态"""
        logger.debug(f"更新会话状态：{session_id} -> {status}")
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.status = status
            db.commit()
            logger.debug(f"会话状态更新成功：{session_id}")
            return True
        logger.warning(f"会话未找到：{session_id}")
        return False

    @staticmethod
    def save_session_message(db: Session, session_id: str, content: str, direction: str, message_type: str = "message") -> Optional[SessionMessage]:
        """保存会话消息"""
        logger.debug(f"保存会话消息：{session_id}, 方向：{direction}")
        try:
            message = SessionMessageCreate(
                session_id=session_id,
                message_type=message_type,
                content=content,
                direction=direction
            )
            db_message = SessionService.create_session_message(db=db, message=message)
            logger.debug(f"会话消息保存成功：{session_id}")
            return db_message
        except Exception as e:
            logger.error(f"保存会话消息失败：{str(e)}")
            return None