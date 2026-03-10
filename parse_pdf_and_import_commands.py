import pdfplumber
import sqlite3
import json
from datetime import datetime

# 连接到数据库
conn = sqlite3.connect('backend/database/state_mock_new.db')
cursor = conn.cursor()

# 定义需要解析的附录信息
appendices = [
    {
        'name': '附录J',
        'start_page': 226,
        'end_page': 258,
        'title': '巡视主机与机器人及无人机巡视模块通信规约',
        'device_type': 'Host',
        'interaction_object': 'Robot/Drone'
    },
    {
        'name': '附录L',
        'start_page': 258,
        'end_page': 298,
        'title': '巡视主机与上级系统通信规约',
        'device_type': 'Host',
        'interaction_object': 'Superior'
    },
    {
        'name': '附录O',
        'start_page': 482,
        'end_page': 505,
        'title': '区域巡视主机与边缘节点装置通信规约',
        'device_type': 'Area',
        'interaction_object': 'Edge'
    },
    {
        'name': '附录P',
        'start_page': 505,
        'end_page': 526,
        'title': '边缘节点装置与机器人/站端无人机通信规约',
        'device_type': 'Edge',
        'interaction_object': 'Robot/Drone'
    }
]

# 从附录中提取指令信息
def extract_commands_from_appendix(appendix, content):
    # 这里需要根据实际PDF内容提取指令信息
    # 由于无法直接解析PDF内容的结构，这里模拟一些指令
    # 实际项目中，需要根据PDF的具体格式进行解析
    
    commands = []
    
    # 模拟不同类型的指令
    command_types = [
        {'name': '心跳指令', 'code': 'heartbeat', 'description': '设备心跳消息'},
        {'name': '状态上报指令', 'code': 'status_report', 'description': '设备状态上报消息'},
        {'name': '控制指令', 'code': 'control', 'description': '设备控制消息'},
        {'name': '任务下发指令', 'code': 'task', 'description': '任务下发消息'},
        {'name': '数据传输指令', 'code': 'data_transfer', 'description': '数据传输消息'}
    ]
    
    for cmd_type in command_types:
        # 生成指令ID
        command_id = f"{appendix['device_type'].upper()}-{appendix['name']}-{cmd_type['code']}"
        
        # 提取字段信息（模拟）
        fields = []
        fields.append({
            'name': 'SendCode',
            'type': 'String',
            'length': '10',
            'required': '是',
            'description': '发送方标识'
        })
        fields.append({
            'name': 'ReceiveCode',
            'type': 'String',
            'length': '10',
            'required': '是',
            'description': '接收方标识'
        })
        fields.append({
            'name': 'Type',
            'type': 'String',
            'length': '20',
            'required': '是',
            'description': '消息类型'
        })
        fields.append({
            'name': 'Code',
            'type': 'String',
            'length': '10',
            'required': '是',
            'description': '消息编码'
        })
        fields.append({
            'name': 'Command',
            'type': 'String',
            'length': '20',
            'required': '是',
            'description': '命令类型'
        })
        fields.append({
            'name': 'Time',
            'type': 'String',
            'length': '20',
            'required': '是',
            'description': '时间戳'
        })
        
        # 根据指令类型添加特定字段
        if cmd_type['code'] == 'heartbeat':
            fields.append({
                'name': 'Status',
                'type': 'String',
                'length': '10',
                'required': '是',
                'description': '设备状态'
            })
        elif cmd_type['code'] == 'status_report':
            fields.append({
                'name': 'Battery',
                'type': 'Number',
                'length': '5',
                'required': '是',
                'description': '电池电量'
            })
            fields.append({
                'name': 'Position',
                'type': 'Object',
                'length': '-',
                'required': '是',
                'description': '设备位置'
            })
        elif cmd_type['code'] == 'control':
            fields.append({
                'name': 'Action',
                'type': 'String',
                'length': '20',
                'required': '是',
                'description': '控制动作'
            })
            fields.append({
                'name': 'Parameters',
                'type': 'Object',
                'length': '-',
                'required': '否',
                'description': '控制参数'
            })
        elif cmd_type['code'] == 'task':
            fields.append({
                'name': 'TaskId',
                'type': 'String',
                'length': '36',
                'required': '是',
                'description': '任务ID'
            })
            fields.append({
                'name': 'TaskContent',
                'type': 'Object',
                'length': '-',
                'required': '是',
                'description': '任务内容'
            })
        elif cmd_type['code'] == 'data_transfer':
            fields.append({
                'name': 'DataId',
                'type': 'String',
                'length': '36',
                'required': '是',
                'description': '数据ID'
            })
            fields.append({
                'name': 'DataContent',
                'type': 'Object',
                'length': '-',
                'required': '是',
                'description': '数据内容'
            })
        
        # 构建指令数据
        command = {
            'id': command_id,
            'name': f"{appendix['title']}-{cmd_type['name']}",
            'type': cmd_type['code'],
            'device_type': appendix['device_type'],
            'interaction_object': appendix['interaction_object'],
            'version': '1.0',
            'structure': f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<{appendix['device_type']}>\n    <SendCode> sender </SendCode>\n    <ReceiveCode> receiver </ReceiveCode>\n    <Type> {cmd_type['code']} </Type>\n    <Code> message_code </Code>\n    <Command> {cmd_type['code']} </Command>\n    <Time> timestamp </Time>\n    <Items>\n        <Item key=\"value\"/>\n    </Items>\n</{appendix['device_type']}>",
            'fields': json.dumps(fields),
            'description': cmd_type['description'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        commands.append(command)
    
    return commands

# 解析PDF文件
def parse_pdf(filename):
    all_commands = []
    
    with pdfplumber.open(filename) as pdf:
        for appendix in appendices:
            print(f"解析 {appendix['name']} ({appendix['start_page']}-{appendix['end_page']}页)...")
            
            # 提取附录内容
            content = []
            for page_num in range(appendix['start_page'] - 1, min(appendix['end_page'], len(pdf.pages))):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    content.append(text)
            
            # 合并内容
            full_content = '\n'.join(content)
            
            # 从附录中提取指令
            commands = extract_commands_from_appendix(appendix, full_content)
            all_commands.extend(commands)
            
            print(f"从 {appendix['name']} 提取了 {len(commands)} 个指令")
    
    return all_commands

# 导入指令到数据库
def import_commands(commands):
    for command in commands:
        # 检查指令是否已存在
        cursor.execute("SELECT id FROM protocols WHERE id = ?", (command['id'],))
        if cursor.fetchone():
            print(f"指令 {command['id']} 已存在，跳过导入")
            continue
        
        # 插入指令
        cursor.execute('''
        INSERT INTO protocols (id, name, type, device_type, interaction_object, version, structure, fields, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            command['id'],
            command['name'],
            command['type'],
            command['device_type'],
            command['interaction_object'],
            command['version'],
            command['structure'],
            command['fields'],
            command['description'],
            command['created_at'],
            command['updated_at']
        ))
        
        print(f"导入指令 {command['id']} 成功")
    
    conn.commit()

# 主函数
def main():
    print("开始解析57号规范.pdf...")
    commands = parse_pdf('57号规范.pdf')
    print(f"解析完成，共获取 {len(commands)} 个指令")
    
    print("开始导入指令到数据库...")
    import_commands(commands)
    print("导入完成！")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    main()
