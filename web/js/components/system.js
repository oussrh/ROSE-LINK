/**
 * ROSE Link - System Component
 * Handles system info display and settings
 */

import { escapeHtml, setButtonLoading } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';

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
        fetch('/api/settings/vpn', {
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
                const msg = err.detail || t('settings_save_failed');
                showToast(msg, 'error');
            })
            .finally(() => setButtonLoading(btn, false));
    });
}

/**
 * Update reboot confirmation messages with translated text
 */
export function updateRebootConfirmations() {
    document.querySelectorAll('[hx-confirm]').forEach(el => {
        el.setAttribute('hx-confirm', t('confirm_reboot'));
    });
}
