// Utility func for showing custom modals (alert replacement)
function showMessage(title, message) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay active';
    overlay.innerHTML = `
        <div class="modal-content glass">
            <div class="modal-header">
                <h2>${title}</h2>
                <button class="close-btn">&times;</button>
            </div>
            <p id="custom-modal-msg"></p>
        </div>
    `;
    // Prevent XSS
    overlay.querySelector('#custom-modal-msg').textContent = message;

    overlay.querySelector('.close-btn').addEventListener('click', () => {
        document.body.removeChild(overlay);
    });
    document.body.appendChild(overlay);
}

async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (data) options.body = JSON.stringify(data);

    try {
        const response = await fetch(url, options);
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login';
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showMessage('Error', 'An error occurred while fetching data.');
        return null;
    }
}

// Mobile sidebar toggle
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }
});
