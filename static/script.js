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


// ==========================================
// AI FEATURES FETCH LOGIC (ASWATHAMA CLASSES)
// ==========================================

// --- TEACHER AI TOOLS ---

function analyzeAttendance() {
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    btn.disabled = true;

    fetch('/api/ai/attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(res => res.json())
    .then(data => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (data.success) {
            const resDiv = document.getElementById('attendance-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = '<strong>Insights:</strong>\n' + data.analysis;
        } else {
            showToast(data.error || 'Failed to analyze attendance.', 'error');
        }
    })
    .catch(err => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('Network error occurred.', 'error');
    });
}

function generateVideoSummary() {
    const topic = document.getElementById('video-topic').value;
    if (!topic) return showToast('Please enter a video topic.', 'error');

    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    btn.disabled = true;

    fetch('/api/ai/video_summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic })
    })
    .then(res => res.json())
    .then(data => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (data.success) {
            const resDiv = document.getElementById('video-summary-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = '<strong>Summary Notes:</strong>\n' + data.summary;
        } else {
            showToast(data.error || 'Failed to generate summary.', 'error');
        }
    })
    .catch(err => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('Network error occurred.', 'error');
    });
}

function generateQuiz() {
    const subject = document.getElementById('quiz-subject').value;
    const topic = document.getElementById('quiz-topic').value;
    if (!subject || !topic) return showToast('Please enter both subject and topic.', 'error');

    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    btn.disabled = true;

    fetch('/api/ai/quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject: subject, topic: topic })
    })
    .then(res => res.json())
    .then(data => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (data.success) {
            const resDiv = document.getElementById('quiz-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = '<strong>Generated Quiz:</strong>\n' + data.quiz;
        } else {
            showToast(data.error || 'Failed to generate quiz.', 'error');
        }
    })
    .catch(err => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('Network error occurred.', 'error');
    });
}

function generateAnnouncement() {
    const promptText = document.getElementById('announcement-prompt').value;
    if (!promptText) return showToast('Please describe the announcement.', 'error');

    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Drafting...';
    btn.disabled = true;

    fetch('/api/ai/announcement', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptText })
    })
    .then(res => res.json())
    .then(data => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (data.success) {
            const resDiv = document.getElementById('announcement-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = '<strong>Draft:</strong>\n' + data.announcement;
        } else {
            showToast(data.error || 'Failed to generate announcement.', 'error');
        }
    })
    .catch(err => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('Network error occurred.', 'error');
    });
}


// --- STUDENT AI TOOLS ---

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    // Append user message
    const chatHistory = document.getElementById('chat-history');
    chatHistory.innerHTML += `
        <div class="chat-message user-message mb-3 text-right">
            <strong>You:</strong>
            <p>${message}</p>
        </div>
    `;
    input.value = '';

    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;

    // Show loading
    const loadingId = 'loading-' + Date.now();
    chatHistory.innerHTML += `
        <div id="${loadingId}" class="chat-message bot-message mb-3 text-secondary">
            <i class="fas fa-spinner fa-spin"></i> TutorBot is thinking...
        </div>
    `;
    chatHistory.scrollTop = chatHistory.scrollHeight;

    fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById(loadingId).remove();
        if (data.success) {
            chatHistory.innerHTML += `
                <div class="chat-message bot-message mb-3">
                    <strong><i class="fas fa-robot text-primary"></i> TutorBot:</strong>
                    <p style="white-space: pre-wrap;">${data.reply}</p>
                </div>
            `;
        } else {
            showToast(data.error || 'Failed to get reply.', 'error');
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
    })
    .catch(err => {
        document.getElementById(loadingId).remove();
        showToast('Network error.', 'error');
    });
}

function solveDoubt() {
    const question = document.getElementById('doubt-input').value.trim();
    if (!question) return showToast('Please enter your question.', 'error');

    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Solving...';
    btn.disabled = true;

    fetch('/api/ai/doubt_solver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
    })
    .then(res => res.json())
    .then(data => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (data.success) {
            const resDiv = document.getElementById('doubt-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = '<strong>Solution:</strong>\n' + data.answer;
        } else {
            showToast(data.error || 'Failed to solve doubt.', 'error');
        }
    })
    .catch(err => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('Network error occurred.', 'error');
    });
}
