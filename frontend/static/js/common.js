// 导航功能
function setupNavigation() {
    const menuItems = document.querySelectorAll('.sidebar li');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            // 移除所有菜单项的 active 类
            menuItems.forEach(menuItem => {
                menuItem.classList.remove('active');
            });
            // 添加当前菜单项的 active 类
            this.classList.add('active');

            // 获取菜单项文本（第二个 span 元素）
            const spans = this.querySelectorAll('span');
            const menuText = spans[1].textContent;

            // 根据菜单项导航到对应页面
            switch(menuText) {
                case '会话中心':
                    window.location.href = '/pages/session-center.html';
                    break;
                case '设备管理':
                    window.location.href = '/pages/device-management.html';
                    break;
                case '会话管理':
                    window.location.href = '/pages/session-management.html';
                    break;
                case '协议管理':
                    window.location.href = '/pages/protocol-management.html';
                    break;
                case '自动化测试':
                    window.location.href = '/pages/automation-test.html';
                    break;
                case '系统设置':
                    // 切换二级菜单
                    toggleSubmenu(this);
                    return;
                case '参数设置':
                    window.location.href = '/pages/parameter-settings.html';
                    break;
                case '周期任务':
                    window.location.href = '/pages/scheduled-task.html';
                    break;
            }
        });
    });
}

// 切换二级菜单
function toggleSubmenu(header) {
    const li = header.parentElement;
    li.classList.toggle('active');
}

// 导航到子页面
function navigateTo(url) {
    console.log('Navigating to:', url);
    window.location.href = url;
}

// 自动调整输入框高度
function adjustInputHeight(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    }
}

// 检查输入框内容，启用/禁用发送按钮
function checkInput(inputId, buttonId, connectionStatus) {
    const input = document.getElementById(inputId);
    const sendButton = document.getElementById(buttonId);
    if (input && sendButton) {
        if (input.value.trim() && connectionStatus === 'connected') {
            sendButton.disabled = false;
            sendButton.classList.add('enabled');
        } else {
            sendButton.disabled = true;
            sendButton.classList.remove('enabled');
        }
    }
}

// 协议模板映射
const protocolTemplates = {
    heartbeat: {
        Superior: '{"type": "heartbeat", "timestamp": "{timestamp}", "from": "{sendCode}", "to": "{receiveCode}"}',
        Area: '{"type": "heartbeat", "timestamp": "{timestamp}", "areaId": "{areaId}"}',
        Edge: '{"type": "heartbeat", "timestamp": "{timestamp}", "edgeId": "{edgeId}"}',
        Robot: '{"type": "heartbeat", "timestamp": "{timestamp}", "robotId": "{robotId}"}',
        Drone: '{"type": "heartbeat", "timestamp": "{timestamp}", "droneId": "{droneId}"}',
        Algo: '{"type": "heartbeat", "timestamp": "{timestamp}", "algoId": "{algoId}"}'
    },
    status: {
        Superior: '{"type": "status", "timestamp": "{timestamp}", "from": "{sendCode}", "to": "{receiveCode}", "status": "online"}',
        Area: '{"type": "status", "timestamp": "{timestamp}", "areaId": "{areaId}", "status": "online"}',
        Edge: '{"type": "status", "timestamp": "{timestamp}", "edgeId": "{edgeId}", "status": "online"}',
        Robot: '{"type": "status", "timestamp": "{timestamp}", "robotId": "{robotId}", "status": "online"}',
        Drone: '{"type": "status", "timestamp": "{timestamp}", "droneId": "{droneId}", "status": "online"}',
        Algo: '{"type": "status", "timestamp": "{timestamp}", "algoId": "{algoId}", "status": "online"}'
    },
    control: {
        Superior: '{"type": "control", "timestamp": "{timestamp}", "from": "{sendCode}", "to": "{receiveCode}", "command": "{command}"}',
        Area: '{"type": "control", "timestamp": "{timestamp}", "areaId": "{areaId}", "command": "{command}"}',
        Edge: '{"type": "control", "timestamp": "{timestamp}", "edgeId": "{edgeId}", "command": "{command}"}',
        Robot: '{"type": "control", "timestamp": "{timestamp}", "robotId": "{robotId}", "command": "{command}"}',
        Drone: '{"type": "control", "timestamp": "{timestamp}", "droneId": "{droneId}", "command": "{command}"}',
        Algo: '{"type": "control", "timestamp": "{timestamp}", "algoId": "{algoId}", "command": "{command}"}'
    },
    data: {
        Superior: '{"type": "data", "timestamp": "{timestamp}", "from": "{sendCode}", "to": "{receiveCode}", "data": "{data}"}',
        Area: '{"type": "data", "timestamp": "{timestamp}", "areaId": "{areaId}", "data": "{data}"}',
        Edge: '{"type": "data", "timestamp": "{timestamp}", "edgeId": "{edgeId}", "data": "{data}"}',
        Robot: '{"type": "data", "timestamp": "{timestamp}", "robotId": "{robotId}", "data": "{data}"}',
        Drone: '{"type": "data", "timestamp": "{timestamp}", "droneId": "{droneId}", "data": "{data}"}',
        Algo: '{"type": "data", "timestamp": "{timestamp}", "algoId": "{algoId}", "data": "{data}"}'
    }
};

// 填充协议模板
function fillProtocolTemplate(protocolTemplateId, protocolTypeId, inputId, sendCodeId, receiveCodeId) {
    const protocolTemplate = document.getElementById(protocolTemplateId).value;
    const protocolType = document.getElementById(protocolTypeId).value;
    const input = document.getElementById(inputId);

    if (protocolTemplate && protocolType && protocolTemplates[protocolTemplate] && protocolTemplates[protocolTemplate][protocolType]) {
        let template = protocolTemplates[protocolTemplate][protocolType];
        const sendCode = document.getElementById(sendCodeId).value;
        const receiveCode = document.getElementById(receiveCodeId).value;
        const timestamp = new Date().toISOString();

        // 替换模板中的变量
        template = template.replace('{timestamp}', timestamp);
        template = template.replace('{sendCode}', sendCode);
        template = template.replace('{receiveCode}', receiveCode);
        template = template.replace('{areaId}', sendCode);
        template = template.replace('{edgeId}', sendCode);
        template = template.replace('{robotId}', sendCode);
        template = template.replace('{droneId}', sendCode);
        template = template.replace('{algoId}', sendCode);
        template = template.replace('{command}', 'test_command');
        template = template.replace('{data}', 'test_data');

        input.value = template;
        adjustInputHeight(inputId);
    }
}

// 初始化页面
function initPage() {
    // 设置导航
    setupNavigation();

    // 其他初始化操作
    console.log('Page initialized');
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initPage);

// 自定义弹窗函数
function showNotification(message, type = 'success') {
    // 创建弹窗容器
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    modal.style.zIndex = '1000';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';

    // 创建弹窗内容
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalContent.style.backgroundColor = type === 'error' ? '#7F1D1D' : (type === 'warning' ? '#78350F' : '#1E293B');
    modalContent.style.borderRadius = '8px';
    modalContent.style.padding = '24px';
    modalContent.style.width = '90%';
    modalContent.style.maxWidth = '400px';
    modalContent.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';

    // 创建消息文本
    const messageElement = document.createElement('div');
    messageElement.style.padding = '20px';
    messageElement.style.textAlign = 'center';
    messageElement.style.color = '#E2E8F0';
    messageElement.style.fontSize = '16px';
    messageElement.textContent = message;
    modalContent.appendChild(messageElement);

    // 创建确认按钮
    const button = document.createElement('button');
    button.className = 'btn btn-primary';
    button.style.display = 'block';
    button.style.margin = '0 auto';
    button.style.padding = '8px 24px';
    button.style.fontSize = '14px';
    button.textContent = '确认';
    button.onclick = function() {
        modal.remove();
    };
    modalContent.appendChild(button);

    // 添加到页面
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // 点击模态框外部关闭
    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.remove();
        }
    };
}
