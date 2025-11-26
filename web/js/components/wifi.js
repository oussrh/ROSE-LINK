/**
 * ROSE Link - WiFi Component
 * Handles WiFi scanning, connection, and status display
 */

import { escapeHtml, icon, refreshIcons, setButtonLoading } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';

/**
 * Render available WiFi networks
 * Uses data attributes and event delegation for security (no inline onclick)
 * @param {Array} networks - Array of network objects
 */
export function renderWifiNetworks(networks) {
    const container = document.getElementById('wifi-networks');
    if (!container) return;

    if (!networks || networks.length === 0) {
        container.innerHTML = `<p class="text-gray-400">${t('no_networks')}</p>`;
        return;
    }

    container.innerHTML = networks.map(net => `
        <div class="bg-gray-700 rounded-lg p-3 sm:p-4 flex items-center justify-between gap-2">
            <div class="min-w-0 flex-1">
                <div class="font-medium truncate text-sm sm:text-base">${escapeHtml(net.ssid)}</div>
                <div class="text-xs sm:text-sm text-gray-400">${escapeHtml(net.security)} | ${net.signal}%</div>
            </div>
            <button data-action="connect-wifi" data-ssid="${escapeHtml(net.ssid)}"
                class="flex-shrink-0 px-2 sm:px-3 py-1 bg-rose-600 hover:bg-rose-700 rounded text-xs sm:text-sm transition-smooth focus-ring touch-manipulation">
                ${t('connect')}
            </button>
        </div>
    `).join('');
}

/**
 * Render current WiFi status
 * @param {Object} data - Status data from API
 */
export function renderWifiCurrentStatus(data) {
    const container = document.getElementById('wifi-current-status');
    if (!container) return;

    const wan = data.wan;
    const ethConnected = wan.ethernet?.connected;
    const wifiConnected = wan.wifi?.connected;

    if (ethConnected) {
        const ethIp = escapeHtml(wan.ethernet?.ip || '');
        container.innerHTML = `
            <div class="bg-green-900/30 border border-green-700 rounded-lg p-3">
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                        <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span class="font-medium">${t('ethernet_connected')}</span>
                    </div>
                    <span class="text-sm text-gray-400">${ethIp}</span>
                </div>
                <p class="text-xs text-gray-400 mt-2">${t('wan_priority_ethernet')}</p>
            </div>
        `;
    } else if (wifiConnected) {
        const wifiSsid = escapeHtml(wan.wifi?.ssid || '');
        const wifiIp = escapeHtml(wan.wifi?.ip || '');
        container.innerHTML = `
            <div class="bg-blue-900/30 border border-blue-700 rounded-lg p-3">
                <div class="flex items-center justify-between gap-2 flex-wrap">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <span class="font-medium truncate">${wifiSsid}</span>
                        <span class="text-sm text-gray-400">${wifiIp}</span>
                    </div>
                    <button data-action="disconnect-wifi"
                        class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-smooth focus-ring touch-manipulation flex items-center gap-1">
                        ${icon('wifi-off')}
                        <span>${t('disconnect')}</span>
                    </button>
                </div>
            </div>
        `;
        refreshIcons();
    } else {
        container.innerHTML = `
            <div class="bg-gray-700/50 border border-gray-600 rounded-lg p-3">
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-gray-500 rounded-full"></div>
                    <span class="text-gray-400">${t('wifi_not_connected')}</span>
                </div>
                <p class="text-xs text-gray-500 mt-2">${t('scan_to_connect')}</p>
            </div>
        `;
    }
}

/**
 * Connect to a WiFi network
 * @param {string} ssid - Network SSID
 * @param {HTMLElement} btn - Button element
 */
export function connectToWifi(ssid, btn) {
    const password = prompt(`${t('password_for')} ${ssid}:`);
    if (!password) return;

    setButtonLoading(btn, true);
    fetch('/api/wifi/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ssid, password })
    })
        .then(r => {
            if (r.ok) return r.json();
            return r.json().then(data => Promise.reject(data));
        })
        .then(() => {
            showToast(`${t('wifi_connected_to')} ${escapeHtml(ssid)}`, 'success');
            htmx.trigger('#status-cards', 'htmx:load');
            htmx.trigger('#wifi-current-status', 'htmx:load');
        })
        .catch((err) => {
            // Escape error message from server to prevent XSS
            const serverMsg = err.detail ? escapeHtml(String(err.detail)) : null;
            const msg = serverMsg || `${t('connection_failed')}: ${escapeHtml(ssid)}`;
            showToast(msg, 'error');
        })
        .finally(() => setButtonLoading(btn, false));
}

/**
 * Disconnect from current WiFi network
 * @param {HTMLElement} btn - Button element
 */
export function disconnectWifi(btn) {
    if (!confirm(t('confirm_disconnect'))) {
        return;
    }

    setButtonLoading(btn, true);
    fetch('/api/wifi/disconnect', { method: 'POST' })
        .then(r => {
            if (r.ok) return r.json();
            return r.json().then(data => Promise.reject(data));
        })
        .then(() => {
            showToast(t('wifi_disconnected'), 'success');
            htmx.trigger('#status-cards', 'htmx:load');
            htmx.trigger('#wifi-current-status', 'htmx:load');
        })
        .catch((err) => {
            // Escape error message from server to prevent XSS
            const serverMsg = err.detail ? escapeHtml(String(err.detail)) : null;
            const msg = serverMsg || t('error');
            showToast(msg, 'error');
        })
        .finally(() => setButtonLoading(btn, false));
}

/**
 * Initialize WiFi event delegation
 * Call this once from main.js to set up click handlers
 */
export function initWifiEvents() {
    document.addEventListener('click', (e) => {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;

        if (action === 'connect-wifi') {
            const ssid = target.dataset.ssid;
            if (ssid) {
                connectToWifi(ssid, target);
            }
        } else if (action === 'disconnect-wifi') {
            disconnectWifi(target);
        }
    });
}
