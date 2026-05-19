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

// --- STUDENT AI LOGIC ---
let chatHistory = [];

function appendChatMessage(role, content) {
    const chatWindow = document.getElementById('chat-window');
    if(!chatWindow) return;

    const msgDiv = document.createElement('div');
    msgDiv.classList.add('chat-message', `${role}-message`);

    if(role === 'user') {
        msgDiv.style.background = '#e2e8f0';
        msgDiv.style.color = '#1e293b';
        msgDiv.style.padding = '10px 15px';
        msgDiv.style.borderRadius = '15px 15px 0 15px';
        msgDiv.style.maxWidth = '80%';
        msgDiv.style.marginBottom = '15px';
        msgDiv.style.alignSelf = 'flex-end';
        msgDiv.style.marginLeft = 'auto';
        msgDiv.style.display = 'block';
        msgDiv.style.width = 'fit-content';
    } else {
        msgDiv.style.background = 'var(--primary)';
        msgDiv.style.color = 'white';
        msgDiv.style.padding = '10px 15px';
        msgDiv.style.borderRadius = '15px 15px 15px 0';
        msgDiv.style.maxWidth = '80%';
        msgDiv.style.marginBottom = '15px';
        msgDiv.style.alignSelf = 'flex-start';
        msgDiv.style.display = 'block';
        msgDiv.style.width = 'fit-content';
    }

    msgDiv.innerText = content;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

window.sendChatMessage = async function() {
    const input = document.getElementById('chat-input');
    if(!input) return;
    const message = input.value.trim();
    if(!message) return;

    appendChatMessage('user', message);
    input.value = '';

    const chatWindow = document.getElementById('chat-window');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'chat-loading';
    loadingDiv.innerText = "Thinking...";
    loadingDiv.style.color = '#64748b';
    loadingDiv.style.fontStyle = 'italic';
    loadingDiv.style.marginBottom = '10px';
    chatWindow.appendChild(loadingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const res = await fetch('/api/ai/chatbot', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: message, history: chatHistory })
        });
        const data = await res.json();
        chatWindow.removeChild(loadingDiv);

        if(data.success) {
            appendChatMessage('ai', data.answer);
            chatHistory.push({"role": "user", "content": message});
            chatHistory.push({"role": "assistant", "content": data.answer});
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch(err) {
        if(document.getElementById('chat-loading')) chatWindow.removeChild(loadingDiv);
        showToast('Connection error.', 'error');
    }
};

window.solveDoubt = async function() {
    const input = document.getElementById('doubt-input');
    const resultDiv = document.getElementById('doubt-result');
    if(!input || !resultDiv) return;

    const question = input.value.trim();
    if(!question) return;

    resultDiv.style.display = 'block';
    resultDiv.innerText = 'Thinking...';

    try {
        const res = await fetch('/api/ai/doubt_solver', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ question: question })
        });
        const data = await res.json();

        if(data.success) {
            resultDiv.innerText = data.answer;
        } else {
            resultDiv.innerText = 'Error: ' + data.error;
            showToast(data.error, 'error');
        }
    } catch(err) {
        resultDiv.innerText = 'Connection error.';
        showToast('Connection error.', 'error');
    }
};

// --- TEACHER AI LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    const btnAttendance = document.getElementById('btn-attendance-insight');
    if(btnAttendance) {
        btnAttendance.addEventListener('click', async () => {
            const resultDiv = document.getElementById('attendance-insight-result');
            resultDiv.innerText = "Analyzing attendance data... This may take a moment.";
            try {
                const res = await fetch('/api/ai/attendance_insight', { method: 'POST' });
                const data = await res.json();
                if(data.success) {
                    resultDiv.innerText = data.insight;
                } else {
                    resultDiv.innerText = "Error: " + data.error;
                    showToast(data.error, 'error');
                }
            } catch(err) {
                resultDiv.innerText = "Connection error.";
                showToast("Connection error.", 'error');
            }
        });
    }

    const btnVideo = document.getElementById('btn-video-summary');
    if(btnVideo) {
        btnVideo.addEventListener('click', async () => {
            const topicInput = document.getElementById('video-topic-input');
            const resultDiv = document.getElementById('video-summary-result');
            const topic = topicInput.value.trim();
            if(!topic) {
                showToast("Please enter a topic", "warning");
                return;
            }
            resultDiv.innerText = "Generating summary...";
            try {
                const res = await fetch('/api/ai/video_summary', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({topic: topic})
                });
                const data = await res.json();
                if(data.success) {
                    resultDiv.innerText = data.summary;
                } else {
                    resultDiv.innerText = "Error: " + data.error;
                    showToast(data.error, 'error');
                }
            } catch(err) {
                resultDiv.innerText = "Connection error.";
                showToast("Connection error.", 'error');
            }
        });
    }

    const btnQuiz = document.getElementById('btn-quiz-generator');
    if(btnQuiz) {
        btnQuiz.addEventListener('click', async () => {
            const subInput = document.getElementById('quiz-subject-input');
            const topInput = document.getElementById('quiz-topic-input');
            const resultDiv = document.getElementById('quiz-generator-result');
            const subject = subInput.value.trim();
            const topic = topInput.value.trim();
            if(!subject || !topic) {
                showToast("Please enter subject and topic", "warning");
                return;
            }
            resultDiv.innerText = "Generating 5 MCQs...";
            try {
                const res = await fetch('/api/ai/quiz_generator', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({subject: subject, topic: topic})
                });
                const data = await res.json();
                if(data.success) {
                    resultDiv.innerText = data.quiz;
                } else {
                    resultDiv.innerText = "Error: " + data.error;
                    showToast(data.error, 'error');
                }
            } catch(err) {
                resultDiv.innerText = "Connection error.";
                showToast("Connection error.", 'error');
            }
        });
    }
});
