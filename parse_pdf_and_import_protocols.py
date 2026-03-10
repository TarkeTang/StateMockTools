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

# 解析PDF文件
def parse_pdf(filename):
    protocols = []
    
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
            
            # 生成协议ID
            protocol_id = f"{appendix['device_type'].upper()}-{appendix['name']}"
            
            # 提取字段信息（这里需要根据实际PDF内容进行解析，这里只是示例）
            fields = []
            # 实际项目中，需要根据PDF内容解析字段信息
            # 这里我们模拟一些字段
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
            fields.append({
                'name': 'Items',
                'type': 'Object',
                'length': '-',
                'required': '否',
                'description': '消息项'
            })
            
            # 构建协议数据
            protocol = {
                'id': protocol_id,
                'name': appendix['title'],
                'type': 'system_message',  # 根据实际情况调整
                'device_type': appendix['device_type'],
                'interaction_object': appendix['interaction_object'],
                'version': '1.0',
                'structure': f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<{appendix['device_type']}>\n    <SendCode> sender </SendCode>\n    <ReceiveCode> receiver </ReceiveCode>\n    <Type> message_type </Type>\n    <Code> message_code </Code>\n    <Command> command </Command>\n    <Time> timestamp </Time>\n    <Items>\n        <Item key=\"value\"/>\n    </Items>\n</{appendix['device_type']}>",
                'fields': json.dumps(fields),
                'description': appendix['title'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            protocols.append(protocol)
    
    return protocols

# 导入协议到数据库
def import_protocols(protocols):
    for protocol in protocols:
        # 检查协议是否已存在
        cursor.execute("SELECT id FROM protocols WHERE id = ?", (protocol['id'],))
        if cursor.fetchone():
            print(f"协议 {protocol['id']} 已存在，跳过导入")
            continue
        
        # 插入协议
        cursor.execute('''
        INSERT INTO protocols (id, name, type, device_type, interaction_object, version, structure, fields, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            protocol['id'],
            protocol['name'],
            protocol['type'],
            protocol['device_type'],
            protocol['interaction_object'],
            protocol['version'],
            protocol['structure'],
            protocol['fields'],
            protocol['description'],
            protocol['created_at'],
            protocol['updated_at']
        ))
        
        print(f"导入协议 {protocol['id']} 成功")
    
    conn.commit()

# 主函数
def main():
    print("开始解析57号规范.pdf...")
    protocols = parse_pdf('57号规范.pdf')
    print(f"解析完成，共获取 {len(protocols)} 个协议")
    
    print("开始导入协议到数据库...")
    import_protocols(protocols)
    print("导入完成！")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    main()
