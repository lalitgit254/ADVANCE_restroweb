document.addEventListener('DOMContentLoaded', function() {
    updateClock();
    setInterval(updateClock, 1000);
    updateTimers();
    setInterval(updateTimers, 1000);

    if (typeof io !== 'undefined') {
        const socket = io();
        socket.on('new_order', function(order) {
            playAlert();
            location.reload();
        });
        socket.on('order_ready', function(order) {
            location.reload();
        });
    }
});

function updateClock() {
    const el = document.getElementById('kdsClock');
    if (el) {
        el.textContent = new Date().toLocaleTimeString();
    }
}

function updateTimers() {
    document.querySelectorAll('.order-timer').forEach(timer => {
        const created = new Date(timer.dataset.created);
        const diff = Math.floor((Date.now() - created.getTime()) / 1000);
        const mins = Math.floor(diff / 60).toString().padStart(2, '0');
        const secs = (diff % 60).toString().padStart(2, '0');
        timer.textContent = mins + ':' + secs;

        if (diff > 1800) {
            timer.style.color = '#ff6b6b';
            timer.closest('.kds-order')?.classList.add('priority');
        }
    });
}

function playAlert() {
    try {
        const audio = new Audio('/static/sounds/alert.mp3');
        audio.play().catch(() => {});
    } catch (e) {}
}
