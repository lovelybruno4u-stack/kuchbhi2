// Custom Modal System (replaces alert)
function showModal(title, content) {
    let modalOverlay = document.getElementById('custom-modal');
    if (!modalOverlay) {
        modalOverlay = document.createElement('div');
        modalOverlay.id = 'custom-modal';
        modalOverlay.className = 'modal-overlay';

        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content glass';

        modalContent.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title" id="modal-title"></h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modal-body"></div>
            <div class="modal-footer" style="margin-top: 24px; text-align: right;">
                <button class="btn btn-primary" onclick="closeModal()">OK</button>
            </div>
        `;

        modalOverlay.appendChild(modalContent);
        document.body.appendChild(modalOverlay);
    }

    document.getElementById('modal-title').textContent = title;
    // Security: using textContent by default unless explicitly passing safe HTML
    if (typeof content === 'string') {
        document.getElementById('modal-body').textContent = content;
    } else {
        document.getElementById('modal-body').innerHTML = '';
        document.getElementById('modal-body').appendChild(content);
    }

    modalOverlay.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('custom-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Custom Fetch Wrapper with UI feedback
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        const data = await response.json();

        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login';
            return null;
        }

        if (!data.success) {
            showModal('Error', data.error || 'An unexpected error occurred.');
            return null;
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        showModal('Error', 'Failed to connect to the server.');
        return null;
    }
}

// Chatbot functionality
let chatHistory = [];

async function sendMessage(endpoint) {
    const inputEl = document.getElementById('chat-input');
    const messagesEl = document.getElementById('chat-messages');
    const loadingEl = document.getElementById('chat-loading');

    const message = inputEl.value.trim();
    if (!message) return;

    // Add User Message safely
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'message user';
    userMsgDiv.appendChild(document.createTextNode(message));
    messagesEl.appendChild(userMsgDiv);

    inputEl.value = '';
    loadingEl.style.display = 'block';
    messagesEl.scrollTop = messagesEl.scrollHeight;

    // API Call
    const data = await apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify({ message: message, history: chatHistory, question: message })
    });

    loadingEl.style.display = 'none';

    if (data) {
        // Add AI Message safely
        const aiMsgDiv = document.createElement('div');
        aiMsgDiv.className = 'message ai';
        aiMsgDiv.appendChild(document.createTextNode(data.answer));
        messagesEl.appendChild(aiMsgDiv);

        // Update history if it's the study chatbot
        if (endpoint.includes('/chat')) {
            chatHistory.push({ role: 'user', content: message });
            chatHistory.push({ role: 'assistant', content: data.answer });
        }
    }

    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Utility to render table rows safely
function createTableCell(text) {
    const td = document.createElement('td');
    td.appendChild(document.createTextNode(text || '-'));
    return td;
}
