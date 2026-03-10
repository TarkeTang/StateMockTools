"""
会话连接管理器
负责管理设备真实连接（TCP/UDP）和 WebSocket 消息推送
参考 interface_client.py 中的 recv_msg、depacketize、send_msg、packetize 实现
"""
import asyncio
import socket
import json
import struct
import binascii
from typing import Dict, Optional, Set, List
from fastapi import WebSocket
from config.logging import logger
from services.session.session_service import SessionService
from database import get_db


class SessionConnectionManager:
    """会话连接管理器 - 单例模式"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            # 前端 WebSocket 连接管理 {session_id: Set[WebSocket]}
            self.frontend_connections: Dict[str, Set[WebSocket]] = {}
            # 设备连接管理 {session_id: socket_info}
            self.device_connections: Dict[str, dict] = {}
            # 连接任务管理 {session_id: asyncio.Task}
            self.connection_tasks: Dict[str, asyncio.Task] = {}
            # 连接状态 {session_id: str}
            self.connection_status: Dict[str, str] = {}
            # 消息缓冲 {session_id: bytes} - 用于处理粘包
            self.message_buffers: Dict[str, bytes] = {}
            self._initialized = True
            logger.info("SessionConnectionManager 初始化完成")
    
    async def connect_frontend(self, websocket: WebSocket, session_id: str):
        """前端 WebSocket 连接"""
        if session_id not in self.frontend_connections:
            self.frontend_connections[session_id] = set()
        self.frontend_connections[session_id].add(websocket)
        logger.info(f"前端 WebSocket 连接：{session_id}")
    
    def disconnect_frontend(self, websocket: WebSocket, session_id: str):
        """前端 WebSocket 断开连接"""
        if session_id in self.frontend_connections:
            self.frontend_connections[session_id].discard(websocket)
            if not self.frontend_connections[session_id]:
                del self.frontend_connections[session_id]
        logger.info(f"前端 WebSocket 断开连接：{session_id}")
    
    async def send_to_frontend(self, session_id: str, message: dict):
        """发送消息到前端"""
        if session_id in self.frontend_connections and self.frontend_connections[session_id]:
            disconnected = set()
            for websocket in self.frontend_connections[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"发送消息到前端失败：{session_id}, 错误：{str(e)}")
                    disconnected.add(websocket)
            # 清理断开的连接
            for ws in disconnected:
                self.frontend_connections[session_id].discard(ws)
    
    async def broadcast_session_status(self, session_id: str, status: str, message: str = ""):
        """广播会话状态变更"""
        self.connection_status[session_id] = status
        await self.send_to_frontend(session_id, {
            "type": "status",
            "session_id": session_id,
            "status": status,
            "message": message
        })
        logger.info(f"会话状态变更：{session_id} -> {status}")
    
    async def broadcast_message(self, session_id: str, content: str, direction: str, message_type: str = "message"):
        """广播消息到前端"""
        await self.send_to_frontend(session_id, {
            "type": message_type,
            "session_id": session_id,
            "content": content,
            "direction": direction
        })
        logger.debug(f"消息广播：{session_id}, 方向：{direction}")
    
    def depacketize(self, message: bytes) -> dict:
        """
        解包消息 - 参考 interface_client.py depacketize 函数
        报文格式：EB90 + 发送会话号 (8 字节 hex) + 接收会话号 (8 字节 hex) + 会话标识 (2 字节 hex) + XML 长度 (4 字节 hex) + XML 内容 + EB90
        """
        try:
            receive_pack = message.hex().upper()
            # 发送会话号 (8 字节 = 16 个 hex 字符)
            send_session_num = receive_pack[0:16]
            send_session_num = int.from_bytes(binascii.unhexlify(send_session_num), 'little')
            # 接收会话号 (8 字节 = 16 个 hex 字符)
            receive_session_num = receive_pack[16:32]
            receive_session_num = int.from_bytes(binascii.unhexlify(receive_session_num), 'little')
            # 会话标识：00 请求  01 接收响应 (2 字节 = 2 个 hex 字符)
            session_source_id = receive_pack[32:34]
            # XML 长度 (4 字节 = 8 个 hex 字符)
            xml_len = receive_pack[34:42]
            xml_len = int.from_bytes(binascii.unhexlify(xml_len), 'little')
            # XML 内容
            xml_content = receive_pack[42:]
            xml_content = binascii.unhexlify(xml_content).decode('utf-8', errors='ignore')
            
            result = {
                'sendSessionNum': send_session_num,
                'receiveSessionNum': receive_session_num,
                'sessionSourceId': session_source_id,
                'xmlLen': xml_len,
                'xmlContent': xml_content
            }
            logger.debug(f"消息解包成功：{result}")
            return result
        except Exception as e:
            logger.error(f"消息解包失败：{str(e)}")
            return {'error': str(e), 'rawHex': message.hex()}
    
    def packetize(self, session_source: str, session_num: int, xml_content: str) -> bytes:
        """
        打包消息 - 参考 interface_client.py packetize 函数
        session_source: "请求" 或 "响应"
        session_num: 会话序列号
        xml_content: XML 内容
        """
        # 会话标识：请求 00，响应 01
        if session_source == "请求":
            session_source_id = '00'
            send_session_num = session_num
            receive_session_num = 0
        elif session_source == "响应":
            session_source_id = '01'
            send_session_num = 0
            receive_session_num = session_num
        else:
            send_session_num = 66666
            receive_session_num = 66666
            session_source_id = '02'
        
        # 发送会话序列号 (8 字节，little-endian)
        send_session_num_hex = struct.pack('q', int(send_session_num)).hex()
        # 接收会话序列号 (8 字节，little-endian)
        receive_session_num_hex = struct.pack('q', int(receive_session_num)).hex()
        # XML 长度 (4 字节，little-endian)
        xml_len_hex = struct.pack('i', len(xml_content.encode('utf-8'))).hex()
        # XML 内容转 hex
        xml_content_hex = binascii.hexlify(xml_content.encode('utf-8')).decode('utf-8', 'ignore')
        
        # 拼接报文：EB90 + 发送会话号 + 接收会话号 + 会话标识 + XML 长度 + XML 内容 + EB90
        message_hex = 'EB90' + send_session_num_hex + receive_session_num_hex + session_source_id + xml_len_hex + xml_content_hex + 'EB90'
        message = binascii.unhexlify(message_hex)
        
        logger.debug(f"消息打包成功：{len(message)} 字节")
        return message
    
    async def establish_device_connection(self, session_id: str, session_data: dict):
        """建立设备连接"""
        logger.info(f"[{session_id}] 开始建立设备连接")
        try:
            ip = session_data.get("ip")
            port = session_data.get("port")
            protocol_type = session_data.get("protocol_type", "TCP")
            send_code = session_data.get("send_code", "")
            receive_code = session_data.get("receive_code", "")

            logger.info(f"[{session_id}] 连接参数：IP={ip}, Port={port}, Protocol={protocol_type}")

            if not ip or not port:
                logger.error(f"[{session_id}] 缺少 IP 或端口配置")
                raise ValueError(f"会话 {session_id} 缺少 IP 或端口配置")

            # 检查是否有旧连接，如果有则先清理
            if session_id in self.device_connections or session_id in self.connection_tasks:
                logger.info(f"[{session_id}] 检测到旧连接，正在清理...")
                await self._cleanup_connection(session_id)

            # 更新状态为连接中
            logger.info(f"[{session_id}] 正在连接 {ip}:{port}")
            await self.broadcast_session_status(session_id, "connecting", f"正在连接 {ip}:{port}")

            # 初始化消息缓冲
            self.message_buffers[session_id] = b''

            # 根据协议类型创建连接
            if protocol_type.upper() == "UDP":
                logger.info(f"[{session_id}] 创建 UDP 连接")
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(5.0)
                self.device_connections[session_id] = {
                    "socket": sock,
                    "type": "UDP",
                    "address": (ip, port),
                    "send_code": send_code,
                    "receive_code": receive_code,
                    "session_num": 0  # 会话序列号
                }
            else:  # 默认 TCP
                logger.info(f"[{session_id}] 创建 TCP 连接到 {ip}:{port}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                logger.info(f"[{session_id}] 正在执行 socket.connect...")
                sock.connect((ip, port))
                sock.setblocking(False)
                self.device_connections[session_id] = {
                    "socket": sock,
                    "type": "TCP",
                    "address": (ip, port),
                    "send_code": send_code,
                    "receive_code": receive_code,
                    "session_num": 0  # 会话序列号
                }
                logger.info(f"[{session_id}] TCP 连接建立成功")

            # 更新状态为已连接
            logger.info(f"[{session_id}] 连接成功，推送状态到前端")
            await self.broadcast_session_status(session_id, "connected", f"已成功连接到 {ip}:{port}")

            # 启动消息监听任务
            if session_id not in self.connection_tasks or self.connection_tasks[session_id].done():
                logger.info(f"[{session_id}] 启动消息监听任务")
                self.connection_tasks[session_id] = asyncio.create_task(
                    self._listen_device_messages(session_id)
                )

            logger.info(f"[{session_id}] 设备连接建立完成")
            return True

        except Exception as e:
            logger.error(f"[{session_id}] 建立设备连接失败：{str(e)}", exc_info=True)
            await self.broadcast_session_status(session_id, "error", f"连接失败：{str(e)}")
            await self.close_device_connection(session_id)
            return False
    
    async def close_device_connection(self, session_id: str):
        """关闭设备连接"""
        try:
            # 取消监听任务
            if session_id in self.connection_tasks:
                self.connection_tasks[session_id].cancel()
                del self.connection_tasks[session_id]
            
            # 关闭 socket
            if session_id in self.device_connections:
                conn_info = self.device_connections[session_id]
                try:
                    conn_info["socket"].close()
                except Exception as e:
                    logger.warning(f"关闭 socket 失败：{str(e)}")
                del self.device_connections[session_id]
            
            # 清理消息缓冲
            if session_id in self.message_buffers:
                del self.message_buffers[session_id]
            
            # 更新状态
            await self.broadcast_session_status(session_id, "disconnected", "连接已关闭")
            logger.info(f"设备连接关闭：{session_id}")
            
        except Exception as e:
            logger.error(f"关闭设备连接失败：{session_id}, 错误：{str(e)}")
    
    async def _process_complete_message(self, session_id: str, message_bytes: bytes):
        """处理完整的消息"""
        try:
            # 解包消息
            decoded = self.depacketize(message_bytes)
            
            if 'error' in decoded:
                logger.warning(f"消息解包警告：{decoded}")
                # 即使解包有问题，也尝试推送原始内容
                await self.broadcast_message(
                    session_id=session_id,
                    content=decoded.get('rawHex', message_bytes.hex()),
                    direction="received",
                    message_type="message"
                )
            else:
                # 推送 XML 内容到前端
                xml_content = decoded.get('xmlContent', '')
                await self.broadcast_message(
                    session_id=session_id,
                    content=xml_content,
                    direction="received",
                    message_type="message"
                )
                logger.info(f"收到设备消息：session_id={session_id}, sessionSourceId={decoded.get('sessionSourceId')}, xmlLen={decoded.get('xmlLen')}")
                
        except Exception as e:
            logger.error(f"处理消息失败：{session_id}, 错误：{str(e)}")
            # 推送错误信息到前端
            await self.broadcast_message(
                session_id=session_id,
                content=f"消息解析错误：{str(e)}",
                direction="received",
                message_type="error"
            )
    
    async def _listen_device_messages(self, session_id: str):
        """
        监听设备消息（后台任务）
        参考 interface_client.py recv_msg 函数处理粘包和断包
        """
        logger.info(f"开始监听设备消息：{session_id}")
        
        while session_id in self.device_connections:
            try:
                conn_info = self.device_connections.get(session_id)
                if not conn_info:
                    break
                
                sock = conn_info["socket"]
                
                try:
                    if conn_info["type"] == "TCP":
                        data = sock.recv(4096)
                    else:  # UDP
                        data, addr = sock.recvfrom(4096)
                    
                    if data:
                        logger.debug(f"收到原始数据：{len(data)} 字节")
                        
                        # 添加到缓冲区
                        self.message_buffers[session_id] += data
                        
                        # 处理缓冲区中的完整消息
                        buffer = self.message_buffers[session_id]
                        
                        # 检查是否有完整的消息（以 EB90 开头和结尾）
                        while len(buffer) >= 4:
                            # 查找消息开头 EB90
                            if buffer.startswith(b'\xeb\x90'):
                                # 查找消息结尾 EB90
                                end_pos = buffer.find(b'\xeb\x90', 2)
                                if end_pos > 2:
                                    # 提取完整消息（包含结尾的 EB90）
                                    complete_message = buffer[:end_pos + 2]
                                    logger.debug(f"检测到完整消息：{len(complete_message)} 字节")
                                    
                                    # 处理完整消息
                                    await self._process_complete_message(session_id, complete_message)
                                    
                                    # 移除已处理的消息
                                    buffer = buffer[end_pos + 2:]
                                    self.message_buffers[session_id] = buffer
                                else:
                                    # 消息不完整，等待更多数据
                                    break
                            else:
                                # 没有找到消息开头，清除缓冲（可能是脏数据）
                                logger.warning(f"缓冲区内没有找到消息开头，清除 {len(buffer)} 字节脏数据")
                                self.message_buffers[session_id] = b''
                                buffer = b''
                                break
                    else:
                        # 连接关闭
                        logger.info(f"设备连接关闭（收到空数据）：{session_id}")
                        await self.broadcast_session_status(session_id, "disconnected", "设备已断开连接")
                        # 清理连接状态
                        await self._cleanup_connection(session_id)
                        break

                except BlockingIOError:
                    # 非阻塞 socket 没有数据时抛出，等待一下
                    await asyncio.sleep(0.1)
                except socket.timeout:
                    # UDP timeout，继续监听
                    await asyncio.sleep(0.1)
                except ConnectionResetError:
                    logger.warning(f"连接被重置：{session_id}")
                    await self.broadcast_session_status(session_id, "disconnected", "连接被设备重置")
                    # 清理连接状态
                    await self._cleanup_connection(session_id)
                    break
                except Exception as e:
                    logger.warning(f"接收消息异常：{str(e)}")
                    await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                logger.info(f"监听任务被取消：{session_id}")
                break
            except Exception as e:
                logger.error(f"监听消息出错：{session_id}, 错误：{str(e)}")
                await self.broadcast_session_status(session_id, "error", f"监听错误：{str(e)}")
                await asyncio.sleep(1.0)

        logger.info(f"监听设备消息结束：{session_id}")

    async def _cleanup_connection(self, session_id: str):
        """清理连接状态（内部方法）"""
        logger.info(f"清理连接状态：{session_id}")
        
        # 取消监听任务
        if session_id in self.connection_tasks:
            try:
                self.connection_tasks[session_id].cancel()
            except:
                pass
            del self.connection_tasks[session_id]
        
        # 关闭 socket
        if session_id in self.device_connections:
            conn_info = self.device_connections[session_id]
            try:
                conn_info["socket"].close()
            except:
                pass
            del self.device_connections[session_id]
        
        # 清理消息缓冲
        if session_id in self.message_buffers:
            del self.message_buffers[session_id]
        
        logger.info(f"连接状态已清理：{session_id}")
    
    async def send_message_to_device(self, session_id: str, xml_content: str) -> bool:
        """
        发送消息到设备
        参考 interface_client.py send_msg 和 packetize 函数
        xml_content: XML 格式的消息内容
        """
        try:
            if session_id not in self.device_connections:
                logger.warning(f"会话未连接：{session_id}")
                await self.broadcast_session_status(session_id, "disconnected", "会话未连接")
                return False
            
            conn_info = self.device_connections[session_id]
            sock = conn_info["socket"]
            
            # 递增会话序列号
            conn_info["session_num"] += 1
            session_num = conn_info["session_num"]
            
            # 打包消息（使用"请求"标识）
            packed_message = self.packetize("请求", session_num, xml_content)
            
            logger.info(f"发送消息到设备：{session_id}, 序列号={session_num}, 打包后{len(packed_message)}字节")
            
            # 发送消息
            if conn_info["type"] == "TCP":
                sock.sendall(packed_message)
            else:  # UDP
                sock.sendto(packed_message, conn_info["address"])
            
            # 推送到前端（显示已发送消息）
            await self.broadcast_message(
                session_id=session_id,
                content=xml_content,
                direction="sent",
                message_type="message"
            )
            
            return True
            
        except BrokenPipeError:
            logger.error(f"管道破裂，设备可能已断开：{session_id}")
            await self.broadcast_session_status(session_id, "disconnected", "设备已断开")
            await self.close_device_connection(session_id)
            return False
        except ConnectionResetError:
            logger.error(f"连接被重置：{session_id}")
            await self.broadcast_session_status(session_id, "disconnected", "连接被设备重置")
            await self.close_device_connection(session_id)
            return False
        except Exception as e:
            logger.error(f"发送消息到设备失败：{session_id}, 错误：{str(e)}")
            await self.broadcast_session_status(session_id, "error", f"发送失败：{str(e)}")
            return False
    
    def get_connection_status(self, session_id: str) -> str:
        """获取连接状态"""
        return self.connection_status.get(session_id, "disconnected")
    
    def is_connected(self, session_id: str) -> bool:
        """检查是否已连接"""
        return session_id in self.device_connections and session_id in self.connection_tasks


# 全局单例
connection_manager = SessionConnectionManager()
