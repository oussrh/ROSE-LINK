/**
 * ROSE Link - DOM Utilities
 * Helper functions for DOM manipulation and security
 */

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML string
 */
export function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

/**
 * Escape string for JavaScript context (prevents quote injection)
 * @param {string} str - String to escape
 * @returns {string} Escaped string safe for JS
 */
export function escapeJs(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

/**
 * Create an icon element
 * @param {string} name - Lucide icon name
 * @param {string} className - CSS class for sizing
 * @returns {string} HTML string for the icon
 */
export function icon(name, className = 'icon-sm') {
    return `<i data-lucide="${escapeHtml(name)}" class="${escapeHtml(className)}"></i>`;
}

/**
 * Reinitialize Lucide icons after dynamic content updates
 */
export function refreshIcons() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Spinner SVG for loading states
 */
export const spinnerSvg = `<svg class="w-4 h-4 spin-slow" fill="none" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>`;

/**
 * Set button loading state
 * @param {HTMLElement} button - Button element
 * @param {boolean} isLoading - Whether button is in loading state
 */
export function setButtonLoading(button, isLoading) {
    if (!button) return;

    // Import t function dynamically to avoid circular dependency
    const loadingText = window.t ? window.t('loading') : 'Loading...';

    if (isLoading) {
        button.disabled = true;
        button.dataset.originalContent = button.innerHTML;
        button.innerHTML = spinnerSvg + ' ' + loadingText;
        button.classList.add('opacity-75', 'cursor-not-allowed');
    } else {
        button.disabled = false;
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            delete button.dataset.originalContent;
        }
        button.classList.remove('opacity-75', 'cursor-not-allowed');
    }
}

/**
 * Format bytes to human readable string
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted string (e.g., "1.5 MB")
 */
export function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
