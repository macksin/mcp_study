// 🚀 MCP Research Assistant - JavaScript Frontend 🚀

class MCPChatInterface {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.soundEnabled = true;
        this.messageQueue = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.updateTimestamp();
        this.connectWebSocket();
        
        console.log('🤖 MCP Chat Interface initialized');
    }
    
    initializeElements() {
        // Get DOM elements
        this.connectionStatus = document.getElementById('connection-status');
        this.modelInfo = document.getElementById('model-info');
        this.toolsCount = document.getElementById('tools-count');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-message');
        this.clearButton = document.getElementById('clear-chat');
        this.soundButton = document.getElementById('toggle-sound');
        this.charCount = document.getElementById('char-count');
        this.lastUpdated = document.getElementById('last-updated');
        this.tokenCount = document.getElementById('token-count');
        
        // Tool progress tracking
        this.toolProgressDiv = null;
    }
    
    setupEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key (Shift+Enter for new line)
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Character counter
        this.chatInput.addEventListener('input', () => {
            const length = this.chatInput.value.length;
            this.charCount.textContent = length;
            
            // Color coding for character limit
            if (length > 1800) {
                this.charCount.style.color = '#ff6666';
            } else if (length > 1500) {
                this.charCount.style.color = '#ffff00';
            } else {
                this.charCount.style.color = '#00ff41';
            }
        });
        
        // Clear chat history
        this.clearButton.addEventListener('click', () => this.clearChat());
        
        // Toggle sound
        this.soundButton.addEventListener('click', () => this.toggleSound());
        
        // Auto-focus on input
        this.chatInput.focus();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.updateConnectionStatus('CONNECTING...', '#ffff00');
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus('CONNECTED', '#00ff41');
                this.playSound('connect');
                
                // Send queued messages
                this.processMessageQueue();
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.socket.onclose = () => {
                console.log('❌ WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus('DISCONNECTED', '#ff6666');
                this.playSound('disconnect');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('ERROR', '#ff6666');
                this.addMessage('error', 'Connection error. Retrying...');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus('FAILED', '#ff6666');
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'status':
                this.handleStatusMessage(data);
                break;
            case 'user_message':
                this.addMessage('user', data.message);
                break;
            case 'assistant_message':
                // Remove tool progress indicator when response arrives
                if (this.toolProgressDiv) {
                    this.toolProgressDiv.remove();
                    this.toolProgressDiv = null;
                }
                
                // Combine message and token info if present
                let fullMessage = data.message;
                if (data.tokens) {
                    fullMessage += '\n\n' + data.tokens;
                }
                
                this.addMessage('assistant', fullMessage);
                this.playSound('message');
                break;
            case 'tool_progress':
                this.showToolProgress(data.message);
                this.playSound('send');
                break;
            case 'error':
                this.addMessage('error', data.message);
                this.playSound('error');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    handleStatusMessage(data) {
        if (data.provider && data.model) {
            this.modelInfo.textContent = `${data.provider} - ${data.model}`;
            
            // Add caching indicator
            if (data.caching) {
                this.modelInfo.textContent += ' 🚀';
                this.modelInfo.title = 'Prompt caching enabled for cost savings!';
            }
        }
        
        if (data.tools !== undefined) {
            this.toolsCount.textContent = data.tools;
        }
        
        if (data.message) {
            this.addMessage('system', data.message);
        }
    }
    
    sendMessage() {
        if (!this.isConnected) {
            this.addMessage('error', 'Not connected to server. Please wait for reconnection.');
            return;
        }
        
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Disable send button temporarily
        this.sendButton.disabled = true;
        this.sendButton.textContent = '📡 SENDING...';
        
        // Send message via WebSocket
        this.socket.send(JSON.stringify({
            type: 'chat',
            message: message
        }));
        
        // Clear input
        this.chatInput.value = '';
        this.charCount.textContent = '0';
        
        // Show loading message
        this.addMessage('assistant', 'Processing your request<span class="loading"></span>');
        
        // Re-enable send button after a short delay
        setTimeout(() => {
            this.sendButton.disabled = false;
            this.sendButton.textContent = '📡 TRANSMIT';
        }, 1000);
        
        this.playSound('send');
    }
    
    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        // Remove loading message if this is an assistant response
        if (type === 'assistant') {
            const loadingMessages = this.chatMessages.querySelectorAll('.assistant-message .loading');
            loadingMessages.forEach(msg => msg.closest('.message').remove());
        }
        
        const messageHeader = this.getMessageHeader(type);
        
        const messageContent = this.formatMessage(content);
        
        // Debug logging (can be removed in production)
        if (type === 'assistant' && content.length > 500) {
            console.log('📝 Long assistant message:', content.length + ' characters');
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">${messageHeader}</div>
            <div class="message-content">${messageContent}</div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        // Ensure the content div has proper styling
        const contentDiv = messageDiv.querySelector('.message-content');
        contentDiv.style.maxHeight = 'none';
        contentDiv.style.height = 'auto';
        contentDiv.style.overflow = 'visible';
        contentDiv.style.wordWrap = 'break-word';
        contentDiv.style.whiteSpace = 'pre-wrap';
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Add typing animation for new messages
        if (type === 'assistant') {
            messageDiv.querySelector('.message-content').classList.add('typing');
        }
    }
    
    showToolProgress(toolMessage) {
        // Remove existing tool progress if any
        if (this.toolProgressDiv) {
            this.toolProgressDiv.remove();
        }
        
        // Create new tool progress indicator
        this.toolProgressDiv = document.createElement('div');
        this.toolProgressDiv.className = 'tool-progress';
        
        const timestamp = new Date().toLocaleTimeString();
        
        this.toolProgressDiv.innerHTML = `
            <div class="message-header">🔧 TOOL EXECUTION</div>
            <div class="tool-progress-content">
                <div class="tool-spinner">⚙️</div>
                <div class="tool-message">${this.formatToolProgress(toolMessage)}</div>
                <div class="tool-dots"><span class="loading"></span></div>
            </div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        this.chatMessages.appendChild(this.toolProgressDiv);
        this.scrollToBottom();
    }
    
    formatToolProgress(message) {
        // Extract tool name and args from message
        const toolMatch = message.match(/Calling tool (\w+) with args (.+)/);
        if (toolMatch) {
            const [, toolName, args] = toolMatch;
            return `<strong style="color: #ffff00;">${toolName}</strong><br><span style="color: #888; font-size: 0.9em;">${args}</span>`;
        }
        return message;
    }
    
    getMessageHeader(type) {
        const headers = {
            'user': '👤 USER',
            'assistant': '🤖 ASSISTANT',
            'system': '🖥️ SYSTEM',
            'error': '❌ ERROR'
        };
        return headers[type] || '📝 MESSAGE';
    }
    
    formatMessage(content) {
        // Convert newlines to <br> tags
        let formatted = content.replace(/\n/g, '<br>');
        
        // Make URLs clickable
        formatted = formatted.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" style="color: #00aaff;">$1</a>'
        );
        
        // Highlight tool calls
        formatted = formatted.replace(
            /Calling tool (\w+) with args/g,
            '🔧 <strong style="color: #ffff00;">Calling tool $1</strong> with args'
        );
        
        // Highlight file operations
        formatted = formatted.replace(
            /(Created|Saved|Reading|Writing|Fetching)/g,
            '📁 <strong style="color: #00ff41;">$1</strong>'
        );
        
        // Style token information nicely
        formatted = formatted.replace(
            /🔢 Tokens: (\d+)\/(\d+) \(Total: (\d+)\/(\d+)\)/g,
            '<div style="margin-top: 15px; padding: 8px; background: rgba(255, 255, 0, 0.1); border: 1px solid #ffff00; border-radius: 5px; font-size: 0.9em; text-align: center;"><strong style="color: #ffff00;">🔢 Tokens:</strong> <span style="color: #00ff41;">$1</span>/<span style="color: #00aaff;">$2</span> | <strong style="color: #ffff00;">Total:</strong> <span style="color: #00ff41;">$3</span>/<span style="color: #00aaff;">$4</span></div>'
        );
        
        return formatted;
    }
    
    clearChat() {
        if (!this.isConnected) {
            this.addMessage('error', 'Cannot clear chat while disconnected.');
            return;
        }
        
        // Send clear command to server
        this.socket.send(JSON.stringify({
            type: 'clear'
        }));
        
        // Clear local chat display
        const messages = this.chatMessages.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(msg => msg.remove());
        
        this.playSound('clear');
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        this.soundButton.textContent = this.soundEnabled ? '🔊 SOUND ON' : '🔇 SOUND OFF';
        this.playSound('toggle');
    }
    
    playSound(type) {
        if (!this.soundEnabled) return;
        
        // Create audio context for retro beeps
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return;
        const audioContext = new AudioContextClass();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequencies for different sounds
        const frequencies = {
            'connect': 800,
            'disconnect': 400,
            'message': 600,
            'send': 1000,
            'error': 300,
            'clear': 750,
            'toggle': 500
        };
        
        oscillator.frequency.setValueAtTime(frequencies[type] || 500, audioContext.currentTime);
        oscillator.type = 'square';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    }
    
    updateConnectionStatus(status, color) {
        this.connectionStatus.textContent = status;
        this.connectionStatus.style.color = color;
    }
    
    updateTokenCount(inputTokens, outputTokens) {
        this.tokenCount.textContent = `${inputTokens}/${outputTokens}`;
        this.tokenCount.title = `Input: ${inputTokens} tokens, Output: ${outputTokens} tokens`;
    }
    
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.socket.send(JSON.stringify(message));
        }
    }
    
    updateTimestamp() {
        const now = new Date();
        const timestamp = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        this.lastUpdated.textContent = timestamp;
        
        // Update every minute
        setTimeout(() => this.updateTimestamp(), 60000);
    }
}

// Initialize the chat interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.mcpChat = new MCPChatInterface();
});

// Add some retro console logging
console.log(`
🤖════════════════════════════════════════🤖
    MCP RESEARCH ASSISTANT v2.0
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    🔬 Multi-server MCP Integration
    📡 Real-time WebSocket Communication  
    🎨 Retro Web 1.0 Styling
    💾 Built with Pure HTML/CSS/JS
🤖════════════════════════════════════════🤖
`);

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.code);
    if (konamiCode.length > konamiSequence.length) {
        konamiCode.shift();
    }
    
    if (JSON.stringify(konamiCode) === JSON.stringify(konamiSequence)) {
        document.body.style.filter = 'hue-rotate(180deg)';
        setTimeout(() => {
            document.body.style.filter = '';
        }, 3000);
        console.log('🎮 KONAMI CODE ACTIVATED! 🎮');
    }
});