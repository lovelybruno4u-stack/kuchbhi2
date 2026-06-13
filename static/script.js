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
// TEACHER AI TOOLS LOGIC
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    // Video Summary
    const formVideo = document.getElementById('form-video-summary');
    if (formVideo) {
        formVideo.addEventListener('submit', async (e) => {
            e.preventDefault();
            const topic = document.getElementById('video-topic').value;
            const btn = document.getElementById('btn-video-summary');
            const resBox = document.getElementById('res-video-summary');

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            resBox.style.display = 'none';

            try {
                const res = await fetch('/api/ai/video_summary', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({topic})
                });
                const data = await res.json();

                resBox.style.display = 'block';
                if (data.success) {
                    resBox.textContent = data.answer;
                } else {
                    resBox.textContent = 'Error: ' + data.error;
                }
            } catch (err) {
                resBox.style.display = 'block';
                resBox.textContent = 'Failed to generate summary.';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generate Summary';
            }
        });
    }

    // Quiz Generator
    const formQuiz = document.getElementById('form-quiz-gen');
    if (formQuiz) {
        formQuiz.addEventListener('submit', async (e) => {
            e.preventDefault();
            const subject = document.getElementById('quiz-subject').value;
            const topic = document.getElementById('quiz-topic').value;
            const btn = document.getElementById('btn-quiz-gen');
            const resBox = document.getElementById('res-quiz-gen');

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            resBox.style.display = 'none';

            try {
                const res = await fetch('/api/ai/quiz', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({subject, topic})
                });
                const data = await res.json();

                resBox.style.display = 'block';
                if (data.success) {
                    resBox.textContent = data.answer;
                } else {
                    resBox.textContent = 'Error: ' + data.error;
                }
            } catch (err) {
                resBox.style.display = 'block';
                resBox.textContent = 'Failed to generate quiz.';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generate 5 MCQs';
            }
        });
    }

    // Attendance Insight
    const btnAttendance = document.getElementById('btn-attendance-insight');
    if (btnAttendance) {
        btnAttendance.addEventListener('click', async () => {
            const resBox = document.getElementById('res-attendance-insight');

            btnAttendance.disabled = true;
            btnAttendance.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            resBox.style.display = 'none';

            try {
                const res = await fetch('/api/ai/attendance', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await res.json();

                resBox.style.display = 'block';
                if (data.success) {
                    resBox.textContent = data.answer;
                } else {
                    resBox.textContent = 'Error: ' + data.error;
                }
            } catch (err) {
                resBox.style.display = 'block';
                resBox.textContent = 'Failed to analyze attendance.';
            } finally {
                btnAttendance.disabled = false;
                btnAttendance.textContent = 'Analyze Attendance';
            }
        });
    }

    // Announcement Generator
    const formAnnouncement = document.getElementById('form-announcement-gen');
    if (formAnnouncement) {
        formAnnouncement.addEventListener('submit', async (e) => {
            e.preventDefault();
            const details = document.getElementById('announcement-details').value;
            const btn = document.getElementById('btn-announcement-gen');
            const resBox = document.getElementById('res-announcement-gen');

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Drafting...';
            resBox.style.display = 'none';

            try {
                const res = await fetch('/api/ai/announcement', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({details})
                });
                const data = await res.json();

                resBox.style.display = 'block';
                if (data.success) {
                    resBox.textContent = data.answer;
                } else {
                    resBox.textContent = 'Error: ' + data.error;
                }
            } catch (err) {
                resBox.style.display = 'block';
                resBox.textContent = 'Failed to draft announcement.';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Draft Announcement';
            }
        });
    }
});

// ==========================================
// STUDENT AI CHATBOT LOGIC
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    // Chatbot
    const formChat = document.getElementById('form-chat');
    if (formChat) {
        formChat.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inputField = document.getElementById('chat-input');
            const message = inputField.value.trim();
            if (!message) return;

            const btn = document.getElementById('btn-chat');
            const chatWindow = document.getElementById('chat-window');

            // Add user message
            const userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'chat-message user-message';
            userMsgDiv.style.alignSelf = 'flex-end';
            userMsgDiv.style.background = 'rgba(255,255,255,0.1)';
            userMsgDiv.style.padding = '0.5rem 1rem';
            userMsgDiv.style.borderRadius = '8px';
            userMsgDiv.textContent = message;
            chatWindow.appendChild(userMsgDiv);

            inputField.value = '';
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            chatWindow.scrollTop = chatWindow.scrollHeight;

            try {
                const res = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                });
                const data = await res.json();

                const aiMsgDiv = document.createElement('div');
                aiMsgDiv.className = 'chat-message ai-message';
                aiMsgDiv.style.alignSelf = 'flex-start';
                aiMsgDiv.style.background = 'rgba(99,102,241,0.2)';
                aiMsgDiv.style.padding = '0.5rem 1rem';
                aiMsgDiv.style.borderRadius = '8px';

                if (data.success) {
                    aiMsgDiv.textContent = data.answer;
                } else {
                    aiMsgDiv.textContent = 'Error: ' + data.error;
                }
                chatWindow.appendChild(aiMsgDiv);
            } catch (err) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'chat-message ai-message';
                errorDiv.style.alignSelf = 'flex-start';
                errorDiv.style.background = 'rgba(239,68,68,0.2)';
                errorDiv.style.padding = '0.5rem 1rem';
                errorDiv.style.borderRadius = '8px';
                errorDiv.textContent = 'Failed to connect to AI server.';
                chatWindow.appendChild(errorDiv);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        });
    }

    // Doubt Solver
    const formDoubt = document.getElementById('form-doubt-solver');
    if (formDoubt) {
        formDoubt.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = document.getElementById('doubt-question').value;
            const btn = document.getElementById('btn-doubt-solver');
            const resBox = document.getElementById('res-doubt-solver');

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Solving...';
            resBox.style.display = 'none';

            try {
                const res = await fetch('/api/ai/doubt_solver', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question})
                });
                const data = await res.json();

                resBox.style.display = 'block';
                if (data.success) {
                    resBox.textContent = data.answer;
                } else {
                    resBox.textContent = 'Error: ' + data.error;
                }
            } catch (err) {
                resBox.style.display = 'block';
                resBox.textContent = 'Failed to solve doubt.';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Solve Doubt';
            }
        });
    }
});
