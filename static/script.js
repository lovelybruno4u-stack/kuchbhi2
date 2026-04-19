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

// AI Tools handling
document.addEventListener('DOMContentLoaded', () => {
    // --- Teacher AI Tools ---
    const btnQuizGen = document.getElementById('btn-quiz-generator');
    if(btnQuizGen) {
        btnQuizGen.addEventListener('click', async () => {
            const subject = prompt("Enter Subject:");
            const topic = prompt("Enter Topic:");
            if(!subject || !topic) return;

            btnQuizGen.disabled = true;
            btnQuizGen.textContent = "Generating...";

            try {
                const res = await fetch('/api/ai/quiz_generator', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({subject, topic})
                });
                const data = await res.json();
                if(data.success) {

                    showAIResult("Generated Quiz", data.quiz);

                } else {

                    showAIResult("Error", data.error);

                }
            } catch (err) {

                showAIResult("Error", err);

            } finally {
                btnQuizGen.disabled = false;
                btnQuizGen.textContent = "Generate Quiz";
            }
        });
    }

    const btnAttnInsight = document.getElementById('btn-attendance-analyzer');
    if(btnAttnInsight) {
        btnAttnInsight.addEventListener('click', async () => {
            btnAttnInsight.disabled = true;
            btnAttnInsight.textContent = "Analyzing...";

            try {
                const res = await fetch('/api/ai/attendance_insight', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({})
                });
                const data = await res.json();
                if(data.success) {

                    showAIResult("Attendance Insights", data.insights);

                } else {

                    showAIResult("Error", data.error);

                }
            } catch (err) {

                showAIResult("Error", err);

            } finally {
                btnAttnInsight.disabled = false;
                btnAttnInsight.textContent = "Analyze Attendance";
            }
        });
    }

    const btnVideoSum = document.getElementById('btn-video-summarizer');
    if(btnVideoSum) {
        btnVideoSum.addEventListener('click', async () => {
            const topic = prompt("Enter Video Topic:");
            if(!topic) return;

            btnVideoSum.disabled = true;
            btnVideoSum.textContent = "Generating...";

            try {
                const res = await fetch('/api/ai/video_summary', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({topic})
                });
                const data = await res.json();
                if(data.success) {

                    showAIResult("Video Summary", data.summary);

                } else {

                    showAIResult("Error", data.error);

                }
            } catch (err) {

                showAIResult("Error", err);

            } finally {
                btnVideoSum.disabled = false;
                btnVideoSum.textContent = "Summarize Video";
            }
        });
    }

    // --- Student Chatbot ---
    const btnChatSend = document.getElementById('btn-chat-send');
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');

    if(btnChatSend && chatInput && chatWindow) {
        btnChatSend.addEventListener('click', async () => {
            const question = chatInput.value.trim();
            if(!question) return;

            // Append user msg

            const userMsgDiv = document.createElement('div');
            userMsgDiv.style.textAlign = 'right';
            userMsgDiv.style.marginBottom = '5px';
            userMsgDiv.innerHTML = '<strong>You:</strong> ';
            const userTextNode = document.createTextNode(question);
            userMsgDiv.appendChild(userTextNode);
            chatWindow.appendChild(userMsgDiv);

            chatInput.value = '';

            btnChatSend.disabled = true;

            try {
                const res = await fetch('/api/ai/doubt_solver', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question})
                });
                const data = await res.json();
                if(data.success) {

                    const aiMsgDiv = document.createElement('div');
                    aiMsgDiv.style.textAlign = 'left';
                    aiMsgDiv.style.marginBottom = '5px';
                    aiMsgDiv.innerHTML = '<strong>AI:</strong> ';
                    const aiTextNode = document.createTextNode(data.answer);
                    aiMsgDiv.appendChild(aiTextNode);
                    chatWindow.appendChild(aiMsgDiv);

                } else {

                     const errorMsgDiv = document.createElement('div');
                     errorMsgDiv.style.textAlign = 'left';
                     errorMsgDiv.style.marginBottom = '5px';
                     errorMsgDiv.style.color = 'red';
                     errorMsgDiv.innerHTML = '<strong>Error:</strong> ';
                     const errorTextNode = document.createTextNode(data.error);
                     errorMsgDiv.appendChild(errorTextNode);
                     chatWindow.appendChild(errorMsgDiv);

                }
            } catch (err) {

                const catchMsgDiv = document.createElement('div');
                catchMsgDiv.style.textAlign = 'left';
                catchMsgDiv.style.marginBottom = '5px';
                catchMsgDiv.style.color = 'red';
                catchMsgDiv.innerHTML = '<strong>Error:</strong> ';
                const catchTextNode = document.createTextNode(err);
                catchMsgDiv.appendChild(catchTextNode);
                chatWindow.appendChild(catchMsgDiv);

            } finally {
                btnChatSend.disabled = false;
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        });
    }
});

function showAIResult(title, content) {
    let modal = document.getElementById('ai-result-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'ai-result-modal';
        modal.style.position = 'fixed';
        modal.style.top = '50%';
        modal.style.left = '50%';
        modal.style.transform = 'translate(-50%, -50%)';
        modal.style.backgroundColor = 'white';
        modal.style.padding = '20px';
        modal.style.borderRadius = '8px';
        modal.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        modal.style.zIndex = '1000';
        modal.style.maxWidth = '80%';
        modal.style.maxHeight = '80%';
        modal.style.overflowY = 'auto';

        const overlay = document.createElement('div');
        overlay.id = 'ai-result-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
        overlay.style.zIndex = '999';

        overlay.onclick = () => {
            document.body.removeChild(modal);
            document.body.removeChild(overlay);
        };
        document.body.appendChild(overlay);
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <h2 style="margin-top:0">${title}</h2>
        <pre style="white-space: pre-wrap; word-wrap: break-word; background: #f4f4f4; padding: 10px; border-radius: 4px;">${content}</pre>
        <button onclick="document.body.removeChild(document.getElementById('ai-result-modal')); document.body.removeChild(document.getElementById('ai-result-overlay'));" class="btn btn-secondary" style="margin-top: 10px;">Close</button>
    `;

    document.getElementById('ai-result-overlay').style.display = 'block';
    modal.style.display = 'block';
}

document.addEventListener('DOMContentLoaded', () => {
    const btnAnnounceGen = document.getElementById('btn-announcement-generator');
    if(btnAnnounceGen) {
        btnAnnounceGen.addEventListener('click', async () => {
            const topic = prompt("Enter Announcement Topic:");
            if(!topic) return;

            btnAnnounceGen.disabled = true;
            btnAnnounceGen.textContent = "Generating...";

            try {
                const res = await fetch('/api/ai/announcement', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({topic})
                });
                const data = await res.json();
                if(data.success) {
                    showAIResult("Generated Announcement", data.announcement);
                } else {
                    showAIResult("Error", data.error);
                }
            } catch (err) {
                showAIResult("Error", err);
            } finally {
                btnAnnounceGen.disabled = false;
                btnAnnounceGen.textContent = "Generate Announcement";
            }
        });
    }
});
