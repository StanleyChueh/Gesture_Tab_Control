let ws = new WebSocket('ws://localhost:8000');
let keepAliveInterval;

function switchTab(tabId, retries = 5) {
    if (retries === 0) {
        console.error('Failed to switch tab after multiple attempts.');
        return;
    }

    chrome.tabs.update(tabId, { active: true }, function(tab) {
        if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError);
            setTimeout(() => switchTab(tabId, retries - 1), 100); // 等待100毫秒后重试
        }
    });
}

ws.onmessage = function(event) {
    console.log(`Received message: ${event.data}`);
    if (event.data === 'next_tab') {
        chrome.tabs.query({currentWindow: true}, function(tabs) {
            if (tabs.length === 0) {
                console.error('No tabs found.');
                return;
            }
            chrome.tabs.query({currentWindow: true, active: true}, function(activeTabs) {
                if (activeTabs.length === 0) {
                    console.error('No active tab found.');
                    return;
                }
                let activeTab = activeTabs[0];
                let activeIndex = tabs.findIndex(tab => tab.id === activeTab.id);
                let nextTabIndex = (activeIndex + 1) % tabs.length;
                let nextTab = tabs[nextTabIndex];
                if (nextTab && nextTab.id) {
                    switchTab(nextTab.id);
                } else {
                    console.error('Next tab not found or missing tab ID.');
                }
            });
        });
    } else if (event.data === 'previous_tab') {
        chrome.tabs.query({currentWindow: true}, function(tabs) {
            if (tabs.length === 0) {
                console.error('No tabs found.');
                return;
            }
            chrome.tabs.query({currentWindow: true, active: true}, function(activeTabs) {
                if (activeTabs.length === 0) {
                    console.error('No active tab found.');
                    return;
                }
                let activeTab = activeTabs[0];
                let activeIndex = tabs.findIndex(tab => tab.id === activeTab.id);
                let previousTabIndex = (activeIndex - 1 + tabs.length) % tabs.length;
                let previousTab = tabs[previousTabIndex];
                if (previousTab && previousTab.id) {
                    switchTab(previousTab.id);
                } else {
                    console.error('Previous tab not found or missing tab ID.');
                }
            });
        });
    }
};

ws.onopen = function() {
    console.log('WebSocket connection opened');
    keepAliveInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send('keep-alive');
        }
    }, 30000); // 每30秒发送一次心跳消息
};

ws.onclose = function() {
    console.log('WebSocket connection closed');
    clearInterval(keepAliveInterval);
};

ws.onerror = function(error) {
    console.log(`WebSocket error: ${error}`);
};
