document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => navMenu.classList.toggle('active'));
    }

    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('active'));
    }

    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js').catch(() => {});
    }

    initSocket();
});

function initSocket() {
    if (typeof io === 'undefined') return;
    const socket = io();

    socket.on('connect', () => console.log('Connected to server'));
    socket.on('notification', (data) => showNotification(data));
    socket.on('order_update', (data) => {
        document.dispatchEvent(new CustomEvent('orderUpdate', { detail: data }));
    });
}

function showNotification(data) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(data.title, { body: data.message });
    }
}

function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2);
}
