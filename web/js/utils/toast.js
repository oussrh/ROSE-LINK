/**
 * ROSE Link - Toast Notifications
 * Accessible toast notification system
 */

/**
 * Color mappings for toast types
 */
const TOAST_COLORS = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    info: 'bg-blue-600',
    warning: 'bg-yellow-600'
};

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type: 'success', 'error', 'info', 'warning'
 */
export function showToast(message, type = 'info') {
    const colorClass = TOAST_COLORS[type] || TOAST_COLORS.info;

    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white text-sm ${colorClass} shadow-lg z-50 transition-all transform translate-y-0 opacity-100`;

    // Accessibility attributes
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
    toast.setAttribute('aria-atomic', 'true');

    // Use textContent to prevent XSS
    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        toast.classList.add('translate-y-2', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Make showToast globally available
window.showToast = showToast;
