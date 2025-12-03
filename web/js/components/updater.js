/**
 * ROSE Link - Update Notification Component
 * Checks for updates and provides UI for triggering updates
 */

import { t } from '../i18n.js';
import { icon, refreshIcons } from '../utils/dom.js';

// Check for updates every 6 hours
const UPDATE_CHECK_INTERVAL = 6 * 60 * 60 * 1000;

// Poll update status every 2 seconds during update
const UPDATE_STATUS_INTERVAL = 2000;

let updateCheckTimer = null;
let updateStatusTimer = null;

/**
 * Initialize the updater - check for updates on load and periodically
 */
export function initUpdater() {
    // Check for updates after a short delay (let other things load first)
    setTimeout(checkForUpdates, 5000);

    // Set up periodic checks
    updateCheckTimer = setInterval(checkForUpdates, UPDATE_CHECK_INTERVAL);
}

/**
 * Check for available updates
 */
export async function checkForUpdates() {
    try {
        const response = await fetch('/api/system/version');
        if (!response.ok) return;

        const data = await response.json();

        if (data.update_available) {
            showUpdateNotification(data.current_version, data.latest_version);
        } else {
            hideUpdateNotification();
        }
    } catch (error) {
        console.error('Failed to check for updates:', error);
    }
}

/**
 * Show the update notification banner
 */
function showUpdateNotification(currentVersion, latestVersion) {
    // Remove existing notification if any
    hideUpdateNotification();

    const notification = document.createElement('div');
    notification.id = 'update-notification';
    notification.className = 'fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-3 shadow-lg transform transition-transform duration-300';
    notification.innerHTML = `
        <div class="container mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div class="flex items-center gap-3">
                <span class="flex items-center gap-2">
                    ${icon('download-cloud', 'w-5 h-5')}
                    <span class="font-medium" data-i18n="update_available">${t('update_available')}</span>
                </span>
                <span class="text-blue-200 text-sm">
                    v${currentVersion} → v${latestVersion}
                </span>
            </div>
            <div class="flex items-center gap-2">
                <button id="update-now-btn" class="bg-white text-blue-700 px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors flex items-center gap-2">
                    ${icon('download', 'w-4 h-4')}
                    <span data-i18n="update_now">${t('update_now')}</span>
                </button>
                <button id="update-dismiss-btn" class="text-blue-200 hover:text-white p-1.5 rounded-lg hover:bg-blue-500/30 transition-colors">
                    ${icon('x', 'w-5 h-5')}
                </button>
            </div>
        </div>
    `;

    // Insert at the top of the body
    document.body.insertBefore(notification, document.body.firstChild);

    // Add padding to main content to prevent overlap
    document.body.style.paddingTop = notification.offsetHeight + 'px';

    // Refresh icons
    refreshIcons();

    // Add event listeners
    document.getElementById('update-now-btn').addEventListener('click', startUpdate);
    document.getElementById('update-dismiss-btn').addEventListener('click', () => {
        hideUpdateNotification();
        // Don't check again for 1 hour after dismissing
        if (updateCheckTimer) clearInterval(updateCheckTimer);
        updateCheckTimer = setInterval(checkForUpdates, 60 * 60 * 1000);
    });
}

/**
 * Hide the update notification
 */
function hideUpdateNotification() {
    const notification = document.getElementById('update-notification');
    if (notification) {
        notification.remove();
        document.body.style.paddingTop = '0';
    }
}

/**
 * Start the update process
 */
async function startUpdate() {
    const btn = document.getElementById('update-now-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span data-i18n="updating">${t('updating')}</span>
        `;
    }

    try {
        const response = await fetch('/api/system/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error('Failed to start update');
        }

        const data = await response.json();

        if (data.status === 'started' || data.status === 'already_running') {
            showUpdateProgress();
            startUpdateStatusPolling();
        } else {
            showUpdateError(data.message || 'Failed to start update');
        }
    } catch (error) {
        console.error('Update failed:', error);
        showUpdateError(error.message);
    }
}

/**
 * Show the update progress modal
 */
function showUpdateProgress() {
    // Remove notification
    hideUpdateNotification();

    // Create modal
    const modal = document.createElement('div');
    modal.id = 'update-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/70';
    modal.innerHTML = `
        <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <div class="text-center">
                <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-500/20 flex items-center justify-center">
                    ${icon('download-cloud', 'w-8 h-8 text-blue-400')}
                </div>
                <h3 class="text-xl font-bold text-white mb-2" data-i18n="updating_rose_link">${t('updating_rose_link')}</h3>
                <p id="update-status-message" class="text-gray-400 mb-4" data-i18n="downloading_update">${t('downloading_update')}</p>

                <div class="w-full bg-gray-700 rounded-full h-3 mb-4">
                    <div id="update-progress-bar" class="bg-blue-500 h-3 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>

                <p class="text-sm text-gray-500" data-i18n="do_not_close">${t('do_not_close')}</p>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    refreshIcons();
}

/**
 * Update the progress modal with current status
 */
function updateProgressModal(status, message, progress) {
    const messageEl = document.getElementById('update-status-message');
    const progressBar = document.getElementById('update-progress-bar');

    if (messageEl) messageEl.textContent = message;
    if (progressBar) progressBar.style.width = `${progress}%`;

    if (status === 'complete') {
        stopUpdateStatusPolling();
        showUpdateComplete();
    } else if (status === 'error') {
        stopUpdateStatusPolling();
        showUpdateError(message);
    }
}

/**
 * Show update complete message
 */
function showUpdateComplete() {
    const modal = document.getElementById('update-modal');
    if (modal) {
        modal.innerHTML = `
            <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
                <div class="text-center">
                    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
                        ${icon('check-circle', 'w-8 h-8 text-green-400')}
                    </div>
                    <h3 class="text-xl font-bold text-white mb-2" data-i18n="update_complete">${t('update_complete')}</h3>
                    <p class="text-gray-400 mb-6" data-i18n="update_complete_message">${t('update_complete_message')}</p>

                    <button onclick="location.reload()" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                        ${icon('refresh-cw', 'w-4 h-4 inline mr-2')}
                        <span data-i18n="reload_page">${t('reload_page')}</span>
                    </button>
                </div>
            </div>
        `;
        refreshIcons();
    }
}

/**
 * Show update error message
 */
function showUpdateError(message) {
    const modal = document.getElementById('update-modal');
    if (modal) {
        modal.innerHTML = `
            <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
                <div class="text-center">
                    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                        ${icon('alert-circle', 'w-8 h-8 text-red-400')}
                    </div>
                    <h3 class="text-xl font-bold text-white mb-2" data-i18n="update_failed">${t('update_failed')}</h3>
                    <p class="text-gray-400 mb-6">${message}</p>

                    <div class="flex gap-3 justify-center">
                        <button onclick="document.getElementById('update-modal').remove()" class="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <span data-i18n="close">${t('close')}</span>
                        </button>
                        <button onclick="location.reload()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <span data-i18n="retry">${t('retry')}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
        refreshIcons();
    } else {
        // No modal, show notification banner notification
        hideUpdateNotification();
    }
}

/**
 * Start polling for update status
 */
function startUpdateStatusPolling() {
    updateStatusTimer = setInterval(async () => {
        try {
            const response = await fetch('/api/system/update/status');
            if (!response.ok) return;

            const data = await response.json();
            updateProgressModal(data.status, data.message, data.progress);
        } catch (error) {
            console.error('Failed to get update status:', error);
        }
    }, UPDATE_STATUS_INTERVAL);
}

/**
 * Stop polling for update status
 */
function stopUpdateStatusPolling() {
    if (updateStatusTimer) {
        clearInterval(updateStatusTimer);
        updateStatusTimer = null;
    }
}

/**
 * Cleanup on page unload
 */
export function cleanupUpdater() {
    if (updateCheckTimer) clearInterval(updateCheckTimer);
    if (updateStatusTimer) clearInterval(updateStatusTimer);
}
