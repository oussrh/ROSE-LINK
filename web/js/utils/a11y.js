/**
 * ROSE Link - Accessibility Utilities
 *
 * Helper functions for implementing accessible UI patterns:
 * - Live region announcements for screen readers
 * - Focus management
 * - Keyboard navigation helpers
 * - ARIA attribute management
 *
 * @see https://www.w3.org/WAI/ARIA/apg/
 */

/**
 * ARIA live region element for screen reader announcements.
 * @type {HTMLElement|null}
 */
let liveRegion = null;

/**
 * Initialize the accessibility utilities.
 * Creates the live region for announcements.
 */
export function initA11y() {
    // Create live region for dynamic announcements
    if (!document.getElementById('a11y-live-region')) {
        liveRegion = document.createElement('div');
        liveRegion.id = 'a11y-live-region';
        liveRegion.setAttribute('role', 'status');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        // Visually hidden but available to screen readers
        liveRegion.className = 'sr-only';
        liveRegion.style.cssText = `
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        `;
        document.body.appendChild(liveRegion);
    } else {
        liveRegion = document.getElementById('a11y-live-region');
    }

    // Setup skip link functionality
    setupSkipLink();

    // Setup focus trap for modals
    setupModalFocusManagement();
}

/**
 * Announce a message to screen readers via live region.
 *
 * @param {string} message - The message to announce
 * @param {'polite'|'assertive'} [priority='polite'] - Announcement priority
 */
export function announce(message, priority = 'polite') {
    if (!liveRegion) {
        initA11y();
    }

    // Set priority
    liveRegion.setAttribute('aria-live', priority);

    // Clear and set message (this triggers the announcement)
    liveRegion.textContent = '';
    // Small delay to ensure screen readers detect the change
    setTimeout(() => {
        liveRegion.textContent = message;
    }, 50);
}

/**
 * Announce an assertive/urgent message (interrupts current speech).
 *
 * @param {string} message - The urgent message to announce
 */
export function announceUrgent(message) {
    announce(message, 'assertive');
}

/**
 * Announce loading state.
 *
 * @param {string} [context=''] - What is loading (e.g., "WiFi networks")
 */
export function announceLoading(context = '') {
    const message = context
        ? `Loading ${context}, please wait.`
        : 'Loading, please wait.';
    announce(message);
}

/**
 * Announce operation completion.
 *
 * @param {string} operation - What completed (e.g., "WiFi scan")
 * @param {boolean} [success=true] - Whether operation succeeded
 */
export function announceComplete(operation, success = true) {
    const status = success ? 'completed successfully' : 'failed';
    announce(`${operation} ${status}.`);
}

/**
 * Set up skip link functionality for keyboard navigation.
 */
function setupSkipLink() {
    const skipLink = document.getElementById('skip-link');
    if (!skipLink) return;

    skipLink.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById('main-content');
        if (target) {
            target.setAttribute('tabindex', '-1');
            target.focus();
            // Remove tabindex after focus to prevent it appearing in tab order
            target.addEventListener('blur', () => {
                target.removeAttribute('tabindex');
            }, { once: true });
        }
    });
}

/**
 * Set up focus management for modal dialogs.
 */
function setupModalFocusManagement() {
    // Setup wizard modal focus trap
    const wizardModal = document.getElementById('setup-wizard');
    if (wizardModal) {
        // Store last focused element when modal opens
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class') {
                    const isHidden = wizardModal.classList.contains('hidden');
                    if (!isHidden) {
                        // Modal opened - trap focus
                        trapFocus(wizardModal);
                    }
                }
            });
        });
        observer.observe(wizardModal, { attributes: true });
    }
}

/**
 * Trap focus within an element (for modal dialogs).
 *
 * @param {HTMLElement} element - Element to trap focus within
 * @returns {Function} Cleanup function to remove trap
 */
export function trapFocus(element) {
    const focusableSelector = [
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        'a[href]',
        '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const focusableElements = element.querySelectorAll(focusableSelector);
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    // Store previously focused element
    const previouslyFocused = document.activeElement;

    // Focus first element
    if (firstFocusable) {
        firstFocusable.focus();
    }

    // Handle Tab key
    const handleKeydown = (e) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
            // Shift+Tab: go to last if on first
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab: go to first if on last
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    };

    element.addEventListener('keydown', handleKeydown);

    // Return cleanup function
    return () => {
        element.removeEventListener('keydown', handleKeydown);
        // Restore focus to previous element
        if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
            previouslyFocused.focus();
        }
    };
}

/**
 * Release focus trap and restore previous focus.
 *
 * @param {HTMLElement} element - Element to release focus from
 * @param {HTMLElement} [returnFocus] - Element to return focus to
 */
export function releaseFocus(element, returnFocus) {
    if (returnFocus && typeof returnFocus.focus === 'function') {
        returnFocus.focus();
    }
}

/**
 * Check if reduced motion is preferred.
 *
 * @returns {boolean} True if user prefers reduced motion
 */
export function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check if high contrast mode is active.
 *
 * @returns {boolean} True if high contrast is enabled
 */
export function prefersHighContrast() {
    return window.matchMedia('(prefers-contrast: more)').matches;
}

/**
 * Add aria-describedby to form controls with validation.
 *
 * @param {HTMLFormElement} form - Form element to enhance
 */
export function enhanceFormAccessibility(form) {
    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach((input) => {
        // Find associated hint text
        const hintId = `${input.id}-hint`;
        const hint = document.getElementById(hintId);

        if (hint) {
            const describedBy = input.getAttribute('aria-describedby') || '';
            if (!describedBy.includes(hintId)) {
                input.setAttribute(
                    'aria-describedby',
                    describedBy ? `${describedBy} ${hintId}` : hintId
                );
            }
        }

        // Add required announcement
        if (input.required && !input.getAttribute('aria-required')) {
            input.setAttribute('aria-required', 'true');
        }
    });
}

/**
 * Set up keyboard shortcut handler.
 *
 * @param {Object.<string, Function>} shortcuts - Map of key combinations to handlers
 * @returns {Function} Cleanup function to remove listener
 */
export function setupKeyboardShortcuts(shortcuts) {
    const handler = (e) => {
        // Build key combination string
        const parts = [];
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        parts.push(e.key.toLowerCase());
        const combo = parts.join('+');

        if (shortcuts[combo]) {
            e.preventDefault();
            shortcuts[combo](e);
        }
    };

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
}

/**
 * Make an element draggable with keyboard support.
 *
 * @param {HTMLElement} element - Element to make draggable
 * @param {Object} options - Drag options
 */
export function makeKeyboardDraggable(element, options = {}) {
    const step = options.step || 10;

    element.setAttribute('role', 'button');
    element.setAttribute('tabindex', '0');
    element.setAttribute('aria-grabbed', 'false');

    element.addEventListener('keydown', (e) => {
        const rect = element.getBoundingClientRect();

        switch (e.key) {
            case 'ArrowUp':
                e.preventDefault();
                element.style.top = `${rect.top - step}px`;
                break;
            case 'ArrowDown':
                e.preventDefault();
                element.style.top = `${rect.top + step}px`;
                break;
            case 'ArrowLeft':
                e.preventDefault();
                element.style.left = `${rect.left - step}px`;
                break;
            case 'ArrowRight':
                e.preventDefault();
                element.style.left = `${rect.left + step}px`;
                break;
        }
    });
}

// Export default initialization
export default {
    initA11y,
    announce,
    announceUrgent,
    announceLoading,
    announceComplete,
    trapFocus,
    releaseFocus,
    prefersReducedMotion,
    prefersHighContrast,
    enhanceFormAccessibility,
    setupKeyboardShortcuts,
};
