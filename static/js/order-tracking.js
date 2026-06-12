document.addEventListener('DOMContentLoaded', function() {
    const tracker = document.getElementById('orderTracker');
    if (!tracker) return;

    const orderId = tracker.dataset.orderId;
    const socket = io();

    socket.emit('join_order', { order_id: orderId });

    socket.on('order_update', function(data) {
        if (data.id == orderId) {
            updateTracker(data.status);
        }
    });

    function updateTracker(status) {
        const steps = tracker.querySelectorAll('.tracker-step');
        const statusList = Array.from(steps).map(s => s.textContent.trim().toLowerCase().replace(/ /g, '_'));
        const currentIndex = statusList.indexOf(status);

        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index < currentIndex) step.classList.add('completed');
            if (index === currentIndex) step.classList.add('active');
        });
    }
});
