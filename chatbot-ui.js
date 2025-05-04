/**
 * 画廊聊天机器人UI控制模块
 * 实现聊天按钮点击、窗口拖拽和最小化/关闭功能
 */

// 获取DOM元素
const chatButton = document.getElementById('chat-button');
const chatWindow = document.getElementById('chat-window');
const chatHeader = document.getElementById('chat-header');
const chatMinimize = document.getElementById('chat-minimize');
const chatClose = document.getElementById('chat-close');
const chatIframe = document.getElementById('chat-iframe');

// 窗口拖拽相关变量
let isDragging = false;
let dragStartX, dragStartY;
let initialX, initialY;

/**
 * 监听窗口大小变化
 */
function setupResizeObserver() {
    // 立即调整一次大小
    adjustIframeSize();
    
    // 创建ResizeObserver实例
    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            // 调整iframe大小
            adjustIframeSize();
            
            // 记录大小变化
            console.log(`聊天窗口大小已调整为: ${entry.contentRect.width}x${entry.contentRect.height}px`);
        }
    });
    
    // 监听聊天窗口的大小变化
    resizeObserver.observe(chatWindow);
}

/**
 * 调整iframe大小以适应容器
 */
function adjustIframeSize() {
    if (chatIframe && chatWindow.style.display === 'flex') {
        const headerHeight = document.getElementById('chat-header').offsetHeight;
        const containerHeight = chatWindow.offsetHeight;
        
        chatIframe.style.width = '100%';
        chatIframe.style.height = `${containerHeight - headerHeight}px`;
    }
}

/**
 * 初始化聊天UI
 */
function initChatUI() {
    // 添加事件监听器
    chatButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleChatWindow(e);
    });
    chatMinimize.addEventListener('click', minimizeChatWindow);
    chatClose.addEventListener('click', closeChatWindow);
    
    // 窗口拖拽事件
    chatHeader.addEventListener('mousedown', startDragging);
    document.addEventListener('mousemove', dragWindow);
    document.addEventListener('mouseup', stopDragging);
    
    // 键盘快捷键
    document.addEventListener('keydown', handleKeyDown);
    
    // 设置窗口大小调整监听
    setupResizeObserver();
    
    console.log('聊天UI初始化完成');
}

/**
 * 打开/关闭聊天窗口
 */
function toggleChatWindow(event) {
    // 防止事件冒泡
    if (event) {
        event.stopPropagation();
    }
    
    if (chatWindow.style.display === 'flex') {
        minimizeChatWindow();
    } else {
        openChatWindow();
    }
}

/**
 * 打开聊天窗口
 */
function openChatWindow() {
    // 检查iframe src是否已设置
    if (!chatIframe.src || chatIframe.src === 'about:blank') {
        chatIframe.src = '/chatbot';
    }
    
    // 显示窗口
    chatWindow.style.display = 'flex';
    
    // 重置位置，确保窗口显示在正确位置
    chatWindow.style.top = '90px';
    chatWindow.style.left = '580px';
    chatWindow.style.bottom = 'auto';
    chatWindow.style.right = 'auto';
    chatWindow.style.transform = 'none';
    chatWindow.style.width = '450px';
    chatWindow.style.height = '240px';
    
    // 调整iframe大小
    const headerHeight = document.getElementById('chat-header').offsetHeight;
    chatIframe.style.width = '100%';
    chatIframe.style.height = `${240 - headerHeight}px`;
    
    // 添加动画效果
    chatWindow.style.opacity = '0';
    chatWindow.style.transform = 'scaleX(0.2)';
    chatWindow.style.transformOrigin = 'left center';
    
    // 延迟添加显示动画
    setTimeout(() => {
        chatWindow.style.opacity = '1';
        chatWindow.style.transform = 'scaleX(1)';
    }, 10);
    
    // 发送打开聊天窗口事件到iframe
    sendMessageToIframe({ type: 'open' });
}

/**
 * 最小化聊天窗口
 */
function minimizeChatWindow() {
    // 添加动画效果
    chatWindow.style.opacity = '0';
    chatWindow.style.transform = 'translateX(-20px)';
    
    // 延迟隐藏元素
    setTimeout(() => {
        chatWindow.style.display = 'none';
    }, 300);
}

/**
 * 关闭聊天窗口
 */
function closeChatWindow() {
    minimizeChatWindow();
    
    // 发送关闭聊天窗口事件到iframe
    sendMessageToIframe({ type: 'close' });
}

/**
 * 开始窗口拖拽
 */
function startDragging(e) {
    isDragging = true;
    
    // 记录鼠标起始位置
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    
    // 记录窗口初始位置
    const rect = chatWindow.getBoundingClientRect();
    initialX = rect.left;
    initialY = rect.top;
    
    // 添加拖拽中的样式
    chatWindow.classList.add('dragging');
    
    // 移除transform，以便直接使用left/top进行定位
    chatWindow.style.transform = 'none';
}

/**
 * 拖拽窗口
 */
function dragWindow(e) {
    if (!isDragging) return;
    
    // 计算移动距离
    const deltaX = e.clientX - dragStartX;
    const deltaY = e.clientY - dragStartY;
    
    // 计算新位置
    const newX = initialX + deltaX;
    const newY = initialY + deltaY;
    
    // 边界检查，确保窗口不会被拖出屏幕
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const chatWindowWidth = chatWindow.offsetWidth;
    const chatWindowHeight = chatWindow.offsetHeight;
    
    const minX = 0;
    const maxX = windowWidth - chatWindowWidth;
    const minY = 0;
    const maxY = windowHeight - chatWindowHeight;
    
    // 应用边界限制
    const boundedX = Math.max(minX, Math.min(maxX, newX));
    const boundedY = Math.max(minY, Math.min(maxY, newY));
    
    // 设置新位置
    chatWindow.style.left = `${boundedX}px`;
    chatWindow.style.top = `${boundedY}px`;
    chatWindow.style.right = 'auto';
    chatWindow.style.bottom = 'auto';
}

/**
 * 停止窗口拖拽
 */
function stopDragging() {
    if (isDragging) {
        isDragging = false;
        chatWindow.classList.remove('dragging');
    }
}

/**
 * 键盘快捷键处理
 */
function handleKeyDown(e) {
    // ESC键关闭聊天窗口（如果已打开）
    if (e.key === 'Escape' && chatWindow.style.display === 'flex') {
        minimizeChatWindow();
    }
}

/**
 * 向iframe发送消息
 */
function sendMessageToIframe(message) {
    try {
        if (chatIframe.contentWindow) {
            chatIframe.contentWindow.postMessage(message, '*');
        }
    } catch (error) {
        console.error('向iframe发送消息失败:', error);
    }
}

/**
 * 从iframe接收消息
 */
function receiveMessageFromIframe(event) {
    try {
        const message = event.data;
        
        // 处理从chatbot iframe接收的消息
        if (message && message.source === 'chatbot') {
            console.log('从Chatbot接收消息:', message);
            
            // 这里可以添加更多的消息处理逻辑
            if (message.action === 'resize') {
                // 调整窗口大小
                if (message.height) {
                    chatWindow.style.height = `${message.height}px`;
                }
            }
        }
    } catch (error) {
        console.error('处理iframe消息失败:', error);
    }
}

// 注册iframe消息监听器
window.addEventListener('message', receiveMessageFromIframe);

// 在DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', initChatUI);

// 在window加载完成后再检查一次初始化
window.addEventListener('load', () => {
    if (!document.getElementById('chat-button')) {
        console.error('聊天按钮未找到，可能DOM尚未完全加载');
        // 尝试重新获取DOM元素并初始化
        setTimeout(() => {
            const chatButtonRetry = document.getElementById('chat-button');
            if (chatButtonRetry) {
                console.log('重试获取聊天按钮成功，初始化聊天UI');
                initChatUI();
            }
        }, 1000);
    }
});

// 添加CSS样式
const style = document.createElement('style');
style.textContent = `
    #chat-window {
        opacity: 0;
        transform: scaleX(0.2);
        transform-origin: left center;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    
    #chat-window.dragging {
        transition: none;
        user-select: none;
    }
`;
document.head.appendChild(style);

// 导出函数，供其他模块使用
export {
    openChatWindow,
    minimizeChatWindow,
    closeChatWindow
}; 