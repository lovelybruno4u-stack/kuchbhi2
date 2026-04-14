// Mobile Sidebar Toggle
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// Modal handling
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal-backdrop')) {
        event.target.style.display = 'none';
    }
}

// AI Utility function
async function callAIApi(endpoint, payload, resultElementId, loadingElementId) {
    const resultEl = document.getElementById(resultElementId);
    const loadingEl = document.getElementById(loadingElementId);

    if (resultEl) resultEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'block';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (loadingEl) loadingEl.style.display = 'none';

        if (response.ok) {
            if (resultEl) {
                // Formatting basic markdown-like response to HTML for simplicity
                const formattedResult = data.result.replace(/\n/g, '<br>');
                resultEl.innerHTML = formattedResult;
                resultEl.style.display = 'block';
            }
            return data.result;
        } else {
            alert('Error: ' + (data.error || 'Something went wrong'));
        }
    } catch (error) {
        if (loadingEl) loadingEl.style.display = 'none';
        alert('Failed to connect to AI service');
        console.error(error);
    }
}
