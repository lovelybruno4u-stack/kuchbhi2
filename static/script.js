// General UI interactions

document.addEventListener('DOMContentLoaded', () => {
    // Mobile sidebar toggle
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    // Highlight active nav link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Custom Modal System (No native alerts)
const modal = {
    show: function(title, message, isError = false) {
        const overlay = document.getElementById('custom-modal');
        const titleEl = document.getElementById('modal-title');
        const msgEl = document.getElementById('modal-message');
        const closeBtn = document.getElementById('modal-close-btn');

        titleEl.textContent = title;
        msgEl.textContent = message;

        if (isError) {
            titleEl.style.color = 'var(--danger)';
        } else {
            titleEl.style.color = 'var(--text-primary)';
        }

        overlay.classList.remove('hidden');

        closeBtn.onclick = () => {
            overlay.classList.add('hidden');
        };
    }
};

// Common Fetch Utility
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(endpoint, options);
        // Handle redirect to login if unauthorized
        if (response.status === 401 || response.status === 403) {
             const data = await response.json();
             modal.show('Authentication Error', data.error || 'Please login again.', true);
             setTimeout(() => window.location.href = '/login', 2000);
             return null;
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        modal.show('Error', 'An unexpected error occurred. Check console for details.', true);
        return null;
    }
}
