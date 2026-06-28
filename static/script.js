// Basic interactions for the platform
document.addEventListener('DOMContentLoaded', () => {
    // Hide flash messages after 5 seconds
    setTimeout(() => {
        const flashes = document.querySelectorAll('.flash');
        flashes.forEach(f => {
            f.style.opacity = '0';
            setTimeout(() => f.remove(), 300);
        });
    }, 5000);
});
