// ASWATHAMA CLASSES - Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    // Mobile Sidebar Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Modal Logic
    const modals = document.querySelectorAll('.modal');
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    const closeButtons = document.querySelectorAll('.close-modal');

    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            const target = document.querySelector(trigger.dataset.modalTarget);
            if (target) target.classList.add('active');
        });
    });

    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').classList.remove('active');
        });
    });

    window.addEventListener('click', (e) => {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

// Helper function for API calls
async function apiCall(url, method, data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: 'An error occurred' };
    }
}

// AI Chatbot Logic
async function sendChatMessage() {
    const inputField = document.getElementById('chatInput');
    const message = inputField.value.trim();
    if (!message) return;

    const chatMessages = document.getElementById('chatMessages');

    // Add user message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'message user';
    userMsgDiv.textContent = message;
    chatMessages.appendChild(userMsgDiv);

    inputField.value = '';

    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai';
    loadingDiv.innerHTML = '<span class="loader"></span> Thinking...';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Call API
    const response = await apiCall('/api/ai/chat', 'POST', { message: message });

    // Replace loading with response
    loadingDiv.innerHTML = response.reply || response.error;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add Student Logic
async function addStudent(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        name: form.name.value,
        class: form.class.value,
        roll: form.roll.value,
        phone: form.phone.value,
        email: form.email.value,
        parent: form.parent.value
    };

    const result = await apiCall('/api/students', 'POST', data);
    if (result.success) {
        window.location.reload();
    } else {
        alert("Failed to add student.");
    }
}

// Edit Student Logic
function openEditStudentModal(id, name, cls, roll, phone, email, parent) {
    document.getElementById('edit_id').value = id;
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_class').value = cls;
    document.getElementById('edit_roll').value = roll;
    document.getElementById('edit_phone').value = phone;
    document.getElementById('edit_email').value = email;
    document.getElementById('edit_parent').value = parent;
    document.getElementById('editStudentModal').classList.add('active');
}

async function editStudent(event) {
    event.preventDefault();
    const form = event.target;
    const id = form.id.value;
    const data = {
        name: form.name.value,
        class: form.class.value,
        roll: form.roll.value,
        phone: form.phone.value,
        email: form.email.value,
        parent: form.parent.value
    };

    const result = await apiCall(`/api/students/${id}`, 'PUT', data);
    if (result.success) {
        window.location.reload();
    } else {
        alert("Failed to update student.");
    }
}

// Delete Student
async function deleteStudent(id) {
    if (confirm("Are you sure you want to delete this student?")) {
        const result = await apiCall(`/api/students/${id}`, 'DELETE');
        if (result.success) {
            window.location.reload();
        }
    }
}

// AI Announcement Generate
async function generateAnnouncement() {
    const promptInput = document.getElementById('aiPromptInput').value;
    const resultBox = document.getElementById('message');
    const btn = document.getElementById('generateBtn');

    if (!promptInput) {
        alert("Please enter a prompt");
        return;
    }

    btn.innerHTML = '<span class="loader"></span>';
    btn.disabled = true;

    const response = await apiCall('/api/ai/announcement', 'POST', { prompt: promptInput });

    btn.innerHTML = '<i class="fas fa-magic"></i> Generate with AI';
    btn.disabled = false;

    if (response.announcement) {
        resultBox.value = response.announcement;
    }
}

// AI Doubt Solver Logic
async function solveDoubt() {
    const question = document.getElementById('doubtInput').value;
    if (!question) return;

    const btn = document.getElementById('solveBtn');
    const resultArea = document.getElementById('doubtResult');

    btn.innerHTML = '<span class="loader"></span>';
    btn.disabled = true;

    const response = await apiCall('/api/ai/doubt', 'POST', { question: question });

    btn.innerHTML = 'Ask AI Tutor';
    btn.disabled = false;

    resultArea.style.display = 'block';
    resultArea.innerHTML = `<strong>Solution:</strong><br><br>${response.answer.replace(/\n/g, '<br>')}`;
}

// Save Attendance
async function saveAttendance() {
    const rows = document.querySelectorAll('#attendanceTable tbody tr');
    const records = [];
    const date = document.getElementById('attendanceDate').value;

    rows.forEach(row => {
        const studentId = row.dataset.id;
        const status = row.querySelector('select').value;
        records.push({ student_id: studentId, status: status });
    });

    const btn = document.getElementById('saveAttBtn');
    btn.innerHTML = '<span class="loader"></span> Saving...';

    const result = await apiCall('/api/attendance', 'POST', { date: date, records: records });

    btn.innerHTML = '<i class="fas fa-save"></i> Save Attendance';

    if (result.success) {
        alert('Attendance saved successfully!');
    } else {
        alert('Error saving attendance.');
    }
}
