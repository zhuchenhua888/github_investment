// 全局应用JavaScript文件
document.addEventListener('DOMContentLoaded', function() {
    // 初始化应用
    console.log('韭菜助手Web应用已启动');
    
    // 设置活动导航链接
    setActiveNav();
});

function setActiveNav() {
    // 获取当前页面路径并设置相应的导航为活跃状态
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// 通用API请求函数
async function apiRequest(url, options = {}) {
    const startTime = performance.now();
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const endTime = performance.now();
        console.log(`[API Request] ${url} took ${(endTime - startTime).toFixed(2)}ms`);
        return data;
    } catch (error) {
        const endTime = performance.now();
        console.error(`[API Request Error] ${url} failed after ${(endTime - startTime).toFixed(2)}ms:`, error);
        throw error;
    }
}

// 显示加载状态
function showLoading(elementId = 'loading') {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

// 隐藏加载状态
function hideLoading(elementId = 'loading') {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// 显示错误信息
function showError(message, elementId = 'error') {
    const element = document.getElementById(elementId);
    const messageElement = document.getElementById('error-message');
    
    if (messageElement) {
        messageElement.textContent = message;
    }
    
    if (element) {
        element.style.display = 'block';
    }
}

// 隐藏错误信息
function hideError(elementId = 'error') {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// 格式化日期
function formatDate(date) {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return `${year}年${month}月${day}日 ${hours}:${minutes}:${seconds}`;
}