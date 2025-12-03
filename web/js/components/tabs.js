/**
 * ROSE Link - Tab Navigation Component
 * Handles tab switching, state persistence, and keyboard navigation
 *
 * Accessibility features:
 * - Full keyboard navigation with arrow keys
 * - ARIA attributes for screen readers
 * - Focus management following WAI-ARIA Tab Pattern
 */

// Tab order for keyboard navigation
const TAB_ORDER = ['wifi', 'vpn', 'hotspot', 'adguard', 'system'];

/**
 * Show a specific tab
 * @param {string} tabName - Tab identifier (wifi, vpn, hotspot, system)
 * @param {boolean} focus - Whether to focus the tab button (default: false)
 */
export function showTab(tabName, focus = false) {
    // Validate tab name
    if (!TAB_ORDER.includes(tabName)) {
        return;
    }

    // Hide all tabs and reset button styles
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-rose-500', 'text-rose-500');
        btn.classList.add('border-transparent', 'text-gray-400');
        btn.setAttribute('aria-selected', 'false');
        btn.setAttribute('tabindex', '-1');
    });

    // Show selected tab
    const content = document.getElementById('content-' + tabName);
    const btn = document.getElementById('tab-' + tabName);

    if (content) content.classList.remove('hidden');
    if (btn) {
        btn.classList.add('border-rose-500', 'text-rose-500');
        btn.classList.remove('border-transparent', 'text-gray-400');
        btn.setAttribute('aria-selected', 'true');
        btn.setAttribute('tabindex', '0');

        // Focus the button if requested (for keyboard navigation)
        if (focus) {
            btn.focus();
        }
    }

    // Save to localStorage
    localStorage.setItem('rose-tab', tabName);
}

/**
 * Navigate to the next tab
 * @param {string} currentTab - Current tab identifier
 * @returns {string} Next tab identifier
 */
function getNextTab(currentTab) {
    const currentIndex = TAB_ORDER.indexOf(currentTab);
    const nextIndex = (currentIndex + 1) % TAB_ORDER.length;
    return TAB_ORDER[nextIndex];
}

/**
 * Navigate to the previous tab
 * @param {string} currentTab - Current tab identifier
 * @returns {string} Previous tab identifier
 */
function getPrevTab(currentTab) {
    const currentIndex = TAB_ORDER.indexOf(currentTab);
    const prevIndex = (currentIndex - 1 + TAB_ORDER.length) % TAB_ORDER.length;
    return TAB_ORDER[prevIndex];
}

/**
 * Get the currently active tab
 * @returns {string|null} Current tab identifier or null
 */
function getCurrentTab() {
    const activeBtn = document.querySelector('.tab-btn[aria-selected="true"]');
    if (activeBtn) {
        // Extract tab name from id (format: "tab-{name}")
        return activeBtn.id.replace('tab-', '');
    }
    return TAB_ORDER[0];
}

/**
 * Handle keyboard navigation for tabs
 * Implements WAI-ARIA Tab Pattern keyboard interactions
 * @param {KeyboardEvent} event - Keyboard event
 */
function handleTabKeydown(event) {
    const currentTab = getCurrentTab();

    switch (event.key) {
        case 'ArrowRight':
        case 'ArrowDown':
            // Move to next tab
            event.preventDefault();
            showTab(getNextTab(currentTab), true);
            break;

        case 'ArrowLeft':
        case 'ArrowUp':
            // Move to previous tab
            event.preventDefault();
            showTab(getPrevTab(currentTab), true);
            break;

        case 'Home':
            // Move to first tab
            event.preventDefault();
            showTab(TAB_ORDER[0], true);
            break;

        case 'End':
            // Move to last tab
            event.preventDefault();
            showTab(TAB_ORDER[TAB_ORDER.length - 1], true);
            break;
    }
}

/**
 * Restore the last active tab from localStorage
 */
export function restoreLastTab() {
    const savedTab = localStorage.getItem('rose-tab');
    if (savedTab && TAB_ORDER.includes(savedTab)) {
        showTab(savedTab);
    } else {
        // Default to first tab
        showTab(TAB_ORDER[0]);
    }
}

/**
 * Initialize tab navigation with keyboard support
 */
export function initTabs() {
    // Restore saved tab
    restoreLastTab();

    // Add keyboard navigation to tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('keydown', handleTabKeydown);
    });

    // Set initial tabindex values
    document.querySelectorAll('.tab-btn').forEach(btn => {
        const isSelected = btn.getAttribute('aria-selected') === 'true';
        btn.setAttribute('tabindex', isSelected ? '0' : '-1');
    });
}

// Make showTab globally available for onclick handlers
window.showTab = showTab;

// Export tab order for testing
export { TAB_ORDER };
