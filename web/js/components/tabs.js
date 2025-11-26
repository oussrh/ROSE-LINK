/**
 * ROSE Link - Tab Navigation Component
 * Handles tab switching and state persistence
 */

/**
 * Show a specific tab
 * @param {string} tabName - Tab identifier (wifi, vpn, hotspot, system)
 */
export function showTab(tabName) {
    // Hide all tabs and reset button styles
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-rose-500', 'text-rose-500');
        btn.classList.add('border-transparent', 'text-gray-400');
        btn.setAttribute('aria-selected', 'false');
    });

    // Show selected tab
    const content = document.getElementById('content-' + tabName);
    const btn = document.getElementById('tab-' + tabName);

    if (content) content.classList.remove('hidden');
    if (btn) {
        btn.classList.add('border-rose-500', 'text-rose-500');
        btn.classList.remove('border-transparent', 'text-gray-400');
        btn.setAttribute('aria-selected', 'true');
    }

    // Save to localStorage
    localStorage.setItem('rose-tab', tabName);
}

/**
 * Restore the last active tab from localStorage
 */
export function restoreLastTab() {
    const savedTab = localStorage.getItem('rose-tab');
    if (savedTab) {
        showTab(savedTab);
    }
}

/**
 * Initialize tab navigation
 */
export function initTabs() {
    restoreLastTab();
}

// Make showTab globally available for onclick handlers
window.showTab = showTab;
