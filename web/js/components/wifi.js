/**
 * ROSE Link - WiFi Component
 * Handles WiFi scanning, connection, and status display
 */

import { escapeHtml, icon, refreshIcons, setButtonLoading } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';
import { showConfirm, showPrompt } from '../utils/modal.js';

// Device capabilities - populated from system info
let deviceCapabilities = {
    singleWifi: false,
    loaded: false
};

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
export async function connectToWifi(ssid, btn) {
    const password = await showPrompt({
        title: t('connect_to_wifi') || 'Connect to WiFi',
        message: `${t('password_for') || 'Enter password for'} ${ssid}`,
        placeholder: t('wifi_password') || 'WiFi password',
        inputType: 'password',
        confirmText: t('connect') || 'Connect',
        cancelText: t('cancel') || 'Cancel',
        icon: 'wifi'
    });

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
export async function disconnectWifi(btn) {
    const confirmed = await showConfirm({
        title: t('disconnect_wifi') || 'Disconnect WiFi',
        message: t('confirm_disconnect') || 'Are you sure you want to disconnect from WiFi?',
        confirmText: t('disconnect') || 'Disconnect',
        cancelText: t('cancel') || 'Cancel',
        variant: 'danger',
        icon: 'wifi-off'
    });

    if (!confirmed) return;

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

/**
 * Load device capabilities from system info API
 */
async function loadDeviceCapabilities() {
    if (deviceCapabilities.loaded) return;

    try {
        const response = await fetch('/api/system/info');
        if (response.ok) {
            const data = await response.json();
            deviceCapabilities.singleWifi = data.interfaces?.single_wifi || false;
            deviceCapabilities.loaded = true;
        }
    } catch {
        // Silently fail - assume dual WiFi if we can't fetch
        deviceCapabilities.loaded = true;
    }
}

/**
 * Check if device has single WiFi (no WiFi WAN available)
 * @returns {boolean}
 */
export function isSingleWifiDevice() {
    return deviceCapabilities.singleWifi;
}

/**
 * Update WiFi tab UI for single WiFi devices
 * Disables scan button and shows warning message
 */
function updateWifiTabForSingleDevice() {
    if (!deviceCapabilities.singleWifi) return;

    const scanBtn = document.getElementById('wifi-scan-btn');
    const networksContainer = document.getElementById('wifi-networks');
    const statusContainer = document.getElementById('wifi-current-status');

    // Disable scan button
    if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.classList.remove('bg-rose-600', 'hover:bg-rose-700', 'active:bg-rose-800');
        scanBtn.classList.add('bg-gray-600', 'cursor-not-allowed', 'opacity-50');
        // Remove HTMX attributes to prevent scanning
        scanBtn.removeAttribute('hx-post');
        scanBtn.removeAttribute('hx-target');
        scanBtn.removeAttribute('hx-indicator');
    }

    // Show warning message in networks container
    if (networksContainer) {
        networksContainer.innerHTML = `
            <div class="bg-orange-900/30 border border-orange-700 rounded-lg p-4">
                <div class="flex items-start gap-3">
                    ${icon('alert-triangle', 'w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5')}
                    <div>
                        <p class="font-medium text-orange-300 mb-1">${t('single_wifi_title')}</p>
                        <p class="text-sm text-orange-200/80">${t('single_wifi_message')}</p>
                    </div>
                </div>
            </div>
        `;
        refreshIcons();
    }

    // Update status container to show Ethernet requirement
    if (statusContainer) {
        // Replace the hx-get to prevent status updates showing WiFi options
        statusContainer.removeAttribute('hx-get');
        statusContainer.removeAttribute('hx-trigger');
        statusContainer.innerHTML = `
            <div class="bg-gray-700/50 border border-gray-600 rounded-lg p-3">
                <div class="flex items-center gap-2">
                    ${icon('ethernet-port', 'w-5 h-5 text-orange-400')}
                    <span class="text-gray-300">${t('ethernet_required')}</span>
                </div>
                <p class="text-xs text-gray-500 mt-2">${t('single_wifi_device_desc')}</p>
            </div>
        `;
        refreshIcons();
    }
}

/**
 * Initialize WiFi tab with single device check
 * Call this on page load to update UI if needed
 */
export async function initWifiTab() {
    await loadDeviceCapabilities();
    updateWifiTabForSingleDevice();
}
