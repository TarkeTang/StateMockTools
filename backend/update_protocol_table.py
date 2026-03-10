import sqlite3
import json

# 连接到数据库
conn = sqlite3.connect('database/state_mock_new.db')
cursor = conn.cursor()

# 检查protocols表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='protocols';")
table_exists = cursor.fetchone() is not None

if table_exists:
    print("检查表结构...")
    
    # 获取当前表结构
    cursor.execute("PRAGMA table_info(protocols);")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    print(f"当前字段: {column_names}")
    
    # 检查并添加缺失的字段
    missing_columns = []
    
    if 'interaction_object' not in column_names:
        missing_columns.append('interaction_object')
        cursor.execute("ALTER TABLE protocols ADD COLUMN interaction_object TEXT NOT NULL DEFAULT '';")
        print("添加字段: interaction_object")
    
    if 'version' not in column_names:
        missing_columns.append('version')
        cursor.execute("ALTER TABLE protocols ADD COLUMN version TEXT NOT NULL DEFAULT '1.0';")
        print("添加字段: version")
    
    if 'fields' not in column_names:
        missing_columns.append('fields')
        cursor.execute("ALTER TABLE protocols ADD COLUMN fields TEXT;")
        print("添加字段: fields")
    
    if missing_columns:
        conn.commit()
        print("表结构更新成功！")
    else:
        print("表结构已经是最新的，无需更新。")
else:
    print("protocols表不存在，将创建新表。")
    # 创建新表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS protocols (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        device_type TEXT NOT NULL,
        interaction_object TEXT NOT NULL,
        version TEXT NOT NULL,
        structure TEXT NOT NULL,
        fields TEXT,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    )
    ''')
    conn.commit()
    print("表创建成功！")

# 关闭连接
conn.close()
print("操作完成。")
