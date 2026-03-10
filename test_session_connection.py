"""
测试会话连接接口
"""
import requests
import json

# 测试会话连接接口
BASE_URL = "http://localhost:8000"

def test_get_sessions():
    """获取会话列表"""
    response = requests.get(f"{BASE_URL}/api/sessions")
    print(f"获取会话列表：{response.status_code}")
    if response.status_code == 200:
        sessions = response.json()
        print(f"会话数量：{len(sessions)}")
        for session in sessions:
            print(f"  - {session['id']}: {session['name']} ({session.get('ip')}:{session.get('port')})")
        return sessions
    else:
        print(f"错误：{response.text}")
        return []

def test_establish_connection(session_id, force=False):
    """建立会话连接"""
    print(f"\n====== 测试建立连接：{session_id}, force={force} ======")
    response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/establish-connection?force={force}")
    print(f"响应状态码：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应数据：{json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"错误：{response.text}")

if __name__ == "__main__":
    print("=== 测试会话连接接口 ===\n")
    
    # 获取会话列表
    sessions = test_get_sessions()
    
    if sessions:
        # 测试第一个会话
        session_id = sessions[0]['id']
        test_establish_connection(session_id)
    else:
        print("没有可用的会话")
