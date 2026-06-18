// Custom Role Selection for Login (Playwright friendly)
document.addEventListener('DOMContentLoaded', () => {
    const roleBtns = document.querySelectorAll('.role-btn');
    const roleInput = document.getElementById('role-input');

    if (roleBtns.length > 0) {
        roleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                roleBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                if (roleInput) {
                    roleInput.value = btn.dataset.role;
                }
            });
        });
    }

    // Initialize tooltips/other UI elements if needed
});

// Modal Logic
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// API Helpers
async function callAI(endpoint, data, btnElement) {
    const originalText = btnElement ? btnElement.textContent : '';
    if (btnElement) {
        btnElement.disabled = true;
        btnElement.innerHTML = `Generating <span class="loading-dots"></span>`;
    }

    try {
        const response = await fetch(`/api/ai/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.textContent = originalText;
        }
        return result;
    } catch (error) {
        console.error('API Error:', error);
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.textContent = originalText;
        }
        return { success: false, error: error.message };
    }
}

// Chatbot Logic
let chatHistory = [];

async function sendMessage(mode = 'doubt_solver') {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    appendMessage('user', msg);
    input.value = '';

    chatHistory.push({ role: 'user', content: msg });

    const responseMsgId = appendMessage('ai', 'Thinking...');

    const result = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: chatHistory, mode: mode })
    }).then(res => res.json());

    updateMessage(responseMsgId, result.success ? result.reply : 'Error: ' + result.error);

    if (result.success) {
        chatHistory.push({ role: 'assistant', content: result.reply });
    } else {
        chatHistory.pop(); // Remove the failed user message
    }
}

function appendMessage(sender, text) {
    const messagesDiv = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    const id = 'msg-' + Date.now();
    msgDiv.id = id;

    // STRICTLY using textContent to prevent DOM XSS
    msgDiv.textContent = text;

    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return id;
}

function updateMessage(id, text) {
    const msgDiv = document.getElementById(id);
    if (msgDiv) {
        msgDiv.textContent = text;
    }
}
