// Helper to show custom DOM modal
function showModal(title, content) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay active';

    const modal = document.createElement('div');
    modal.className = 'modal-content';

    const header = document.createElement('div');
    header.className = 'modal-header';
    header.innerHTML = `<h3>${title}</h3><button class="close-btn">&times;</button>`;

    const body = document.createElement('div');
    body.className = 'modal-body';
    body.innerHTML = content;

    modal.appendChild(header);
    modal.appendChild(body);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    const closeBtn = header.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => {
        overlay.classList.remove('active');
        setTimeout(() => overlay.remove(), 300);
    });
}

// Global Fetch Wrapper for API calls to handle standard responses
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
            return { success: false, error: 'Unauthorized' };
        }
        return await response.json();
    } catch (err) {
        console.error('API Call Error:', err);
        return { success: false, error: 'Network error occurred.' };
    }
}

// UI Loader Helper
function createLoader() {
    return `<div class="loader"></div>`;
}

// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', () => {
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');

    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
});
