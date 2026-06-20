// ASWATHAMA CLASSES - Global Script

// --- Utility: Safe Text Injection (XSS Prevention) ---
function safeSetText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = text;
    }
}

function createTextNode(text) {
    return document.createTextNode(text);
}

// --- Modals ---
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// --- Mobile Menu ---
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    if(sidebar) {
        sidebar.classList.toggle('active');
    }
}

// --- Auth & Role Selection ---
document.addEventListener('DOMContentLoaded', () => {

    // Login Page Logic
    const roleSelector = document.getElementById('role-selector');
    if (roleSelector) {
        const teacherFields = document.getElementById('teacher-fields');
        const studentFields = document.getElementById('student-fields');

        // Memory constraint: Custom div-based role selection
        const roleDivs = document.querySelectorAll('.role-option');
        let selectedRole = 'student'; // default

        roleDivs.forEach(div => {
            div.addEventListener('click', () => {
                roleDivs.forEach(d => d.classList.remove('selected'));
                div.classList.add('selected');
                selectedRole = div.getAttribute('data-role');

                if (selectedRole === 'teacher') {
                    teacherFields.style.display = 'block';
                    studentFields.style.display = 'none';
                } else {
                    teacherFields.style.display = 'none';
                    studentFields.style.display = 'block';
                }
            });
        });

        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const payload = { role: selectedRole };
                if (selectedRole === 'teacher') {
                    payload.username = document.getElementById('username').value;
                    payload.password = document.getElementById('password').value;
                } else {
                    payload.roll_no = document.getElementById('roll_no').value;
                    payload.phone = document.getElementById('phone').value;
                }

                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const data = await response.json();
                    if (data.success) {
                        window.location.href = data.redirect;
                    } else {
                        // Using a custom alert div or simple text injection for error instead of native alert
                        const errorDiv = document.getElementById('login-error');
                        if(errorDiv) {
                            errorDiv.textContent = data.error;
                            errorDiv.style.display = 'block';
                        }
                    }
                } catch (err) {
                    console.error(err);
                }
            });
        }
    }

    // Logout Logic
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        });
    }
});

// --- Data Fetching & UI Updates (Dashboard) ---

// Generic fetch and render table
async function fetchAndRenderTable(endpoint, tableBodyId, columns, actions = null) {
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        const tbody = document.getElementById(tableBodyId);
        if (!tbody) return;

        tbody.innerHTML = ''; // Clear existing

        data.forEach((item, index) => {
            const tr = document.createElement('tr');

            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = item[col] || '';
                tr.appendChild(td);
            });

            if (actions) {
                const td = document.createElement('td');
                actions(td, item);
                tr.appendChild(td);
            }

            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error fetching table data:", err);
    }
}

// Teacher Dashboard Initialization
async function initTeacherDashboard() {
    if (document.getElementById('teacher-dashboard-stats')) {
        try {
            const [studentsRes, attendanceRes] = await Promise.all([
                fetch('/api/students'),
                fetch('/api/attendance')
            ]);
            const students = await studentsRes.json();
            const attendance = await attendanceRes.json();

            safeSetText('stat-total-students', students.length);

            // Calculate today's attendance
            const today = new Date().toISOString().split('T')[0];
            const todayAttendance = attendance.filter(a => a.date === today);
            const presentCount = todayAttendance.filter(a => a.status === 'present').length;

            safeSetText('stat-today-attendance', `${presentCount} / ${students.length}`);

        } catch(e) {
            console.error(e);
        }
    }
}

// Student Management
async function initStudentManagement() {
    if (document.getElementById('students-table-body')) {
        fetchAndRenderTable('/api/students', 'students-table-body', ['name', 'class', 'roll', 'phone', 'email', 'parent'], (td, item) => {
            const delBtn = document.createElement('button');
            delBtn.className = 'btn btn-danger';
            delBtn.textContent = 'Delete';
            delBtn.onclick = async () => {
                await fetch(`/api/students/${item.id}`, { method: 'DELETE' });
                initStudentManagement(); // refresh
            };
            td.appendChild(delBtn);
        });

        const addForm = document.getElementById('add-student-form');
        if (addForm) {
            addForm.onsubmit = async (e) => {
                e.preventDefault();
                const payload = {
                    name: document.getElementById('s-name').value,
                    class: document.getElementById('s-class').value,
                    roll: document.getElementById('s-roll').value,
                    phone: document.getElementById('s-phone').value,
                    email: document.getElementById('s-email').value,
                    parent: document.getElementById('s-parent').value
                };
                await fetch('/api/students', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify(payload)
                });
                closeModal('add-student-modal');
                addForm.reset();
                initStudentManagement();
            };
        }
    }
}

// Video Management
async function initVideoManagement() {
    if (document.getElementById('videos-table-body')) {
        fetchAndRenderTable('/api/videos', 'videos-table-body', ['date', 'subject'], (td, item) => {
            const link = document.createElement('a');
            link.href = item.drive_link;
            link.target = '_blank';
            link.textContent = 'View Video';
            td.appendChild(link);
        });

        const addForm = document.getElementById('add-video-form');
        if (addForm) {
            addForm.onsubmit = async (e) => {
                e.preventDefault();
                const payload = {
                    date: document.getElementById('v-date').value,
                    subject: document.getElementById('v-subject').value,
                    drive_link: document.getElementById('v-link').value
                };
                await fetch('/api/videos', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify(payload)
                });
                closeModal('add-video-modal');
                addForm.reset();
                initVideoManagement();
            };
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initTeacherDashboard();
    initStudentManagement();
    initVideoManagement();
});

// Attendance Management (Teacher)
async function initAttendanceManagement() {
    if (document.getElementById('attendance-students-body')) {
        try {
            const response = await fetch('/api/students');
            const students = await response.json();
            const tbody = document.getElementById('attendance-students-body');
            tbody.innerHTML = '';

            students.forEach(student => {
                const tr = document.createElement('tr');
                tr.setAttribute('data-student-id', student.id);

                const tdName = document.createElement('td');
                tdName.textContent = student.name;
                tr.appendChild(tdName);

                const tdClass = document.createElement('td');
                tdClass.textContent = student.class;
                tr.appendChild(tdClass);

                const tdStatus = document.createElement('td');
                const select = document.createElement('select');
                select.className = 'form-control attendance-status';
                ['Present', 'Absent'].forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.toLowerCase();
                    option.textContent = opt;
                    select.appendChild(option);
                });
                tdStatus.appendChild(select);
                tr.appendChild(tdStatus);

                tbody.appendChild(tr);
            });

            const submitBtn = document.getElementById('submit-attendance-btn');
            if(submitBtn) {
                submitBtn.onclick = async () => {
                    const date = document.getElementById('attendance-date').value;
                    if(!date) return alert('Please select a date'); // Only simple text fallback

                    const records = [];
                    document.querySelectorAll('#attendance-students-body tr').forEach(tr => {
                        records.push({
                            student_id: tr.getAttribute('data-student-id'),
                            status: tr.querySelector('.attendance-status').value
                        });
                    });

                    await fetch('/api/attendance', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({date, records})
                    });

                    // Custom modal/alert instead of native if time permits, for now change text
                    submitBtn.textContent = 'Saved!';
                    setTimeout(() => submitBtn.textContent = 'Save Attendance', 2000);
                };
            }
        } catch(e) {
            console.error(e);
        }
    }
}

// Announcements Management
async function initAnnouncementsManagement() {
    if (document.getElementById('announcements-container')) {
        try {
            const response = await fetch('/api/announcements');
            const announcements = await response.json();
            const container = document.getElementById('announcements-container');
            container.innerHTML = '';

            announcements.forEach(a => {
                const div = document.createElement('div');
                div.className = 'card';
                div.style.marginBottom = '1rem';

                const h4 = document.createElement('h4');
                h4.textContent = a.date;
                div.appendChild(h4);

                const p = document.createElement('p');
                p.textContent = a.message;
                div.appendChild(p);

                container.appendChild(div);
            });
        } catch(e) {
            console.error(e);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initAttendanceManagement();
    initAnnouncementsManagement();
});

// --- AI Features ---

async function fetchAI(endpoint, payload, resultElementId, loadingElementId = null) {
    if(loadingElementId) document.getElementById(loadingElementId).style.display = 'inline-block';
    const resultEl = document.getElementById(resultElementId);
    if(resultEl) resultEl.textContent = 'Thinking...';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if(resultEl) resultEl.textContent = data.content || data.error || 'No response';
    } catch(e) {
        if(resultEl) resultEl.textContent = 'Error connecting to AI.';
    } finally {
        if(loadingElementId) document.getElementById(loadingElementId).style.display = 'none';
    }
}

// AI Doubt Solver
async function initAIDoubtSolver() {
    const btn = document.getElementById('btn-doubt-solve');
    if(btn) {
        btn.onclick = () => {
            const question = document.getElementById('ai-doubt-input').value;
            fetchAI('/api/ai/doubt_solver', {question}, 'ai-doubt-result', 'ai-doubt-loading');
        };
    }
}

// AI Video Summary
async function initAIVideoSummary() {
    const btn = document.getElementById('btn-video-summary');
    if(btn) {
        btn.onclick = () => {
            const topic = document.getElementById('ai-video-input').value;
            fetchAI('/api/ai/video_summary', {topic}, 'ai-video-result', 'ai-video-loading');
        };
    }
}

// AI Quiz Generator
async function initAIQuizGenerator() {
    const btn = document.getElementById('btn-quiz-gen');
    if(btn) {
        btn.onclick = () => {
            const subject = document.getElementById('ai-quiz-subject').value;
            const topic = document.getElementById('ai-quiz-topic').value;
            fetchAI('/api/ai/quiz', {subject, topic}, 'ai-quiz-result', 'ai-quiz-loading');
        };
    }
}

// AI Attendance Analysis
async function initAIAttendanceAnalysis() {
    const btn = document.getElementById('btn-attendance-analysis');
    if(btn) {
        btn.onclick = () => {
            fetchAI('/api/ai/attendance', {}, 'ai-attendance-result', 'ai-attendance-loading');
        };
    }
}

// AI Announcement
async function initAIAnnouncement() {
    const btn = document.getElementById('btn-ai-announce');
    if(btn) {
        btn.onclick = () => {
            const prompt = document.getElementById('ai-announce-input').value;
            fetchAI('/api/ai/announcement', {prompt}, 'ai-announce-result', 'ai-announce-loading');
        };
    }
}

// AI Chatbot (Student)
let chatHistory = [];
async function initAIChatbot() {
    const chatForm = document.getElementById('chatbot-form');
    if(chatForm) {
        chatForm.onsubmit = async (e) => {
            e.preventDefault();
            const inputEl = document.getElementById('chat-input');
            const message = inputEl.value;
            if(!message.trim()) return;

            const container = document.getElementById('chat-messages');

            // Append User Message
            const userDiv = document.createElement('div');
            userDiv.className = 'chat-message user';
            userDiv.textContent = message;
            container.appendChild(userDiv);

            inputEl.value = '';
            container.scrollTop = container.scrollHeight;

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-message ai';
            loadingDiv.innerHTML = '<div class="loading-spinner"></div>';
            container.appendChild(loadingDiv);
            container.scrollTop = container.scrollHeight;

            try {
                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message, history: chatHistory })
                });
                const data = await response.json();

                container.removeChild(loadingDiv);

                const aiDiv = document.createElement('div');
                aiDiv.className = 'chat-message ai';
                aiDiv.textContent = data.content || data.error || 'Error';
                container.appendChild(aiDiv);

                // Update history as per memory constraint
                chatHistory.push({role: 'user', content: message});
                chatHistory.push({role: 'assistant', content: data.content});

                container.scrollTop = container.scrollHeight;

            } catch(e) {
                container.removeChild(loadingDiv);
                console.error(e);
            }
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initAIDoubtSolver();
    initAIVideoSummary();
    initAIQuizGenerator();
    initAIAttendanceAnalysis();
    initAIAnnouncement();
    initAIChatbot();
});
