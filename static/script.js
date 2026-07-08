document.addEventListener('DOMContentLoaded', () => {
    // Role Toggle Logic
    const roleBtns = document.querySelectorAll('.role-btn');
    const roleInput = document.getElementById('role-input');

    if (roleBtns.length > 0) {
        roleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                roleBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                if(roleInput) {
                    roleInput.value = e.target.getAttribute('data-role');
                }
            });
        });
    }

    // Sidebar Toggle for Mobile
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');

    if (hamburger && sidebar) {
        hamburger.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('active');
            document.body.classList.toggle('sidebar-open');
        });

        // Close sidebar if clicking outside on mobile overlay
        document.body.addEventListener('click', (e) => {
            if (document.body.classList.contains('sidebar-open') && !sidebar.contains(e.target)) {
                sidebar.classList.remove('active');
                document.body.classList.remove('sidebar-open');
            }
        });
    }

    // Modal Logic
    const openModalBtns = document.querySelectorAll('[data-modal-target]');
    const closeModalBtns = document.querySelectorAll('[data-close-button]');
    const overlay = document.getElementById('modal-overlay');

    openModalBtns.forEach(button => {
        button.addEventListener('click', () => {
            const modal = document.querySelector(button.dataset.modalTarget);
            openModal(modal);
        });
    });

    closeModalBtns.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal-overlay');
            closeModal(modal);
        });
    });

    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                const modals = document.querySelectorAll('.modal-overlay.active');
                modals.forEach(modal => closeModal(modal));
            }
        });
    }

    function openModal(modal) {
        if (modal == null) return;
        modal.classList.add('active');
        document.body.classList.add('modal-open');
    }

    function closeModal(modal) {
        if (modal == null) return;
        modal.classList.remove('active');
        document.body.classList.remove('modal-open');
    }

    // Chatbot Logic
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (chatForm && chatInput && chatMessages) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            appendMessage('user', message);
            chatInput.value = '';

            try {
                const response = await fetch('/api/chatbot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                if(!response.ok) throw new Error("Network response was not ok");

                const data = await response.json();
                appendMessage('ai', data.reply);
            } catch (error) {
                console.error("Chat error:", error);
                appendMessage('ai', "Sorry, I'm having trouble connecting right now.");
            }
        });
    }

    function appendMessage(sender, text) {
        if(!chatMessages) return;
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

function showLoading() {
    const loader = document.getElementById('global-loader');
    if(loader) loader.style.display = 'block';
}

function hideLoading() {
    const loader = document.getElementById('global-loader');
    if(loader) loader.style.display = 'none';
}

// CUSTOM DOM MODAL TO REPLACE ALERT()
function createModalDOM() {
    if (document.getElementById('customModalOverlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'customModalOverlay';
    overlay.className = 'custom-modal-overlay';

    const modal = document.createElement('div');
    modal.className = 'custom-modal';
    modal.id = 'customModalBox';

    const title = document.createElement('div');
    title.className = 'custom-modal-title';
    title.id = 'customModalTitle';
    title.textContent = 'Notification';

    const body = document.createElement('div');
    body.className = 'custom-modal-body';
    body.id = 'customModalBody';

    const btn = document.createElement('button');
    btn.className = 'custom-modal-btn';
    btn.textContent = 'OK';
    btn.onclick = closeCustomModal;

    modal.appendChild(title);
    modal.appendChild(body);
    modal.appendChild(btn);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
}

function showCustomModal(message, title='Notice') {
    createModalDOM();
    document.getElementById('customModalTitle').textContent = title;
    document.getElementById('customModalBody').textContent = message;

    const overlay = document.getElementById('customModalOverlay');
    const box = document.getElementById('customModalBox');

    overlay.style.display = 'flex';
    setTimeout(() => {
        box.classList.add('show');
    }, 10);
}

function closeCustomModal() {
    const overlay = document.getElementById('customModalOverlay');
    const box = document.getElementById('customModalBox');

    box.classList.remove('show');
    setTimeout(() => {
        overlay.style.display = 'none';
    }, 300);
}

// Override native alert (optional but good for catching old code)
window.alert = function(msg) {
    showCustomModal(msg);
};
