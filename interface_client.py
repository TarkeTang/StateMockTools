# _*_ coding: UTF-8 _*_																									
"""																									
@Author : TarkeTang																									
@Project : TarkeTang																									
@Date : 2024/4/20																									
"""
import connDB
import json
import random
import tkinter
from socket import *
import sys
import time
import datetime
from threading import Thread
import xml.dom.minidom as minidom
import binascii
import struct
import socket
from common.do_excel import *
from common.w_excel import *
from picSend import _FTPS, picImage
from common.loginfo import Logging
from north_validation import North_validation
from area_validation import Area_validation
from edge_validation import Edge_validation
from robot_validation import Robot_validation
from drone_validation import Drone_validation
from algo_validation import Algo_validation
from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
from tkcalendar import calendar_ as ca
from common.do_excel import DoExcel
from common.w_excel import ExcelData


class sysConfig():
    # 模拟器端口
    Port = 10011
    IP = '192.168.1.101'
    # 发送身份标识
    sendCode = 'Drone01'
    # 接受身份标识
    receiveCode = 'Edge01'
    # 用例执行文件
    run_file = './Data/2024-220kV-InterfaceList.xlsx'
    # 用例执行指定工作表
    run_sheet = 'DroneTest'
    # 用例执行结果文件
    save_file = './Data/Result.xlsx'
    # 用例结果指定工作表
    save_sheet = 'sheet1'
    # 连接对象模式：Superior、Area、Edge、Robot、Drone、Algo
    model = 'Superior'
    # 标志是否断开此次连接
    close = 0
    # 请求信息记录，校验响应信息
    reqList = '6666666666666666666'
    # 心跳间隔 单位：秒
    heart_beat_interval = 100
    # 巡视装置运行数据间隔 单位：秒
    patroldevice_run_interval = 3000
    # 无人机机巢运行数据间隔 单位：秒
    nest_run_interval = 3000
    # 环境数据间隔 单位：秒
    weather_interval = 3000
    # 机器人&无人机环境数据间隔，单位s
    env_interval = 3000
    # 运行参数间隔,单位s
    run_params_interval = 3000
    # 连接对象
    c_socket = ''
    # 连接地址
    c_address = ''
    # 连接兑现
    s_socket = ''
    # 连接状态
    status = 'up'
    # 任务执行状态
    runStatus = 'run'
    node = 'CloudHost'

    # 登录态 1 为开，0 为关
    Login = 0
    # 响应会话号
    respSign = []
    # 响应信息
    resp = []


logger = Logging("MockTool")
date_log = time.strftime('%Y-%m-%d_%H', time.localtime())


def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)

    helper.calls = 1
    helper.__name__ = func.__name__
    return helper


class XmlStdin():
    def __init__(self):
        self.str = ""

    def write(self, value):
        self.str += value

    def toString(self):
        return self.str


def writeXml(type, code, command, itemList):
    dom = minidom.getDOMImplementation().createDocument(None, sysConfig.node, None)
    root = dom.documentElement
    element1 = dom.createElement('SendCode')
    element1.appendChild(dom.createTextNode(sysConfig.sendCode))
    root.appendChild(element1)
    element2 = dom.createElement('ReceiveCode')
    element2.appendChild(dom.createTextNode(sysConfig.receiveCode))
    root.appendChild(element2)
    element3 = dom.createElement('Type')
    element3.appendChild(dom.createTextNode(type))
    root.appendChild(element3)
    element4 = dom.createElement('Code')
    element4.appendChild(dom.createTextNode(code))
    root.appendChild(element4)
    element5 = dom.createElement('Command')
    element5.appendChild(dom.createTextNode(command))
    root.appendChild(element5)
    element6 = dom.createElement('Time')
    element6.appendChild(dom.createTextNode(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    root.appendChild(element6)
    element7 = dom.createElement('Items')
    root.appendChild(element7)
    if itemList:
        for item in itemList:
            sub_element1 = dom.createElement('Item')
            for k, v in item.items():
                sub_element1.setAttribute(k, str(v))
                element7.appendChild(sub_element1)
    else:
        pass
    xmlStdin = XmlStdin()
    sys.stdin = xmlStdin
    dom.writexml(sys.stdin, addindent='\t', newl='\n', encoding='utf-8')
    xmlContent = xmlStdin.toString()
    return xmlContent


def packetize(sessionSource, sessionNum, sendXmlContent):
    # sessionSourceId：会话标识--------------请求 00，接收响应 01
    if sessionSource == "请求":
        sessionSourceId = '00'
        sendSessionNum = sessionNum
        receiveSessionNum = '0'
    elif sessionSource == "响应":
        sessionSourceId = '01'
        sendSessionNum = '0'
        receiveSessionNum = sessionNum
    else:
        sendSessionNum = '66666'
        receiveSessionNum = '66666'
        sessionSourceId = '02'
    # 发送会话序列号
    sendSessionNum = struct.pack('q', int(sendSessionNum)).hex()
    # 接收会话序列号
    receiveSessionNum = struct.pack('q', int(receiveSessionNum)).hex()
    # xml长度
    sendXmlLen = struct.pack('i', len(sendXmlContent.encode())).hex()
    # sendXmlContent: 调用writeXml()返回
    sendXmlContent = binascii.hexlify(sendXmlContent.encode()).decode('utf8', 'ignore')
    # 拼接报文
    sendMessage = 'EB90' + sendSessionNum + receiveSessionNum + sessionSourceId + sendXmlLen + sendXmlContent + 'EB90'
    sendMessage = binascii.unhexlify(sendMessage)
    return sendMessage


def readXml(receiveXmlContent):
    root = minidom.parseString(receiveXmlContent).documentElement
    if root.nodeName != sysConfig.node:
        logger.error("***根节点不匹配：%s" % sysConfig.node, "system_")
        return ""
    recSendCode = root.getElementsByTagName('SendCode')[0].childNodes[0].data
    # 接受方校验
    if recSendCode != sysConfig.receiveCode:
        logger.error("***发送方不匹配：" + sysConfig.receiveCode, "system_")
        return ""
    # 接收方唯一标识
    recReceiveCode = root.getElementsByTagName('ReceiveCode')[0].childNodes[0].data
    if recReceiveCode != sysConfig.sendCode:
        logger.error("***接收方%s不匹配：" % recReceiveCode + sysConfig.sendCode, "system_")
        return ""
    # 消息类型
    recMessageType = root.getElementsByTagName('Type')[0].childNodes[0].data
    # 接收消息时，编码，如果是接收响应消息，就是100/200/400/500 ,如果是接收请求消息，就是 变电站编码
    recMessageCode = root.getElementsByTagName('Code')[0].childNodes
    # 有些消息无Code
    if recMessageCode:
        recMessageCode = recMessageCode[0].data
    else:
        recMessageCode = ''
    # 接收的指令
    recMessageCommand = root.getElementsByTagName('Command')[0].childNodes
    # 有些消息无指令
    if recMessageCommand:
        recMessageCommand = recMessageCommand[0].data
    else:
        recMessageCommand = ''
    # 接收消息的时间
    recMessageTime = root.getElementsByTagName('Time')[0].childNodes[0].data
    # 接收消息的Item
    recItemList = root.getElementsByTagName('Items')[0].childNodes
    if recItemList:
        recItemList = [{k: v for k, v in i.attributes.items()} for item in root.getElementsByTagName('Items') for i in
                       item.getElementsByTagName('Item')]
    else:
        recItemList = ''
    return {"recMessageType": recMessageType, "recMessageCode": recMessageCode, "recMessageCommand": recMessageCommand, "recMessageTime": recMessageTime, "recItemList": recItemList}


def func(type, code, command, itemList):
    actionCount = send_msg.calls
    sendContent = writeXml(type, code, command, itemList)
    sendMessage = packetize("请求", str(actionCount), sendContent)
    send_msg(sysConfig.c_socket, sendMessage)
    logger.info("-----控制指令已发送：" + str(sendMessage), "system_")
    Thread(target=recv_msg).start()
    sysConfig.respSign.append({
        'actionCount': actionCount,
        'requestXMl': str(sendContent)
    })


def res(code, sendSessionNum, confirm, resList=None):
    if code == 3:
        if str(confirm) == "True":
            resXmlContent = writeXml("251", "200", "3", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        elif str(confirm) == "False":
            resXmlContent = writeXml("251", "400", "3", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        elif str(confirm) == "None":
            resXmlContent = writeXml("251", "500", "3", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        else:
            resXmlContent = writeXml("251", "100", "3", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        return str(responseMessage)
    elif code == 4:
        if str(confirm) == "True":
            resXmlContent = writeXml("251", "200", "4", resList)
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        elif str(confirm) == "False":
            resXmlContent = writeXml("251", "400", "4", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        elif str(confirm) == "None":
            resXmlContent = writeXml("251", "500", "4", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        else:
            resXmlContent = writeXml("251", "100", "4", "")
            responseMessage = packetize("响应", str(sendSessionNum), resXmlContent)
            logger.info("**响应会话：" + str(responseMessage), "system_")
            send_msg(sysConfig.c_socket, responseMessage)
        return str(responseMessage)
def recv_msg():
    receiveMesList = []
    while sysConfig.status == 'connect':
        receiveMessage = sysConfig.c_socket.recv(1024)
        logger.debug("***receiveMessage：" + str(receiveMessage), "system_")
        if receiveMessage != b'':
            if receiveMessage.endswith(b'\xeb\x90') and receiveMessage.startswith(b'\xeb\x90'):
                logger.debug("*****报文开头结尾校验通过：EB90*****", "system_")
                l = receiveMessage.split(b'\xeb\x90')
                for i in l:
                    if i != b'':
                        logger.debug("+++++报文内容：{m}+++++".format(m=i), "system_")
                        # 启用消息处理
                        Thread(target=msg_control, args=(i,)).start()
                        # 消息入库
                        receivePack = i.hex()
                        receivePack = receivePack.upper()
                        receiveXmlContent = receivePack[42:]
                        receiveXmlContent = binascii.unhexlify(receiveXmlContent).decode()
                        receiveDict = readXml(receiveXmlContent)
                        connDB.insert_recv_message(receiveDict)
                        logger.debug("+++++报文入库：{r}+++++".format(r=receiveDict), "system_")
                    continue
            else:
                logger.debug("++++++++++收到的报文开头结尾错误,进入等待+++++", "system_")
                logger.debug("**********报文内容：" + str(receiveMessage) + "*****", "system_")
                logger.debug("==========接收报文内容：" + str(receiveMessage) + "=====", "system_")
                receiveMesList.append(receiveMessage)
                if receiveMessage.endswith(b'\xeb\x90'):
                    receiveMessage = b''.join(receiveMesList)
                    l = receiveMessage.split(b'\xeb\x90')
                    for i in l:
                        if i != b'':
                            logger.debug("+++++报文内容：{m}+++++".format(m=i), "system_")
                            # 启用消息处理
                            Thread(target=msg_control, args=(i,)).start()
                            # 消息入库
                            receivePack = i.hex()
                            receivePack = receivePack.upper()
                            receiveXmlContent = receivePack[42:]
                            receiveXmlContent = binascii.unhexlify(receiveXmlContent).decode()
                            receiveDict = readXml(receiveXmlContent)
                            # connDB.insert_recv_message(receiveDict)
                            logger.debug("+++++报文入库：{r}+++++".format(r=receiveDict), "system_")
                    continue
        else:
            continue
    if sysConfig.status == 'close':
        # 关闭与客户端的连接
        sysConfig.c_socket.close()
        if sysConfig.s_socket != '':
            # 关闭与服务端的连接
            sysConfig.s_socket.close()
        # 断开连接
        logger.info("*****模拟器断开连接，连接对象：%s*****" % str(sysConfig.c_address), "system_")


def msg_control(i):
    recMessageContent = depacketize(i)
    logger.debug("******消息处理完成：{m}+++++".format(m=recMessageContent), "system_")


def depacketize(receiveMessage):
    receivePack = receiveMessage.hex()
    receivePack = receivePack.upper()
    # 发送会话号
    sendSessionNum = receivePack[0:16]
    sendSessionNum = int.from_bytes(binascii.unhexlify(sendSessionNum), 'little')
    # 接收会话号
    receiveSessionNum = receivePack[16:32]
    receiveSessionNum = int.from_bytes(binascii.unhexlify(receiveSessionNum), 'little')
    # 会话标识：00请求  01接收响应
    sessionSourceId = receivePack[32:34]
    # xml长度
    receiveXmlLen = receivePack[34:42]
    receiveXmlLen = int.from_bytes(binascii.unhexlify(receiveXmlLen), 'little')
    # xml内容
    receiveXmlContent = receivePack[42:]
    receiveXmlContent = binascii.unhexlify(receiveXmlContent).decode()
    receiveDict = readXml(receiveXmlContent)
    logger.info("**发送会话号：" + str(sendSessionNum), "system_")
    logger.info("**接收会话号：" + str(receiveSessionNum), "system_")
    logger.info("**会话标识：" + str(sessionSourceId), "system_")
    logger.info("==========xml内容" + str(receiveDict), "system_")
    if receiveDict == "":
        logger.error("报文解析错误：receiveDict为空", "system_")
        return '报文解析错误：receiveDict为空'
    recMessageType = receiveDict['recMessageType']
    recMessageCode = receiveDict['recMessageCode']
    recMessageCommand = receiveDict['recMessageCommand']
    recMessageTime = receiveDict['recMessageTime']
    recItemList = receiveDict['recItemList']
    confirmContent = '------未解析接收响应内容'
    # 标识会话请求
    if str(sessionSourceId) == '00':
        try:
            if sysConfig.model in ['Superior']:
                confirm, confirmContent = North_validation(receiveDict).call_functon()
            elif sysConfig.model in ['Area']:
                confirm, confirmContent = Area_validation(receiveDict).call_functon()
            elif sysConfig.model in ['Edge']:
                confirm, confirmContent = Edge_validation(receiveDict).call_functon()
            elif sysConfig.model in ['Robot']:
                confirm, confirmContent = Robot_validation(receiveDict).call_functon()
            elif sysConfig.model in ['Drone']:
                confirm, confirmContent = Drone_validation(receiveDict).call_functon()
            elif sysConfig.model in ['Waite']:
                confirm, confirmContent = Area_validation(receiveDict).call_functon()
            elif sysConfig.model in ['Algo']:
                # confirm, confirmContent = Algo_validation(receiveDict).call_functon()
                confirm = "True"
                confirmContent = '忽略校验'
            if recMessageType == '251':
                if recMessageCommand == '1':
                    if sysConfig.model in ['Algo']:
                        resList = [{'heart_beat_interval': sysConfig.heart_beat_interval,
                                    'run_params_interval': '10'
                                    }]
                    else:
                        resList = [{'heart_beat_interval': sysConfig.heart_beat_interval,
                                    'patroldevice_run_interval': sysConfig.patroldevice_run_interval,
                                    'nest_run_interval': sysConfig.nest_run_interval,
                                    'weather_interval': sysConfig.weather_interval,
                                    }]
                    responseMessage = res(4, sendSessionNum, confirm, resList)
                elif recMessageCommand == '2':
                    responseMessage = res(3, sendSessionNum, confirm)
                else:
                    responseMessage = "未定义的指令"
            elif recMessageType == '316':
                resList=[{
                        "algorithm_manufacturer": "江行联加",
                        "version": "V1.0",
                        "record_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                        "algorithm_path": "algoTest/2_jxzn_0.0.1.zip",
                    }]
                responseMessage = res(4, sendSessionNum, confirm, resList)
            elif recMessageType == '41':
                resList=[{
                        "task_patrolled_id": str("1_" + str(recMessageCode) + "_" + time.strftime("%Y%m%d%H%M%S", time.localtime()))
                    }]
                responseMessage = res(4, sendSessionNum, confirm, resList)
            else:
                responseMessage = res(3, sendSessionNum, confirm)
            return responseMessage
        except Exception:
            logger.error("报文校验并响应错误：" + "【" + str(receiveXmlContent) + "】", "system_")
            return '报文校验并响应错误'
    # 标识会话接收响应
    elif str(sessionSourceId) == '01':
        if recMessageType == '251':
            for i in sysConfig.respSign:
                if receiveSessionNum == i['actionCount']:
                    sysConfig.resp.append({
                        'receiveSessionNum': receiveSessionNum,
                        'receiveXMl': [receiveXmlContent]
                    })
                    logger.info("**接收响应信息：" + "：【" + str(receiveXmlContent) + "】", "system_")
            if recMessageCommand == '3':
                if str(recMessageCode) == '200':
                    confirmContent = '正常响应！' + '\n' + str(receiveXmlContent)
                elif str(recMessageCode) == '500':
                    confirmContent = '请求错误，响应500！' + '\n' + str(receiveXmlContent)
                elif str(recMessageCode) == '400':
                    confirmContent = '请求被拒绝，响应400！' + '\n' + str(receiveXmlContent)
                elif str(recMessageCode) == '100':
                    confirmContent = '请求需重发，响应100！' + '\n' + str(receiveXmlContent)
                else:
                    confirmContent = '指令发送失败！' + '\n' + str(receiveXmlContent)
            elif recMessageCommand == '4':
                if sysConfig.model in ['Robot', 'Drone']:  # P.5.2 注册指令，机器人/无人机与边缘节点装置建立通信连接后，返回消息中需携带上报时间信息，
                    if sysConfig.model == 'Robot':
                        regis_l = ['heart_beat_interval', 'patroldevice_run_interval', 'env_interval']
                        if list(sorted(receiveDict['recItemList'][0].keys())) == sorted(regis_l):
                            # 心跳间隔时长，单位s
                            sysConfig.heart_beat_interval = int(receiveDict['recItemList'][0]['heart_beat_interval'])
                            # 巡视设备运行数据间隔，单位s
                            sysConfig.patroldevice_run_interval = int(
                                receiveDict['recItemList'][0]['patroldevice_run_interval'])
                            # 环境数据间隔，单位s
                            sysConfig.env_interval = int(receiveDict['recItemList'][0]['env_interval'])
                            # Login置为1，开始发起心跳
                            sysConfig.Login = 1
                            confirmContent = '心跳指令响应：心跳间隔-{h}、巡视设备运行数据间隔-{d}、环境数据上报间隔-{e}'.format(h=sysConfig.heart_beat_interval, d=sysConfig.patroldevice_run_interval, e=sysConfig.env_interval)
                        else:
                            confirmContent = '未录入的响应内容，请处理：' + '\n' + str(receiveDict)
                    elif sysConfig.model == 'Drone':
                        regis_l = ['heart_beat_interval', 'patroldevice_run_interval', 'nest_run_interval',
                                   'env_interval']
                        if list(sorted(receiveDict['recItemList'][0].keys())) == sorted(regis_l):
                            # 心跳间隔时长，单位s
                            sysConfig.heart_beat_interval = int(receiveDict['recItemList'][0]['heart_beat_interval'])
                            # 巡视设备运行数据间隔，单位s
                            sysConfig.patroldevice_run_interval = int(
                                receiveDict['recItemList'][0]['patroldevice_run_interval'])
                            # # 无人机机巢运行数据间隔，单位s
                            sysConfig.nest_run_interval = int(receiveDict['recItemList'][0]['nest_run_interval'])
                            # 环境数据间隔，单位s
                            sysConfig.env_interval = int(receiveDict['recItemList'][0]['env_interval'])
                            # Login置为1，开始发起心跳
                            sysConfig.Login = 1
                            confirmContent = '心跳指令响应：心跳间隔-{h}、巡视设备运行数据间隔-{d}、无人机机巢运行数据间隔-{n}、环境数据上报间隔-{e}'.format(h=sysConfig.heart_beat_interval, d=sysConfig.patroldevice_run_interval, n=sysConfig.nest_run_interval, e=sysConfig.env_interval)
                        else:
                            confirmContent = '未录入的响应内容，请处理：' + '\n' + str(receiveDict)
                elif sysConfig.model in ['Superior', 'Area', 'Edge']:
                    regis_l = ['heart_beat_interval', 'patroldevice_run_interval', 'nest_run_interval',
                               'weather_interval']
                    if sorted(list(receiveDict['recItemList'][0].keys())) == sorted(regis_l):
                        # 心跳间隔时长，单位s
                        sysConfig.heart_beat_interval = int(receiveDict['recItemList'][0]['heart_beat_interval'])
                        # 巡视设备运行数据间隔，单位s
                        sysConfig.patroldevice_run_interval = int(
                            receiveDict['recItemList'][0]['patroldevice_run_interval'])
                        # # 无人机机巢运行数据间隔，单位s
                        sysConfig.nest_run_interval = int(receiveDict['recItemList'][0]['nest_run_interval'])
                        # 环境数据间隔，单位s
                        sysConfig.env_interval = int(receiveDict['recItemList'][0]['weather_interval'])
                        # Login置为1，开始发起心跳
                        sysConfig.Login = 1
                        confirmContent = '心跳指令响应：心跳间隔-{h}、巡视设备运行数据间隔-{d}、无人机机巢运行数据间隔-{n}、环境数据上报间隔-{e}'.format(h=sysConfig.heart_beat_interval, d=sysConfig.patroldevice_run_interval, n=sysConfig.nest_run_interval, e=sysConfig.weather_interval)
                        # 模拟发送静默监视数据
                        def Test():
                            while True:
                                actionCount = send_msg.calls
                                sendContent = writeXml("64", "", "", [{'patroldevice_code': 'Robot03', 'device_name': '静默点位1', 'device_id': '9900001', 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'rectangle': '', 'file_type': '2', 'file_path': 'wcaqm.png', 'monitor_type': '1'}])
                                sendMessage = packetize("请求", str(actionCount), sendContent)
                                send_msg(sysConfig.c_socket, sendMessage)
                                logger.info("-----静默监视数据已发送：" + str(sendContent), "system_")
                                time.sleep(10)
                        Test()
                    else:
                        confirmContent = '未录入的响应内容，请处理：' + '\n' + str(receiveDict)

                elif sysConfig.model in ['Algo']:
                    regis_l = ['heart_beat_interval', 'run_params_interval']
                    if sorted(list(receiveDict['recItemList'][0].keys())) == sorted(regis_l):
                        # 心跳间隔时长，单位s
                        sysConfig.heart_beat_interval = int(receiveDict['recItemList'][0]['heart_beat_interval'])
                        # 巡视设备运行数据间隔，单位s
                        sysConfig.run_params_interval = int(receiveDict['recItemList'][0]['run_params_interval'])
                        # Login置为1，开始发起心跳
                        sysConfig.Login = 1
                        confirmContent = '心跳指令响应：心跳间隔-{h}、运行数据间隔-{r}'.format(h=sysConfig.heart_beat_interval, r=sysConfig.run_params_interval)
                    else:
                        confirmContent = '未录入的响应内容，请处理：' + '\n' + str(receiveDict)

            logger.info("**接收响应信息：" + "：【" + str(confirmContent) + "】", "system_")
            return str(confirmContent)
        else:
            logger.error("！！！响应类型非251 系统消息！！！", "system_")
            return '响应类型非251'
    else:
        logger.error("！！！会话标识错误！！！", "system_")
        return '会话标识错误'


class initface():

    def __init__(self, window):
        self.window = window
        self.window.title('搞事情的模拟器')
        self.window.geometry('1000x600')
        self.loginFrame = Frame(self.window, bg="#fffff3")
        self.loginFrame.place(width=1000, height=600, x=0)
        self.mainFrame = Frame(self.window, bg="#fffff3")
        self.mainFrame2()

    def s_up(self):
        # 等待客户端连接
        # 创建一个socket对象
        sysConfig.s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while sysConfig.status != 'close':
            if sysConfig.status != 'connect':
                # 绑定socket到ip和端口
                sysConfig.s_socket.bind((sysConfig.IP, sysConfig.Port))
                # 设置最大连接数，超过后排队
                sysConfig.s_socket.listen(10)
                sysConfig.c_socket, sysConfig.c_address = sysConfig.s_socket.accept()
                # 连接成功
                sysConfig.status = 'connect'
                logger.info("*****模拟器创建服务端成功，连接对象：%s*****" % str(sysConfig.c_address), "system_")
                # 启用消息接收
                Thread(target=recv_msg).start()
                break
            else:
                break

    def c_up(self):
        # 尝试客户端连接
        sysConfig.s_socket = ''
        while sysConfig.status != 'close':
            if sysConfig.status != 'connect':
                sysConfig.c_socket = socket.socket(AF_INET, SOCK_STREAM)
                # 连接socket到ip和端口
                sysConfig.c_socket.connect((sysConfig.IP, sysConfig.Port))
                sysConfig.c_address = sysConfig.IP
                # 连接成功
                sysConfig.status = 'connect'
                logger.info("*****模拟器客户端连接成功，连接对象：%s*****" % str(sysConfig.c_address), "system_")

                # 启用注册
                Thread(target=self.login).start()
                # 启用心跳
                Thread(target=self.heartbeat).start()
                break
            else:
                break

    def login(self):
        actionCount = send_msg.calls
        sendContent = writeXml("251", "", "1", "")
        sendMessage = packetize("请求", str(actionCount), sendContent)
        send_msg(sysConfig.c_socket, sendMessage)
        logger.info("-----注册指令已发送：" + str(sendContent), "system_")
        # 启用消息接收
        Thread(target=recv_msg).start()
        # 启用消息处理
        Thread(target=msg_control).start()

    def heartbeat(self):
        while True:
            if sysConfig.status != 'close':
                if sysConfig.Login == 1:
                    time.sleep(sysConfig.heart_beat_interval)
                    actionCount = send_msg.calls
                    sendContent = writeXml("251", "", "2", "")
                    sendMessage = packetize("请求", str(actionCount), sendContent)
                    send_msg(sysConfig.c_socket, sendMessage)
                    logger.info("-----心跳指令已发送：" + str(sendContent), "system_")
                    Thread(target=recv_msg).start()
            else:
                break

    def close(self):
        sysConfig.status = 'close'

    def up(self, select, TKIp, TKPort, TKsendCode, TKreceiveCode):
        sysConfig.IP = TKIp
        sysConfig.Port = int(TKPort)
        sysConfig.sendCode = TKsendCode
        sysConfig.receiveCode = TKreceiveCode
        sysConfig.status = 'up'
        if select == '上级系统':
            sysConfig.model = 'Superior'
            sysConfig.node = 'PatrolHost'
            Thread(target=self.s_up).start()
        elif select == '区域主机':
            sysConfig.model = 'Area'
            sysConfig.node = 'PatrolHost'
            Thread(target=self.c_up).start()
        elif select == '边缘节点':
            sysConfig.model = 'Edge'
            sysConfig.node = 'PatrolHost'
            Thread(target=self.c_up).start()
        elif select == '机器人':
            sysConfig.model = 'Robot'
            sysConfig.node = 'PatrolDevice'
            Thread(target=self.c_up).start()
        elif select == '无人机':
            sysConfig.model = 'Drone'
            sysConfig.node = 'PatrolDevice'
            Thread(target=self.c_up).start()
        elif select == '声纹检测设备':
            sysConfig.model = 'waiting'
            Thread(target=self.c_up).start()
        elif select == '主辅控':
            sysConfig.model = 'waiting'
            Thread(target=self.c_up).start()
        elif select == '算法管理平台':
            sysConfig.model = 'Algo'
            sysConfig.node = 'CloudHost'
            Thread(target=self.s_up).start()
        else:
            sysConfig.model = 'Superior'
            sysConfig.node = 'PatrolHost'
            raise Exception

    def mainFrame2(self):

        # 模拟器连接
        self.c_f = Frame(self.loginFrame, bg="#fffff3")
        self.c_f.pack(side="left", fill='both', pady=1)

        listbox = Listbox(self.loginFrame, bg="#fffff3")
        listbox.insert(1, '上级系统')
        listbox.insert(2, '区域主机')
        listbox.insert(3, '边缘节点')
        listbox.insert(4, '机器人')
        listbox.insert(5, '无人机')
        listbox.insert(6, '声纹')
        listbox.insert(7, '主辅控')
        listbox.insert(8, '算法管理平台')
        listbox.pack(side="right", fill='both', padx=5, pady=1)

        def get_list():
            listbox.activate(1)
            indexs = [index for index in listbox.curselection()]
            select = [listbox.get(index) for index in indexs]
            return select

        c_f_r0 = Frame(self.c_f, bg='#fffff3')
        c_f_r0.pack(side="top", fill="both", pady=1)
        Label(c_f_r0, text="IP地址", font=(
        "华文楷体", 10, "bold"), bg="#fffff3", fg="#5f6c7b").pack(side="left", fill="y", padx=5)

        c_f_r1_1 = Frame(self.c_f, bg='#fffff3')
        c_f_r1_1.pack(side="top", fill="both", pady=1)
        inputIP = StringVar()
        inputIP.set(sysConfig.IP)

        self.inputIP = Entry(c_f_r1_1, textvariable=inputIP, bg="#fffff3", width=50, fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        self.inputIP.pack(side="left", padx=5, pady=1)

        inputPort = StringVar()
        inputPort.set(str(sysConfig.Port))
        self.inputPort = Entry(c_f_r1_1, textvariable=inputPort, bg="#fffff3", width=50, fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        self.inputPort.pack(side="left", padx=5, pady=1)

        c_f_r1_2 = Frame(self.c_f, bg='#fffff3')
        c_f_r1_2.pack(side="top", fill="both", pady=1)
        input_sendCode = StringVar()
        input_sendCode.set(sysConfig.sendCode)

        self.input_sendCode = Entry(c_f_r1_2, textvariable=input_sendCode, bg="#fffff3", width=50, fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        self.input_sendCode.pack(side="left", padx=5, pady=1)

        input_receiveCode = StringVar()
        input_receiveCode.set(sysConfig.receiveCode)
        self.input_receiveCode = Entry(c_f_r1_2, textvariable=input_receiveCode, bg="#fffff3", width=50, fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        self.input_receiveCode.pack(side="left", padx=5, pady=1)

        c_f_r2 = Frame(self.c_f, bg='#fffff3')
        c_f_r2.pack(side="top", fill="x", pady=1)

        c_b1 = Button(c_f_r2, text="连接", fg='#fffff3', bg='#378DFC', width=10, relief=FLAT, command=lambda: self.up(
            get_list()[0], inputIP.get(), inputPort.get(), input_sendCode.get(), input_receiveCode.get()))
        c_b1.pack(side="left", padx=5, pady=1)

        c_b2 = Button(c_f_r2, text="断开连接", fg='#fffff3', bg='#378DFC', width=10, relief=FLAT, command=lambda: self.close())
        c_b2.pack(side="left", padx=5, pady=1)

        c_f_r3 = Frame(self.c_f, bg='#fffff3')
        c_f_r3.pack(side="top", fill="x", pady=1)
        Label(c_f_r3, text="执行测试任务：", font=(
        "华文楷体", 10, "bold"), bg="#fffff3", fg="#5f6c7b").pack(side="left", fill="y", padx=5)
        self.run_file = StringVar()
        self.run_file.set(sysConfig.run_file)
        c_f_r3_f = Entry(c_f_r3, width=20, textvariable=self.run_file, bg="#fffff3", fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        c_f_r3_f.pack(side="left", padx=5)
        self.run_sheet = StringVar()
        self.run_sheet.set(sysConfig.run_sheet)
        c_f_r3_v = Entry(c_f_r3, width=20, textvariable=self.run_sheet, bg="#fffff3", fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        c_f_r3_v.pack(side="left", padx=5)

        c_f_r4 = Frame(self.c_f, bg='#fffff3')
        c_f_r4.pack(side="top", fill="x", pady=1)
        Label(c_f_r4, text="测试记录：", font=(
        "华文楷体", 10, "bold"), bg="#fffff3", fg="#5f6c7b").pack(side="left", fill="y", padx=5)
        self.save_file = StringVar()
        self.save_file.set(sysConfig.save_file)
        c_f_r4_f = Entry(c_f_r4, width=20, textvariable=self.save_file, bg="#fffff3", fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        c_f_r4_f.pack(side="left", padx=5)
        self.save_sheet = StringVar()
        self.save_sheet.set(sysConfig.save_sheet)
        c_f_r4_v = Entry(c_f_r4, width=20, textvariable=self.save_sheet, bg="#fffff3", fg="#5f6c7b", highlightcolor="#378DFC", highlightthickness=1)
        c_f_r4_v.pack(side="left", padx=5)

        c_f_r5 = Frame(self.c_f, bg='#fffff3')
        c_f_r5.pack(side="top", fill="x", pady=1)
        c_b3 = Button(c_f_r5, text="开始执行", bg='#378DFC', fg='#fffff3', width=10, relief=FLAT, command=lambda: self.runningtest())
        c_b3.pack(side="left", padx=5, pady=1)

        c_b4 = Button(c_f_r5, text="停止执行", bg='#378DFC', fg='#fffff3', width=10, relief=FLAT, command=lambda: self.stoptest())
        c_b4.pack(side="left", padx=5, pady=1)

    def start_calendar(self, timeInput):
        def print_sel():
            s_data = str(cal.selection_get()) + " " + str(hour.get()) + ":" + str(minute.get() + ":" + str(second.get()))
            timeInput.set(s_data)
            cal.see(datetime.date(year=2016, month=2, day=5))
            top.destroy()

        top = Toplevel()
        top.geometry("300x250")
        top.config(bg="#fffff3")
        mindate = datetime.date(year=2016, month=1, day=1)

        cal = ca(top, font="Arial 10", selectmode='day', locale='zh_CN', mindate=mindate, background="#fffff3", foreground="#378DFC", bordercolor="#fffff3", selectbackground="lightcyan", selectforeground="#378DFC")
        cal.place(x=0, y=0, width=300, height=200)
        values_h = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                    20, 21, 22, 23]
        values_m = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                    20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
                    45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
        hour = ttk.Combobox(
            master=top,  # 父容器
            height=15,  # 高度,下拉显示的条目数量
            width=3,  # 宽度
            state="normal",  # 设置状态 normal(可选可输入)、readonly(只可选)、 disabled
            cursor="arrow",  # 鼠标移动时样式 arrow, circle, cross, plus...
            font=("", 12),  # 字体
            values=values_h,  # 设置下拉框的选项
        )
        hour.current("07")
        hour.place(x=5, y=205)
        Label(top, text="时", bg="#fffff3").place(x=55, y=195, width=20, height=40)

        minute = ttk.Combobox(
            master=top,  # 父容器
            height=15,  # 高度,下拉显示的条目数量
            width=3,  # 宽度
            state="normal",  # 设置状态 normal(可选可输入)、readonly(只可选)、 disabled
            cursor="arrow",  # 鼠标移动时样式 arrow, circle, cross, plus...
            font=("", 12),  # 字体
            values=values_m,  # 设置下拉框的选项
        )
        minute.current("00")
        minute.place(x=85, y=205)
        Label(top, text="分", bg="#fffff3").place(x=135, y=195, width=20, height=40)
        second = ttk.Combobox(
            master=top,  # 父容器
            height=15,  # 高度,下拉显示的条目数量
            width=3,  # 宽度
            state="normal",  # 设置状态 normal(可选可输入)、readonly(只可选)、 disabled
            cursor="arrow",  # 鼠标移动时样式 arrow, circle, cross, plus...
            font=("", 12),  # 字体
            values=values_m,  # 设置下拉框的选项
        )
        second.current("00")
        second.place(x=170, y=205)
        Label(top, text="秒", bg="#fffff3").place(x=225, y=195, width=20, height=40)
        Button(top, text="确定", command=print_sel, bg='#378DFC', fg='#fffff3', relief=FLAT).place(x=260, y=205)

    def stoptest(self):
        sysConfig.runStatus = 'stop'

    def runningtest(self):
        sysConfig.runStatus = 'run'
        Thread(target=self.runtest).start()

    def runtest(self):
        exceldata = {
            'Request': [],
            'RelRequest': [],
            'Response': [],
            'result': [],
            'TestTime': [],
            'Tester': [],
        }
        do_excel = DoExcel(self.run_file.get(), self.run_sheet.get())
        cases = do_excel.raed()
        for i in range(len(cases) -1):
            if sysConfig.runStatus == 'stop':
                break
            else:
                try:
                    logger.info('用例开始执行：' + str(cases[i].TestPoint), "system_")
                    data = json.loads(cases[i].Request)
                    exceldata['Request'].insert(len(exceldata['Request']), str(data))
                    sysConfig.sendCode = data['sendCode']
                    sysConfig.receiveCode = data['receiveCode']
                    sysConfig.model = data['model']
                    if data['type'] == '':
                        if 'time' not in str(cases[i].TestPoint):
                            for i in data['itemList']:
                                i['time'] = str(datetime.datetime.today().replace(second=0, microsecond=0))
                    elif data['type'] == '6':
                        if 'source_time' not in str(cases[i].TestPoint):
                            for i in data['itemList']:
                                i['source_time'] = str(datetime.datetime.today().replace(second=0, microsecond=0))
                    func(data['type'], data['code'], data['command'], data['itemList'])
                    logger.info("-----请求数据已发送：" + str(data), "system_")
                except Exception as e:
                    logger.info(f"-----请求异常：{e}", "system_")
                    break
                # s_t = int(time.time())
                # logger.info('开始等待响应：' + str(int(time.time())), "system_")
                # while True:
                #     e_t = int(time.time())
                #     if (e_t - s_t) >= 3600:
                #         logger.info('请求超时（10s）：' + str(int(time.time())), "system_")
                #         sysConfig.runStatus = 'stop'
                #         logger.info('用例执行异常，停止执行：' + str(int(time.time())), "system_")
                #         sysConfig.respSign = []
                #         sysConfig.resp = []
                #         break
                #     else:
                #         if sysConfig.respSign == [] or sysConfig.resp == []:
                #             time.sleep(1)
                #         else:
                #             for i in sysConfig.respSign:
                #                 for r in sysConfig.resp:
                #                     if i['actionCount'] == r['receiveSessionNum']:
                #                         exceldata['RelRequest'].insert(len(exceldata['RelRequest']), str(
                #                             i['requestXMl']))
                #                         exceldata['Response'].insert(len(exceldata['Response']), str(r['receiveXMl']))
                #                         exceldata['result'].insert(len(exceldata['result']), 'success')
                #                         exceldata['TestTime'].insert(len(exceldata[
                #                                                              'TestTime']), str(datetime.datetime.today().replace(second=0, microsecond=0)))
                #                         exceldata['Tester'].insert(len(exceldata['Tester']), '唐心林')
                #                         sysConfig.respSign.remove(i)
                #                         sysConfig.resp.remove(r)
                #                         logger.info('结束等待响应：' + str(time.time()), "system_")
                #                         logger.info('响应内容：' + str(r['receiveXMl']), "system_")
                #             if sysConfig.resp == [] or sysConfig.respSign == []:
                #                 break
                #             else:
                #                 time.sleep(1)
        if exceldata['Request'] == []:
            pass
        else:
            content = do_excel.save_d(exceldata, self.save_file.get(), self.save_sheet.get())
            logger.info('%s：' % content + str(int(time.time())), "system_")


def Jieshu():
    messagebox.showwarning(title='提示', message='退出客户端')
    sys.exit(0)


@call_counter
def send_msg(client_s_socket, msg):
    client_s_socket.send(msg)


if __name__ == '__main__':
    window = Tk()
    initface(window)
    window.protocol("WM_DELETE_WINDOW", Jieshu)
    window.mainloop()
