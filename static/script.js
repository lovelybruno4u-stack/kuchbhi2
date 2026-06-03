// Utility function to show custom modals instead of native alerts
function showModal(title, message) {
    let overlay = document.getElementById('custom-modal');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'custom-modal';
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modal-title"></h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p id="modal-message" style="white-space: pre-wrap; line-height: 1.6;"></p>
                </div>
                <div class="mt-4 text-center">
                    <button class="btn btn-primary" onclick="closeModal()">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    document.getElementById('modal-title').innerText = title;
    // Basic markdown parsing for bold text
    let formattedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    document.getElementById('modal-message').innerHTML = formattedMessage;

    // Trigger layout before adding active class for animation
    void overlay.offsetWidth;
    overlay.classList.add('active');
}

window.closeModal = function() {
    const overlay = document.getElementById('custom-modal');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Mobile sidebar toggle
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('mobile-toggle');
    const sidebar = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Highlight active nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Login Role Selector Logic
    const roleOptions = document.querySelectorAll('.role-option');
    const roleInput = document.getElementById('role-input');

    if (roleOptions.length > 0 && roleInput) {
        roleOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Remove active from all
                roleOptions.forEach(opt => opt.classList.remove('active'));
                // Add active to clicked
                this.classList.add('active');
                // Set hidden input value
                roleInput.value = this.dataset.role;
            });
        });
    }
});

// Generic Fetch Wrapper
async function apiCall(endpoint, method = 'GET', data = null) {
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
        const response = await fetch(endpoint, options);
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'API request failed');
        }
        return result;
    } catch (error) {
        console.error(error);
        showModal('Error', error.message);
        throw error;
    }
}
