/**
 * ROSE Link - Modal/Dialog Component
 * Accessible modal dialogs following shadcn/ui patterns
 */

import { t } from '../i18n.js';
import { icon, refreshIcons } from './dom.js';

/**
 * Modal state management
 */
let activeModal = null;

/**
 * Create and show a confirmation dialog
 * @param {Object} options - Dialog options
 * @param {string} options.title - Dialog title
 * @param {string} options.message - Dialog message
 * @param {string} [options.confirmText] - Confirm button text
 * @param {string} [options.cancelText] - Cancel button text
 * @param {string} [options.variant] - Button variant: 'default', 'danger'
 * @param {string} [options.icon] - Lucide icon name
 * @returns {Promise<boolean>} Resolves to true if confirmed, false if cancelled
 */
export function showConfirm({
    title,
    message,
    confirmText = null,
    cancelText = null,
    variant = 'default',
    icon: iconName = 'alert-circle'
}) {
    return new Promise((resolve) => {
        // Close any existing modal
        closeModal();

        const confirmLabel = confirmText || t('confirm') || 'Confirm';
        const cancelLabel = cancelText || t('cancel') || 'Cancel';

        // Determine button colors based on variant
        const confirmBtnClass = variant === 'danger'
            ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
            : 'bg-rose-600 hover:bg-rose-700 focus:ring-rose-500';

        const iconColor = variant === 'danger' ? 'text-red-400' : 'text-rose-400';

        // Create modal backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in';
        backdrop.setAttribute('role', 'dialog');
        backdrop.setAttribute('aria-modal', 'true');
        backdrop.setAttribute('aria-labelledby', 'modal-title');
        backdrop.setAttribute('aria-describedby', 'modal-description');

        // Create modal content
        backdrop.innerHTML = `
            <div class="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl max-w-md w-full transform animate-scale-in">
                <div class="p-6">
                    <div class="flex items-start gap-4">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center ${iconColor}">
                            ${icon(iconName, 'w-5 h-5')}
                        </div>
                        <div class="flex-1 min-w-0">
                            <h3 id="modal-title" class="text-lg font-semibold text-white">${escapeForHtml(title)}</h3>
                            <p id="modal-description" class="mt-2 text-sm text-gray-400">${escapeForHtml(message)}</p>
                        </div>
                    </div>
                </div>
                <div class="flex gap-3 p-4 bg-gray-900/50 rounded-b-xl border-t border-gray-700">
                    <button type="button" id="modal-cancel"
                        class="flex-1 px-4 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-800">
                        ${escapeForHtml(cancelLabel)}
                    </button>
                    <button type="button" id="modal-confirm"
                        class="flex-1 px-4 py-2.5 ${confirmBtnClass} text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800">
                        ${escapeForHtml(confirmLabel)}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(backdrop);
        activeModal = backdrop;
        refreshIcons();

        // Focus the cancel button by default (safer option)
        const cancelBtn = backdrop.querySelector('#modal-cancel');
        const confirmBtn = backdrop.querySelector('#modal-confirm');
        cancelBtn.focus();

        // Handle keyboard navigation
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                cleanup();
                resolve(false);
            } else if (e.key === 'Tab') {
                // Trap focus within modal
                const focusable = backdrop.querySelectorAll('button');
                const first = focusable[0];
                const last = focusable[focusable.length - 1];

                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        };

        // Cleanup function
        const cleanup = () => {
            document.removeEventListener('keydown', handleKeydown);
            backdrop.classList.add('animate-fade-out');
            backdrop.querySelector('div').classList.add('animate-scale-out');
            setTimeout(() => {
                backdrop.remove();
                activeModal = null;
            }, 150);
        };

        // Event listeners
        document.addEventListener('keydown', handleKeydown);

        cancelBtn.addEventListener('click', () => {
            cleanup();
            resolve(false);
        });

        confirmBtn.addEventListener('click', () => {
            cleanup();
            resolve(true);
        });

        // Close on backdrop click
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                cleanup();
                resolve(false);
            }
        });
    });
}

/**
 * Show an alert dialog (single button)
 * @param {Object} options - Dialog options
 * @param {string} options.title - Dialog title
 * @param {string} options.message - Dialog message
 * @param {string} [options.buttonText] - Button text
 * @param {string} [options.variant] - Variant: 'default', 'success', 'error', 'warning'
 * @param {string} [options.icon] - Lucide icon name
 * @returns {Promise<void>} Resolves when dialog is closed
 */
export function showAlert({
    title,
    message,
    buttonText = null,
    variant = 'default',
    icon: iconName = 'info'
}) {
    return new Promise((resolve) => {
        closeModal();

        const btnLabel = buttonText || t('ok') || 'OK';

        // Determine colors based on variant
        const variantConfig = {
            default: { iconColor: 'text-blue-400', bgColor: 'bg-blue-600 hover:bg-blue-700' },
            success: { iconColor: 'text-green-400', bgColor: 'bg-green-600 hover:bg-green-700' },
            error: { iconColor: 'text-red-400', bgColor: 'bg-red-600 hover:bg-red-700' },
            warning: { iconColor: 'text-yellow-400', bgColor: 'bg-yellow-600 hover:bg-yellow-700' }
        };
        const config = variantConfig[variant] || variantConfig.default;

        const backdrop = document.createElement('div');
        backdrop.className = 'fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in';
        backdrop.setAttribute('role', 'alertdialog');
        backdrop.setAttribute('aria-modal', 'true');
        backdrop.setAttribute('aria-labelledby', 'alert-title');
        backdrop.setAttribute('aria-describedby', 'alert-description');

        backdrop.innerHTML = `
            <div class="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl max-w-md w-full transform animate-scale-in">
                <div class="p-6">
                    <div class="flex items-start gap-4">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center ${config.iconColor}">
                            ${icon(iconName, 'w-5 h-5')}
                        </div>
                        <div class="flex-1 min-w-0">
                            <h3 id="alert-title" class="text-lg font-semibold text-white">${escapeForHtml(title)}</h3>
                            <p id="alert-description" class="mt-2 text-sm text-gray-400">${escapeForHtml(message)}</p>
                        </div>
                    </div>
                </div>
                <div class="p-4 bg-gray-900/50 rounded-b-xl border-t border-gray-700">
                    <button type="button" id="alert-close"
                        class="w-full px-4 py-2.5 ${config.bgColor} text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800">
                        ${escapeForHtml(btnLabel)}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(backdrop);
        activeModal = backdrop;
        refreshIcons();

        const closeBtn = backdrop.querySelector('#alert-close');
        closeBtn.focus();

        const handleKeydown = (e) => {
            if (e.key === 'Escape' || e.key === 'Enter') {
                cleanup();
                resolve();
            }
        };

        const cleanup = () => {
            document.removeEventListener('keydown', handleKeydown);
            backdrop.classList.add('animate-fade-out');
            backdrop.querySelector('div').classList.add('animate-scale-out');
            setTimeout(() => {
                backdrop.remove();
                activeModal = null;
            }, 150);
        };

        document.addEventListener('keydown', handleKeydown);

        closeBtn.addEventListener('click', () => {
            cleanup();
            resolve();
        });

        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                cleanup();
                resolve();
            }
        });
    });
}

/**
 * Show a prompt dialog with input field
 * @param {Object} options - Dialog options
 * @param {string} options.title - Dialog title
 * @param {string} options.message - Dialog message
 * @param {string} [options.placeholder] - Input placeholder
 * @param {string} [options.defaultValue] - Default input value
 * @param {string} [options.inputType] - Input type: 'text', 'password'
 * @param {string} [options.confirmText] - Confirm button text
 * @param {string} [options.cancelText] - Cancel button text
 * @param {string} [options.icon] - Lucide icon name
 * @returns {Promise<string|null>} Resolves to input value or null if cancelled
 */
export function showPrompt({
    title,
    message,
    placeholder = '',
    defaultValue = '',
    inputType = 'text',
    confirmText = null,
    cancelText = null,
    icon: iconName = 'edit-3'
}) {
    return new Promise((resolve) => {
        closeModal();

        const confirmLabel = confirmText || t('confirm') || 'Confirm';
        const cancelLabel = cancelText || t('cancel') || 'Cancel';

        const backdrop = document.createElement('div');
        backdrop.className = 'fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in';
        backdrop.setAttribute('role', 'dialog');
        backdrop.setAttribute('aria-modal', 'true');
        backdrop.setAttribute('aria-labelledby', 'prompt-title');
        backdrop.setAttribute('aria-describedby', 'prompt-description');

        backdrop.innerHTML = `
            <div class="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl max-w-md w-full transform animate-scale-in">
                <div class="p-6">
                    <div class="flex items-start gap-4">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-rose-400">
                            ${icon(iconName, 'w-5 h-5')}
                        </div>
                        <div class="flex-1 min-w-0">
                            <h3 id="prompt-title" class="text-lg font-semibold text-white">${escapeForHtml(title)}</h3>
                            <p id="prompt-description" class="mt-2 text-sm text-gray-400">${escapeForHtml(message)}</p>
                            <input type="${inputType}" id="prompt-input"
                                class="mt-4 w-full px-4 py-2.5 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                                placeholder="${escapeForHtml(placeholder)}"
                                value="${escapeForHtml(defaultValue)}"
                                autocomplete="${inputType === 'password' ? 'current-password' : 'off'}">
                        </div>
                    </div>
                </div>
                <div class="flex gap-3 p-4 bg-gray-900/50 rounded-b-xl border-t border-gray-700">
                    <button type="button" id="prompt-cancel"
                        class="flex-1 px-4 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-800">
                        ${escapeForHtml(cancelLabel)}
                    </button>
                    <button type="button" id="prompt-confirm"
                        class="flex-1 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-gray-800">
                        ${escapeForHtml(confirmLabel)}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(backdrop);
        activeModal = backdrop;
        refreshIcons();

        const inputEl = backdrop.querySelector('#prompt-input');
        const cancelBtn = backdrop.querySelector('#prompt-cancel');
        const confirmBtn = backdrop.querySelector('#prompt-confirm');

        // Focus input field
        inputEl.focus();
        inputEl.select();

        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                cleanup();
                resolve(null);
            } else if (e.key === 'Enter' && document.activeElement === inputEl) {
                cleanup();
                resolve(inputEl.value);
            } else if (e.key === 'Tab') {
                // Trap focus within modal
                const focusable = backdrop.querySelectorAll('input, button');
                const first = focusable[0];
                const last = focusable[focusable.length - 1];

                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        };

        const cleanup = () => {
            document.removeEventListener('keydown', handleKeydown);
            backdrop.classList.add('animate-fade-out');
            backdrop.querySelector('div').classList.add('animate-scale-out');
            setTimeout(() => {
                backdrop.remove();
                activeModal = null;
            }, 150);
        };

        document.addEventListener('keydown', handleKeydown);

        cancelBtn.addEventListener('click', () => {
            cleanup();
            resolve(null);
        });

        confirmBtn.addEventListener('click', () => {
            cleanup();
            resolve(inputEl.value);
        });

        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                cleanup();
                resolve(null);
            }
        });
    });
}

/**
 * Close active modal
 */
export function closeModal() {
    if (activeModal) {
        activeModal.remove();
        activeModal = null;
    }
}

/**
 * Simple HTML escape for modal content
 */
function escapeForHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// Make functions globally available for HTMX integration
window.showConfirm = showConfirm;
window.showAlert = showAlert;
window.showPrompt = showPrompt;
window.closeModal = closeModal;
