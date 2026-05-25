// Global Utility Functions

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Custom Modal instead of alert()
function showModal(title, message) {
    document.getElementById('modalTitle').innerText = title;
    document.getElementById('modalBody').innerHTML = `<p>${message}</p>`;
    document.getElementById('globalModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('globalModal').style.display = 'none';
}

// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('mobile-toggle');
    const sidebar = document.getElementById('sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }
});

// Generic API caller
async function apiCall(url, method = 'GET', data = null) {
    showLoading();
    try {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'API Error');
        }

        hideLoading();
        return result;
    } catch (error) {
        hideLoading();
        showModal('Error', error.message || 'Something went wrong. Please try again.');
        return null;
    }
}
