from database import get_db
from models.device import Device

db = next(get_db())
devices = db.query(Device).all()
print('数据库中的设备:')
for device in devices:
    print(f'ID: {device.id}, 名称: {device.name}, 类型: {device.type}')
