/**
 * ROSE Link - VPN Component
 * Handles VPN status, profiles, and operations
 */

import { escapeHtml, escapeJs, icon, refreshIcons, setButtonLoading } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';

/**
 * Render VPN status details
 * @param {Object} data - VPN status data from API
 */
export function renderVPNStatus(data) {
    const container = document.getElementById('vpn-status-detail');
    if (!container) return;

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
        const jsName = escapeJs(prof.name);
        return `
        <div class="bg-gray-700 rounded-lg p-3 mb-2 flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0 flex-1">
                <div class="w-2 h-2 ${prof.active ? 'bg-green-500 pulse-slow' : 'bg-gray-500'} rounded-full flex-shrink-0"></div>
                <span class="font-medium truncate">${safeName}</span>
            </div>
            <div class="flex gap-2 flex-shrink-0">
                ${!prof.active
        ? `<button onclick="activateProfile('${jsName}', this)" class="px-3 py-1 bg-rose-600 hover:bg-rose-700 rounded text-sm transition-smooth focus-ring touch-manipulation">${t('activate')}</button>
                       <button onclick="deleteProfile('${jsName}', this)" class="px-2 py-1 bg-red-800 hover:bg-red-700 rounded text-sm transition-smooth focus-ring touch-manipulation flex items-center" title="${t('delete')}">${icon('trash-2')}</button>`
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
            const msg = err.detail || t('activation_failed');
            showToast(msg, 'error');
        })
        .finally(() => setButtonLoading(btn, false));
}

/**
 * Delete a VPN profile
 * @param {string} name - Profile name
 * @param {HTMLElement} btn - Button element
 */
export function deleteProfile(name, btn) {
    if (!confirm(`${t('confirm_delete')} "${name}"?`)) {
        return;
    }

    setButtonLoading(btn, true);
    fetch(`/api/vpn/profiles/${encodeURIComponent(name)}`, { method: 'DELETE' })
        .then(r => {
            if (r.ok) return r.json();
            return r.json().then(data => Promise.reject(data));
        })
        .then(() => {
            showToast(`${t('deleted')}: ${name}`, 'success');
            htmx.trigger('#vpn-profiles', 'htmx:load');
        })
        .catch((err) => {
            const msg = err.detail || t('delete_failed');
            showToast(msg, 'error');
        })
        .finally(() => setButtonLoading(btn, false));
}

/**
 * Load VPN settings into form
 */
export async function loadVPNSettings() {
    try {
        const response = await fetch('/api/settings/vpn');
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

// Make functions globally available for onclick handlers
window.activateProfile = activateProfile;
window.deleteProfile = deleteProfile;
