/**
 * 画廊聊天机器人UI控制模块
 * 实现聊天按钮点击、窗口拖拽和最小化/关闭功能
 */

// DOM元素变量 - 将在DOM加载完成后初始化
let chatButton, chatWindow, chatHeader, chatMinimize, chatClose, chatIframe;

// 窗口拖拽相关变量
let isDragging = false;
let dragStartX, dragStartY;
let initialX, initialY;

/**
 * 监听窗口大小变化和动态调整UI位置
 */
function setupResizeObserver() {
    // 立即调整一次大小
    adjustIframeSize();
    adjustUIPositions();
    
    // 创建ResizeObserver实例监听聊天窗口变化
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
    
    // 添加浏览器窗口大小变化监听
    let resizeTimeout;
    window.addEventListener('resize', () => {
        // 使用防抖避免频繁调用
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            adjustUIPositions();
            // 如果聊天窗口是打开的，也调整其位置
            if (chatWindow.style.display === 'flex') {
                adjustChatWindowPosition();
            }
            console.log(`浏览器窗口大小已调整为: ${window.innerWidth}x${window.innerHeight}px`);
        }, 100);
    });
    
    console.log('窗口大小监听器已设置完成');
}

/**
 * 动态调整UI元素位置和大小
 */
function adjustUIPositions() {
    // 确保DOM元素已初始化
    if (!chatButton) {
        console.warn('聊天按钮元素未初始化，重新获取DOM元素');
        if (!initDOMElements()) {
            console.error('无法获取DOM元素，跳过UI位置调整');
            return;
        }
    }
    
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const chatLabel = document.getElementById('chat-label');
    const chatButtonSvg = chatButton.querySelector('svg');
    
    // 计算响应式尺寸和位置
    let buttonSize, iconSize, leftPosition, topOffset, labelTop, fontSize, padding;
    
    // 计算标题底部位置 - 标题位于top:10px, padding:15px*2, h2字体约25px
    const titleHeight = 100; // 标题总高度（110px基准位置）
    const titleBottom = 110; // 标题底部固定位置
    const marginBelowTitle = 10; // 标签与标题的间距
    
    // 标签高度（根据字体大小估算）
    let labelHeight;
    
    // 计算标题位置 - 标题居中，估算宽度
    const titleEstimatedWidth = Math.min(400, viewportWidth * 0.6); // 标题估算宽度
    const titleCenterX = viewportWidth / 2; // 标题中心位置
    const titleLeftEdge = titleCenterX - (titleEstimatedWidth / 2); // 标题左边界
    const titleRightEdge = titleCenterX + (titleEstimatedWidth / 2) + 20; // 标题右边界 + 安全边距
    
    if (viewportWidth < 480) {
        // 超小屏幕 - 固定位置120px和165px，向左移动65px
        buttonSize = Math.max(40, Math.min(50, viewportWidth * 0.1));
        iconSize = Math.max(18, buttonSize * 0.45);
        leftPosition = Math.max(10, titleLeftEdge - 65); // 向左移动65px，最小保持10px边距
        fontSize = Math.max(9, viewportWidth * 0.025);
        labelHeight = Math.max(25, fontSize + 10);
        labelTop = 120; // 固定位置120px
        topOffset = 165; // 固定位置165px
        padding = `${Math.max(2, fontSize * 0.3)}px ${Math.max(4, fontSize * 0.6)}px`;
    } else if (viewportWidth < 768) {
        // 小屏幕 - 固定位置120px和165px，向左移动65px
        buttonSize = Math.max(45, Math.min(55, viewportWidth * 0.08));
        iconSize = Math.max(20, buttonSize * 0.45);
        leftPosition = Math.max(15, titleLeftEdge - 65); // 向左移动65px，最小保持15px边距
        fontSize = Math.max(10, viewportWidth * 0.02);
        labelHeight = Math.max(28, fontSize + 12);
        labelTop = 120; // 固定位置120px
        topOffset = 165; // 固定位置165px
        padding = `${Math.max(3, fontSize * 0.4)}px ${Math.max(6, fontSize * 0.8)}px`;
    } else if (viewportWidth < 1200) {
        // 中等屏幕 - 固定位置120px和165px，向左移动65px
        buttonSize = Math.max(50, Math.min(65, viewportWidth * 0.05));
        iconSize = Math.max(22, buttonSize * 0.45);
        leftPosition = Math.max(20, titleLeftEdge - 65); // 向左移动65px，最小保持20px边距
        fontSize = Math.max(11, viewportWidth * 0.015);
        labelHeight = Math.max(30, fontSize + 14);
        labelTop = 120; // 固定位置120px
        topOffset = 165; // 固定位置165px
        padding = `${Math.max(4, fontSize * 0.5)}px ${Math.max(8, fontSize * 1)}px`;
    } else {
        // 大屏幕 - 固定位置120px和165px，向左移动65px
        buttonSize = Math.max(55, Math.min(70, 55 + (viewportWidth - 1200) * 0.01));
        iconSize = Math.max(24, buttonSize * 0.45);
        leftPosition = Math.max(30, titleLeftEdge - 65); // 向左移动65px，最小保持30px边距
        fontSize = Math.max(12, Math.min(15, 12 + (viewportWidth - 1200) * 0.002));
        labelHeight = Math.max(32, fontSize + 16);
        labelTop = 120; // 固定位置120px
        topOffset = 165; // 固定位置165px
        padding = `${Math.max(5, fontSize * 0.5)}px ${Math.max(10, fontSize * 1)}px`;
    }
    
    // 应用按钮样式 - 使用left定位恢复原始位置风格
    chatButton.style.setProperty('width', `${buttonSize}px`, 'important');
    chatButton.style.setProperty('height', `${buttonSize}px`, 'important');
    chatButton.style.setProperty('top', `${topOffset}px`, 'important');
    chatButton.style.setProperty('left', `${leftPosition}px`, 'important');
    chatButton.style.removeProperty('right'); // 移除right定位
    
    // 应用图标样式
    if (chatButtonSvg) {
        chatButtonSvg.style.setProperty('width', `${iconSize}px`, 'important');
        chatButtonSvg.style.setProperty('height', `${iconSize}px`, 'important');
    }
    
    // 应用标签样式 - 位于按钮正上方，左边距对齐
    if (chatLabel) {
        // 标签与按钮的左边距对齐
        const labelLeft = leftPosition;
        
        chatLabel.style.setProperty('top', `${labelTop}px`, 'important');
        chatLabel.style.setProperty('left', `${labelLeft}px`, 'important');
        chatLabel.style.removeProperty('right'); // 移除right定位
        chatLabel.style.setProperty('font-size', `${fontSize}px`, 'important');
        chatLabel.style.setProperty('padding', padding, 'important');
        chatLabel.style.setProperty('border-radius', `${Math.max(12, fontSize)}px`, 'important');
        chatLabel.style.setProperty('max-width', `${Math.max(150, viewportWidth * 0.25)}px`, 'important');
        
        // 在超小屏幕上隐藏标签
        chatLabel.style.setProperty('display', viewportWidth < 320 ? 'none' : 'block', 'important');
    }
    
    console.log(`UI位置已调整 - 窗口: ${viewportWidth}x${viewportHeight}, 标签: left:${leftPosition}px top:${labelTop}px, 按钮: left:${leftPosition}px top:${topOffset}px, 大小:${buttonSize}px`);
}

/**
 * 调整iframe大小以适应容器 - 响应式版本
 */
function adjustIframeSize() {
    if (chatIframe && chatWindow.style.display === 'flex') {
        // 使用flexbox布局，iframe会自动填充剩余空间
        // 移除固定高度设置，让CSS flexbox处理布局
        chatIframe.style.removeProperty('height');
        chatIframe.style.height = '100%';
        chatIframe.style.width = '100%';
        
        // 确保聊天内容区域正确伸展
        const chatContent = document.getElementById('chat-content');
        if (chatContent) {
            chatContent.style.flex = '1';
            chatContent.style.display = 'flex';
            chatContent.style.flexDirection = 'column';
        }
        
        console.log('iframe大小已调整为响应式布局');
    }
}

/**
 * 初始化DOM元素
 */
function initDOMElements() {
    chatButton = document.getElementById('chat-button');
    chatWindow = document.getElementById('chat-window');
    chatHeader = document.getElementById('chat-header');
    chatMinimize = document.getElementById('chat-minimize');
    chatClose = document.getElementById('chat-close');
    chatIframe = document.getElementById('chat-iframe');
    
    // 检查关键元素是否存在
    if (!chatButton) {
        console.error('聊天按钮元素未找到');
        return false;
    }
    if (!chatWindow) {
        console.error('聊天窗口元素未找到');
        return false;
    }
    
    console.log('DOM元素初始化成功');
    return true;
}

/**
 * 初始化聊天UI
 */
function initChatUI() {
    // 首先初始化DOM元素
    if (!initDOMElements()) {
        console.error('DOM元素初始化失败，无法启动聊天UI');
        return;
    }
    
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
    
    // 立即调整一次UI位置
    setTimeout(() => {
        adjustUIPositions();
    }, 100);
    
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
 * 打开聊天窗口 - 响应式版本
 */
function openChatWindow() {
    // 检查iframe src是否已设置
    if (!chatIframe.src || chatIframe.src === 'about:blank') {
        chatIframe.src = '/chatbot';
    }
    
    // 调整UI位置确保窗口在正确位置
    adjustUIPositions();
    adjustChatWindowPosition();
    
    // 显示窗口
    chatWindow.style.display = 'flex';
    
    // 确保iframe正确填充内容区域
    chatIframe.style.width = '100%';
    chatIframe.style.height = '100%';
    
    // 添加响应式动画效果
    chatWindow.style.opacity = '0';
    chatWindow.style.transform = 'scale(0.8)';
    chatWindow.style.transformOrigin = 'top left';
    
    // 延迟添加显示动画
    setTimeout(() => {
        chatWindow.style.opacity = '1';
        chatWindow.style.transform = 'scale(1)';
    }, 10);
    
    // 发送打开聊天窗口事件到iframe
    sendMessageToIframe({ type: 'open' });
}

/**
 * 动态调整聊天窗口位置和大小 - 基于按钮位置
 */
function adjustChatWindowPosition() {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // 获取按钮的当前位置和大小
    const buttonRect = chatButton.getBoundingClientRect();
    const buttonLeft = parseFloat(chatButton.style.left) || buttonRect.left;
    const buttonTop = parseFloat(chatButton.style.top) || buttonRect.top;
    const buttonSize = parseFloat(chatButton.style.width) || 60;
    
    // 清除可能存在的其他定位属性
    chatWindow.style.removeProperty('right');
    chatWindow.style.removeProperty('bottom');
    
    // 计算窗口尺寸和位置 - 基于按钮位置
    let windowWidth, windowHeight, leftPosition, topPosition;
    
    // 计算聊天窗口位置：按钮右下方
    const marginFromButton = 10; // 与按钮的间距
    
    if (viewportWidth < 480) {
        // 超小屏幕 - 几乎全屏，但避免覆盖按钮
        const margin = Math.max(5, viewportWidth * 0.02);
        windowWidth = viewportWidth - (margin * 2);
        windowHeight = viewportHeight - buttonTop - buttonSize - marginFromButton - 20;
        leftPosition = margin;
        topPosition = buttonTop + buttonSize + marginFromButton;
        
        // 确保高度足够
        if (windowHeight < 200) {
            windowHeight = Math.min(300, viewportHeight * 0.6);
            topPosition = Math.max(20, viewportHeight - windowHeight - 20);
        }
    } else if (viewportWidth < 768) {
        // 小屏幕 - 紧邻按钮右下方
        windowWidth = Math.max(280, Math.min(400, viewportWidth * 0.7));
        windowHeight = Math.max(200, Math.min(350, viewportHeight * 0.5));
        leftPosition = buttonLeft + buttonSize + marginFromButton;
        topPosition = buttonTop;
        
        // 防止窗口超出屏幕右边界
        if (leftPosition + windowWidth > viewportWidth - 10) {
            leftPosition = buttonLeft - windowWidth - marginFromButton;
        }
        // 防止窗口超出屏幕下边界
        if (topPosition + windowHeight > viewportHeight - 10) {
            topPosition = Math.max(10, viewportHeight - windowHeight - 10);
        }
    } else if (viewportWidth < 1200) {
        // 中等屏幕 - 按钮右下方，合适大小
        windowWidth = Math.max(320, Math.min(450, viewportWidth * 0.35));
        windowHeight = Math.max(240, Math.min(400, viewportHeight * 0.45));
        leftPosition = buttonLeft + buttonSize + marginFromButton;
        topPosition = buttonTop;
        
        // 边界检查
        if (leftPosition + windowWidth > viewportWidth - 20) {
            leftPosition = buttonLeft - windowWidth - marginFromButton;
        }
        if (topPosition + windowHeight > viewportHeight - 20) {
            topPosition = Math.max(20, viewportHeight - windowHeight - 20);
        }
    } else {
        // 大屏幕 - 按钮右下方，较大窗口
        windowWidth = Math.max(400, Math.min(550, viewportWidth * 0.3));
        windowHeight = Math.max(300, Math.min(500, viewportHeight * 0.4));
        leftPosition = buttonLeft + buttonSize + marginFromButton;
        topPosition = buttonTop;
        
        // 边界检查
        if (leftPosition + windowWidth > viewportWidth - 30) {
            leftPosition = buttonLeft - windowWidth - marginFromButton;
        }
        if (topPosition + windowHeight > viewportHeight - 30) {
            topPosition = Math.max(30, viewportHeight - windowHeight - 30);
        }
    }
    
    // 应用计算出的样式
    chatWindow.style.setProperty('left', `${leftPosition}px`, 'important');
    chatWindow.style.setProperty('top', `${topPosition}px`, 'important');
    chatWindow.style.setProperty('width', `${windowWidth}px`, 'important');
    chatWindow.style.setProperty('height', `${windowHeight}px`, 'important');
    
    console.log(`聊天窗口位置已调整 - 窗口: ${viewportWidth}x${viewportHeight}, 按钮位置: left:${buttonLeft}px top:${buttonTop}px, 聊天窗口: left:${leftPosition}px top:${topPosition}px ${windowWidth}x${windowHeight}`);
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
    if (!chatButton || !document.getElementById('chat-button')) {
        console.error('聊天按钮未找到，可能DOM尚未完全加载');
        // 尝试重新获取DOM元素并初始化
        setTimeout(() => {
            if (document.getElementById('chat-button')) {
                console.log('重试获取聊天按钮成功，初始化聊天UI');
                initChatUI();
            }
        }, 1000);
    } else {
        // DOM已准备好，立即调整UI位置
        console.log('DOM加载完成，立即调整UI位置');
        setTimeout(() => {
            adjustUIPositions();
        }, 100);
    }
});

// 添加CSS样式 - 响应式动画优化
const style = document.createElement('style');
style.textContent = `
    #chat-window {
        opacity: 0;
        transform: scale(0.8);
        transform-origin: top left;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    
    #chat-window.dragging {
        transition: none;
        user-select: none;
    }
    
    /* 确保在所有屏幕尺寸下动画都流畅 */
    @media (prefers-reduced-motion: reduce) {
        #chat-window {
            transition: none;
        }
        
        #chat-button, #chat-label {
            transition: none;
        }
    }
`;
document.head.appendChild(style);

// 导出函数，供其他模块使用
export {
    openChatWindow,
    minimizeChatWindow,
    closeChatWindow
}; 