/**
 * ROSE Link - System Component
 * Handles system info display and settings
 */

import { escapeHtml, setButtonLoading, spinnerSvg } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';

// Reboot state tracking
let isRebooting = false;
let rebootCheckInterval = null;

/**
 * Render system information
 * @param {Object} data - System info data from API
 */
export function renderSystemInfo(data) {
    const container = document.getElementById('system-info');
    if (!container) return;

    const uptimeHours = Math.floor(data.uptime_seconds / 3600);
    const uptimeMinutes = Math.floor((data.uptime_seconds % 3600) / 60);

    // Escape all user-controlled/API data to prevent XSS
    const modelShort = escapeHtml(data.model_short || data.model || t('unknown'));
    const architecture = escapeHtml(data.architecture || t('unknown'));
    const ramFree = parseInt(data.ram_free_mb) || 0;
    const ramTotal = parseInt(data.ram_mb) || 0;
    const diskFree = parseInt(data.disk_free_gb) || 0;
    const diskTotal = parseInt(data.disk_total_gb) || 0;
    const cpuTemp = parseInt(data.cpu_temp_c) || 0;

    container.innerHTML = `
        <div class="space-y-2 sm:space-y-3 text-sm">
            <div class="grid grid-cols-2 gap-2">
                <div class="bg-gray-700 rounded p-2 sm:p-3">
                    <div class="text-gray-400 text-xs">${t('model')}</div>
                    <div class="font-medium text-sm truncate">${modelShort}</div>
                </div>
                <div class="bg-gray-700 rounded p-2 sm:p-3">
                    <div class="text-gray-400 text-xs">${t('architecture')}</div>
                    <div class="font-medium text-sm">${architecture}</div>
                </div>
            </div>

            <div class="grid grid-cols-3 gap-2">
                <div class="bg-gray-700 rounded p-2 sm:p-3">
                    <div class="text-gray-400 text-xs">${t('ram')}</div>
                    <div class="font-medium text-xs sm:text-sm">${ramFree}/${ramTotal}MB</div>
                </div>
                <div class="bg-gray-700 rounded p-2 sm:p-3">
                    <div class="text-gray-400 text-xs">${t('disk')}</div>
                    <div class="font-medium text-xs sm:text-sm">${diskFree}/${diskTotal}GB</div>
                </div>
                <div class="bg-gray-700 rounded p-2 sm:p-3">
                    <div class="text-gray-400 text-xs">${t('cpu')}</div>
                    <div class="font-medium text-xs sm:text-sm ${cpuTemp > 70 ? 'text-orange-400' : ''}">${cpuTemp}°C</div>
                </div>
            </div>

            <div class="bg-gray-700 rounded p-2 sm:p-3">
                <div class="text-gray-400 text-xs mb-1">${t('wifi_capabilities')}</div>
                <div class="flex gap-1 flex-wrap">
                    ${data.wifi_capabilities?.supports_5ghz ? '<span class="px-2 py-0.5 bg-green-900 text-green-300 rounded text-xs">5GHz</span>' : '<span class="px-2 py-0.5 bg-gray-600 text-gray-400 rounded text-xs">5GHz</span>'}
                    ${data.wifi_capabilities?.supports_ac ? '<span class="px-2 py-0.5 bg-green-900 text-green-300 rounded text-xs">AC</span>' : ''}
                    ${data.wifi_capabilities?.supports_ax ? '<span class="px-2 py-0.5 bg-green-900 text-green-300 rounded text-xs">AX</span>' : ''}
                    ${data.wifi_capabilities?.ap_mode ? '<span class="px-2 py-0.5 bg-green-900 text-green-300 rounded text-xs">AP</span>' : ''}
                </div>
            </div>

            <div class="text-xs text-gray-500">
                ${t('uptime')}: ${uptimeHours}h ${uptimeMinutes}m
            </div>
        </div>
    `;
}

/**
 * Initialize VPN settings form
 */
export function initVPNSettingsForm() {
    const form = document.getElementById('vpn-settings-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const btn = document.getElementById('vpn-settings-submit-btn');
        const formData = new FormData(e.target);
        const data = {
            ping_host: formData.get('ping_host'),
            check_interval: parseInt(formData.get('check_interval'))
        };

        setButtonLoading(btn, true);
        fetch('/api/system/settings/vpn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(r => {
                if (r.ok) return r.json();
                return r.json().then(data => Promise.reject(data));
            })
            .then(() => {
                showToast(t('vpn_settings_saved'), 'success');
            })
            .catch((err) => {
                // Escape error message from server to prevent XSS
                const serverMsg = err.detail ? escapeHtml(String(err.detail)) : null;
                const msg = serverMsg || t('settings_save_failed');
                showToast(msg, 'error');
            })
            .finally(() => setButtonLoading(btn, false));
    });
}

/**
 * Get the reboot button element
 * @returns {HTMLElement|null}
 */
function getRebootButton() {
    return document.querySelector('button[hx-post="/api/system/reboot"]');
}

/**
 * Set reboot button to rebooting state
 * @param {HTMLElement} button - The reboot button
 */
function setRebootingState(button) {
    if (!button) return;

    isRebooting = true;
    button.disabled = true;
    button.dataset.originalContent = button.innerHTML;
    button.innerHTML = `${spinnerSvg} <span>${t('rebooting') || 'Rebooting...'}</span>`;
    button.classList.add('opacity-75', 'cursor-not-allowed');
}

/**
 * Restore reboot button to original state
 * @param {HTMLElement} button - The reboot button
 */
function restoreRebootButton(button) {
    if (!button) return;

    isRebooting = false;
    button.disabled = false;
    if (button.dataset.originalContent) {
        button.innerHTML = button.dataset.originalContent;
        delete button.dataset.originalContent;
    }
    button.classList.remove('opacity-75', 'cursor-not-allowed');

    // Refresh icons since we restored the original content
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Check if system is back online after reboot
 * @returns {Promise<boolean>}
 */
async function checkSystemOnline() {
    try {
        const response = await fetch('/api/status', {
            method: 'GET',
            cache: 'no-store',
            signal: AbortSignal.timeout(3000)
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Start polling to detect when system comes back online
 */
function startRebootPolling() {
    const button = getRebootButton();
    let attempts = 0;
    const maxAttempts = 60; // 2 minutes max (2s interval)

    // Clear any existing interval
    if (rebootCheckInterval) {
        clearInterval(rebootCheckInterval);
    }

    rebootCheckInterval = setInterval(async () => {
        attempts++;

        const online = await checkSystemOnline();

        if (online) {
            clearInterval(rebootCheckInterval);
            rebootCheckInterval = null;
            restoreRebootButton(button);
            showToast(t('reboot_complete') || 'Reboot completed successfully', 'success');

            // Trigger a refresh of status cards
            setTimeout(() => {
                if (typeof htmx !== 'undefined') {
                    htmx.trigger('#status-cards', 'htmx:load');
                }
            }, 1000);
        } else if (attempts >= maxAttempts) {
            clearInterval(rebootCheckInterval);
            rebootCheckInterval = null;
            restoreRebootButton(button);
            showToast(t('reboot_timeout') || 'Reboot timed out - system may still be starting', 'warning');
        }
    }, 2000);
}

/**
 * Handle reboot action
 * Called after HTMX request is issued
 */
export function handleRebootAction() {
    const button = getRebootButton();
    setRebootingState(button);

    // Start polling after a short delay to allow the reboot to begin
    setTimeout(() => {
        startRebootPolling();
    }, 5000);
}

/**
 * Initialize reboot button handler
 * Intercepts HTMX afterRequest to handle reboot response
 */
export function initRebootHandler() {
    document.body.addEventListener('htmx:afterRequest', (event) => {
        const el = event.detail.elt;

        // Check if this is the reboot button
        if (el && el.getAttribute('hx-post') === '/api/system/reboot') {
            const xhr = event.detail.xhr;

            // Only handle successful requests
            if (xhr && xhr.status === 200) {
                handleRebootAction();
            } else if (xhr && xhr.status !== 200) {
                // Show error toast for failed reboot
                showToast(t('reboot_failed') || 'Failed to initiate reboot', 'error');
            }
        }
    });
}

/**
 * Set a button to loading state with custom text
 * @param {HTMLElement} button - The button element
 * @param {string} loadingText - Text to show while loading
 */
function setButtonLoadingState(button, loadingText) {
    if (!button) return;

    button.disabled = true;
    button.dataset.originalContent = button.innerHTML;
    button.innerHTML = `${spinnerSvg} <span>${loadingText}</span>`;
    button.classList.add('opacity-75', 'cursor-not-allowed');
}

/**
 * Restore a button from loading state
 * @param {HTMLElement} button - The button element
 */
function restoreButtonState(button) {
    if (!button) return;

    button.disabled = false;
    if (button.dataset.originalContent) {
        button.innerHTML = button.dataset.originalContent;
        delete button.dataset.originalContent;
    }
    button.classList.remove('opacity-75', 'cursor-not-allowed');

    // Refresh icons since we restored the original content
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Initialize service restart button handlers (VPN and Hotspot)
 * Adds loading states and toast notifications for these buttons
 */
export function initServiceRestartHandlers() {
    // Handle before request - show loading state
    document.body.addEventListener('htmx:beforeRequest', (event) => {
        const el = event.detail.elt;
        const hxPost = el?.getAttribute('hx-post');

        if (hxPost === '/api/vpn/restart') {
            setButtonLoadingState(el, t('restarting') || 'Restarting...');
        } else if (hxPost === '/api/hotspot/restart') {
            setButtonLoadingState(el, t('restarting') || 'Restarting...');
        }
    });

    // Handle after request - show result and restore button
    document.body.addEventListener('htmx:afterRequest', (event) => {
        const el = event.detail.elt;
        const hxPost = el?.getAttribute('hx-post');
        const xhr = event.detail.xhr;

        if (hxPost === '/api/vpn/restart') {
            restoreButtonState(el);

            if (xhr && xhr.status === 200) {
                showToast(t('vpn_restarted') || 'VPN restarted', 'success');
                // Clear the message container after showing toast
                clearMessageContainer('system-action-message');
            } else {
                const errorMsg = parseErrorMessage(xhr) || t('vpn_restart_failed') || 'Failed to restart VPN';
                showToast(errorMsg, 'error');
                clearMessageContainer('system-action-message');
            }
        } else if (hxPost === '/api/hotspot/restart') {
            restoreButtonState(el);

            if (xhr && xhr.status === 200) {
                showToast(t('hotspot_restarted') || 'Hotspot restarted', 'success');
                // Clear the message container after showing toast
                clearMessageContainer('system-action-message');
            } else {
                const errorMsg = parseErrorMessage(xhr) || t('hotspot_restart_failed') || 'Failed to restart hotspot';
                showToast(errorMsg, 'error');
                clearMessageContainer('system-action-message');
            }
        }
    });
}

/**
 * Parse error message from XHR response
 * @param {XMLHttpRequest} xhr - The XMLHttpRequest object
 * @returns {string|null} Error message or null
 */
function parseErrorMessage(xhr) {
    if (!xhr || !xhr.responseText) return null;

    try {
        const data = JSON.parse(xhr.responseText);
        return data.detail || null;
    } catch {
        // If not JSON, return the raw text if it looks like an error message
        const text = xhr.responseText.trim();
        if (text && text.length < 200) {
            return text;
        }
        return null;
    }
}

/**
 * Clear the system action message container
 * @param {string} containerId - ID of the message container
 */
function clearMessageContainer(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}

