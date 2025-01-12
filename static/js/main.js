// Textarea auto-resize
const textarea = document.getElementById('query-input');
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Handle Enter key
textarea.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function usePrompt(prompt) {
    textarea.value = prompt;
    textarea.focus();
    textarea.dispatchEvent(new Event('input'));
}

function createLoadingMessage() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-robot message-icon"></i>
            <div class="message-text loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return loadingDiv;
}

function addMessage(type, content) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const icon = type === 'user' ? 'fa-user' : 'fa-robot';
    messageDiv.innerHTML = `
        <div class="message-content">
            <i class="fas ${icon} message-icon"></i>
            <div class="message-text">
                <p>${content}</p>
            </div>
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');
    const query = input.value.trim();
    
    if (!query) return;
    
    // Disable input and button
    input.disabled = true;
    sendButton.disabled = true;
    
    // Add user message
    addMessage('user', query);
    
    // Add loading message
    const messagesDiv = document.getElementById('chat-messages');
    const loadingMessage = createLoadingMessage();
    messagesDiv.appendChild(loadingMessage);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        // Remove loading message
        messagesDiv.removeChild(loadingMessage);
        
        if (data.error) {
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } else {
            addMessage('assistant', data.answer);
        }
    } catch (error) {
        // Remove loading message
        messagesDiv.removeChild(loadingMessage);
        addMessage('assistant', 'Sorry, something went wrong. Please try again.');
        console.error('Error:', error);
    } finally {
        // Clear and reset input
        input.value = '';
        input.style.height = 'auto';
        input.disabled = false;
        sendButton.disabled = false;
        input.focus();
    }
}