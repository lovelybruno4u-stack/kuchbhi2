// Custom role selector logic for login page
document.addEventListener('DOMContentLoaded', () => {
    const roleOptions = document.querySelectorAll('.role-option');
    const roleInput = document.getElementById('role-input');

    if (roleOptions.length > 0 && roleInput) {
        roleOptions.forEach(option => {
            option.addEventListener('click', () => {
                // Remove selected class from all
                roleOptions.forEach(opt => opt.classList.remove('selected'));
                // Add to clicked
                option.classList.add('selected');
                // Update hidden input
                roleInput.value = option.getAttribute('data-role');
            });
        });
    }

    // Initialize chat interface if on chatbot page
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        let chatHistory = [];
        const chatContainer = document.getElementById('chat-container');
        const chatInput = document.getElementById('chat-input');
        const loader = document.getElementById('chat-loader');

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message to UI
            appendMessage('user', message);
            chatInput.value = '';

            // Add to history
            chatHistory.push({ role: 'user', content: message });

            // Show loader
            loader.style.display = 'inline-block';

            try {
                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chat_history: chatHistory })
                });

                const data = await response.json();

                if (response.ok) {
                    appendMessage('ai', data.reply);
                    chatHistory.push({ role: 'assistant', content: data.reply });
                } else {
                    appendMessage('ai', 'Sorry, I encountered an error. Please try again.');
                }
            } catch (error) {
                appendMessage('ai', 'Connection error. Please check your internet.');
            } finally {
                loader.style.display = 'none';
            }
        });

        function appendMessage(sender, text) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-message ${sender}`;
            msgDiv.textContent = text;
            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    // Custom modal logic
    window.showModal = function(title, message) {
        let modal = document.getElementById('custom-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'custom-modal';
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.5); display: flex;
                align-items: center; justify-content: center; z-index: 1000;
            `;

            const content = document.createElement('div');
            content.className = 'card';
            content.style.cssText = `
                min-width: 300px; max-width: 500px; text-align: center;
                background: white; padding: 20px; border-radius: 12px;
            `;

            const titleEl = document.createElement('h3');
            titleEl.id = 'modal-title';
            titleEl.style.marginBottom = '15px';

            const msgEl = document.createElement('p');
            msgEl.id = 'modal-message';
            msgEl.style.marginBottom = '20px';

            const closeBtn = document.createElement('button');
            closeBtn.className = 'btn btn-primary';
            closeBtn.textContent = 'Close';
            closeBtn.onclick = () => modal.style.display = 'none';

            content.appendChild(titleEl);
            content.appendChild(msgEl);
            content.appendChild(closeBtn);
            modal.appendChild(content);
            document.body.appendChild(modal);
        }

        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-message').textContent = message;
        modal.style.display = 'flex';
    };
});
