/**
 * ROSE Link - VPN Component
 * Handles VPN status, profiles, and operations
 */

import { escapeHtml, icon, refreshIcons, setButtonLoading } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';
import { showConfirm } from '../utils/modal.js';

/**
 * Render VPN status details
 * @param {Object} data - VPN status data from API
 */
export function renderVPNStatus(data) {
    const container = document.getElementById('vpn-status-detail');
    if (!container) return;

    // Update the control buttons based on VPN state
    updateVPNButtons(data.active);

    if (!data.active) {
        container.innerHTML = `
            <div class="bg-gray-700 rounded-lg p-4">
                <div class="flex items-center gap-2 text-red-400">
                    <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span class="font-medium">${t('vpn_inactive')}</span>
                </div>
                <p class="text-sm text-gray-400 mt-2">${t('import_profile_hint')}</p>
            </div>
        `;
        return;
    }

    // Escape all API data to prevent XSS
    const endpoint = data.endpoint ? escapeHtml(data.endpoint) : '';
    const handshake = data.latest_handshake ? escapeHtml(data.latest_handshake) : '';
    const received = escapeHtml(data.transfer?.received || '0 B');
    const sent = escapeHtml(data.transfer?.sent || '0 B');

    container.innerHTML = `
        <div class="bg-gray-700 rounded-lg p-4 space-y-2">
            <div class="flex items-center gap-2 text-green-400">
                <div class="w-3 h-3 bg-green-500 rounded-full pulse-slow"></div>
                <span class="font-medium">${t('vpn_active')}</span>
            </div>
            ${endpoint ? `<p class="text-sm"><strong>${t('endpoint')}:</strong> ${endpoint}</p>` : ''}
            ${handshake ? `<p class="text-sm"><strong>${t('last_handshake')}:</strong> ${handshake}</p>` : ''}
            <p class="text-sm"><strong>${t('transfer')}:</strong> ↓ ${received} | ↑ ${sent}</p>
        </div>
    `;
}

/**
 * Update VPN control buttons based on active state
 * @param {boolean} isActive - Whether VPN is currently active
 */
function updateVPNButtons(isActive) {
    const btnRestart = document.getElementById('vpn-btn-restart');
    const btnStop = document.getElementById('vpn-btn-stop');
    const btnStart = document.getElementById('vpn-btn-start');

    if (btnRestart) btnRestart.classList.toggle('hidden', !isActive);
    if (btnStop) btnStop.classList.toggle('hidden', !isActive);
    if (btnStart) btnStart.classList.toggle('hidden', isActive);
}

/**
 * Render VPN profiles list
 * @param {Array} profiles - Array of VPN profile objects
 */
export function renderVPNProfiles(profiles) {
    const container = document.getElementById('vpn-profiles');
    if (!container) return;

    if (!profiles || profiles.length === 0) {
        container.innerHTML = `<div class="mt-4 p-4 bg-gray-700 rounded-lg text-sm text-gray-400">${t('no_profiles')}</div>`;
        return;
    }

    container.innerHTML = profiles.map(prof => {
        const safeName = escapeHtml(prof.name);
        return `
        <div class="bg-gray-700 rounded-lg p-3 mb-2 flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0 flex-1">
                <div class="w-2 h-2 ${prof.active ? 'bg-green-500 pulse-slow' : 'bg-gray-500'} rounded-full flex-shrink-0"></div>
                <span class="font-medium truncate">${safeName}</span>
            </div>
            <div class="flex gap-2 flex-shrink-0">
                ${!prof.active
        ? `<button data-action="activate-vpn" data-name="${safeName}" class="px-3 py-1 bg-rose-600 hover:bg-rose-700 rounded text-sm transition-smooth focus-ring touch-manipulation">${t('activate')}</button>
                       <button data-action="delete-vpn" data-name="${safeName}" class="px-2 py-1 bg-red-800 hover:bg-red-700 rounded text-sm transition-smooth focus-ring touch-manipulation flex items-center" title="${t('delete')}">${icon('trash-2')}</button>`
        : `<span class="text-xs text-green-400 px-2">${t('active')}</span>`}
            </div>
        </div>
    `;}).join('');
    refreshIcons();
}

/**
 * Activate a VPN profile
 * @param {string} name - Profile name
 * @param {HTMLElement} btn - Button element
 */
export function activateProfile(name, btn) {
    setButtonLoading(btn, true);
    fetch('/api/vpn/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    })
        .then(r => {
            if (r.ok) return r.json();
            return r.json().then(data => Promise.reject(data));
        })
        .then(() => {
            showToast(`${t('vpn_activated')}: ${escapeHtml(name)}`, 'success');
            htmx.trigger('#vpn-profiles', 'htmx:load');
            htmx.trigger('#vpn-status-detail', 'htmx:load');
        })
        .catch((err) => {
            // Escape error message from server to prevent XSS
            const serverMsg = err.detail ? escapeHtml(String(err.detail)) : null;
            const msg = serverMsg || t('activation_failed');
            showToast(msg, 'error');
        })
        .finally(() => setButtonLoading(btn, false));
}

/**
 * Delete a VPN profile
 * @param {string} name - Profile name
 * @param {HTMLElement} btn - Button element
 */
export async function deleteProfile(name, btn) {
    const confirmed = await showConfirm({
        title: t('delete_profile') || 'Delete Profile',
        message: `${t('confirm_delete')} "${name}"?`,
        confirmText: t('delete') || 'Delete',
        cancelText: t('cancel') || 'Cancel',
        variant: 'danger',
        icon: 'trash-2'
    });

    if (!confirmed) return;

    setButtonLoading(btn, true);
    fetch(`/api/vpn/profiles/${encodeURIComponent(name)}`, { method: 'DELETE' })
        .then(r => {
            if (r.ok) return r.json();
            return r.json().then(data => Promise.reject(data));
        })
        .then(() => {
            showToast(`${t('deleted')}: ${escapeHtml(name)}`, 'success');
            htmx.trigger('#vpn-profiles', 'htmx:load');
        })
        .catch((err) => {
            // Escape error message from server to prevent XSS
            const serverMsg = err.detail ? escapeHtml(String(err.detail)) : null;
            const msg = serverMsg || t('delete_failed');
            showToast(msg, 'error');
        })
        .finally(() => setButtonLoading(btn, false));
}

/**
 * Load VPN settings into form
 */
export async function loadVPNSettings() {
    try {
        const response = await fetch('/api/system/settings/vpn');
        if (response.ok) {
            const data = await response.json();
            const pingHost = document.getElementById('vpn-ping-host');
            const checkInterval = document.getElementById('vpn-check-interval');
            if (pingHost) pingHost.value = data.ping_host || '8.8.8.8';
            if (checkInterval) checkInterval.value = data.check_interval || 60;
        }
    } catch {
        console.warn('Could not load VPN settings');
    }
}

/**
 * Initialize VPN event delegation
 * Call this once from main.js to set up click handlers
 */
export function initVPNEvents() {
    document.addEventListener('click', (e) => {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;

        if (action === 'activate-vpn') {
            const name = target.dataset.name;
            if (name) {
                activateProfile(name, target);
            }
        } else if (action === 'delete-vpn') {
            const name = target.dataset.name;
            if (name) {
                deleteProfile(name, target);
            }
        }
    });
}

/**
 * Initialize VPN import form handler
 * Handles file upload with loading state and toast notifications
 */
export function initVPNImportForm() {
    const form = document.querySelector('form[hx-post="/api/vpn/import"]');
    if (!form) return;

    // Remove HTMX handling - we'll handle it with JS for better UX
    form.removeAttribute('hx-post');
    form.removeAttribute('hx-encoding');
    form.removeAttribute('hx-target');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fileInput = form.querySelector('input[type="file"]');
        const submitBtn = form.querySelector('button[type="submit"]');

        if (!fileInput?.files?.length) {
            showToast(t('select_file') || 'Please select a file', 'error');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        // Show loading state
        setButtonLoading(submitBtn, true);

        try {
            const response = await fetch('/api/vpn/import', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                const profileName = data.name || file.name;
                showToast(`${t('upload_success')}: ${escapeHtml(profileName)}`, 'success');

                // Clear file input
                fileInput.value = '';

                // Refresh profiles list
                if (typeof htmx !== 'undefined') {
                    htmx.trigger('#vpn-profiles', 'htmx:load');
                    htmx.trigger('#vpn-status-detail', 'htmx:load');
                }
            } else {
                // Parse error response
                let errorMsg = t('upload_failed') || 'Upload failed';
                try {
                    const text = await response.text();
                    const data = JSON.parse(text);
                    if (data.detail) {
                        errorMsg = typeof data.detail === 'string'
                            ? data.detail
                            : JSON.stringify(data.detail);
                    }
                } catch {
                    // Use default error message
                }
                showToast(errorMsg, 'error');
            }
        } catch (err) {
            showToast(t('upload_failed') || 'Upload failed', 'error');
        } finally {
            setButtonLoading(submitBtn, false);
        }
    });
}

/**
 * Render VPN action result (start/stop/restart success)
 * @param {Object} data - Response data from API
 */
export function renderVPNActionResult(data) {
    const container = document.getElementById('vpn-message');
    if (!container) return;

    const status = data.status || '';
    let message = '';
    let iconName = 'check-circle';

    switch (status) {
        case 'started':
            message = t('vpn_started') || 'VPN started successfully';
            break;
        case 'stopped':
            message = t('vpn_stopped') || 'VPN stopped';
            break;
        case 'restarted':
            message = t('vpn_restarted') || 'VPN restarted successfully';
            break;
        default:
            message = t('operation_successful') || 'Operation successful';
    }

    container.innerHTML = `
        <div class="p-3 bg-green-900/50 border border-green-700 rounded-lg text-green-200 text-sm flex items-center gap-2">
            <i data-lucide="${iconName}" class="w-4 h-4 flex-shrink-0"></i>
            <span>${escapeHtml(message)}</span>
        </div>`;

    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Refresh VPN status after action
    setTimeout(() => {
        htmx.trigger('#vpn-status-detail', 'htmx:load');
    }, 1000);

    // Clear message after 5 seconds
    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}
