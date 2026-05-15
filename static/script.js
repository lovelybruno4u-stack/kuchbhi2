// Custom Alert System
function showAlert(message, type = 'success') {
    const alertEl = document.createElement('div');
    alertEl.className = `custom-alert ${type}`;
    alertEl.innerText = message;
    document.body.appendChild(alertEl);

    // Trigger animation
    setTimeout(() => alertEl.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
        alertEl.classList.remove('show');
        setTimeout(() => alertEl.remove(), 300);
    }, 3000);
}

// Modal handling
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if(modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if(modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

// Close modals when clicking outside
document.addEventListener('click', (e) => {
    if(e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
});

// API Helper
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login';
            return { success: false, error: 'Session expired' };
        }
        const result = await response.json();
        return result;
    } catch (err) {
        console.error("API Error:", err);
        return { success: false, error: 'Network error' };
    }
}

// Set active nav link based on current path
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-item');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});
