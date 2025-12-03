/**
 * ROSE Link - Hotspot Component
 * Handles hotspot configuration and connected clients
 */

import { escapeHtml, icon, refreshIcons, setButtonLoading, formatBytes } from '../utils/dom.js';
import { t } from '../i18n.js';

/**
 * Update channel options based on selected band
 */
export function updateChannels() {
    const band = document.getElementById('wifi-band')?.value;
    const channelSelect = document.getElementById('wifi-channel');
    if (!channelSelect) return;

    const recommended = t('recommended');

    if (band === '5GHz') {
        channelSelect.innerHTML = `
            <option value="36">36 (5GHz) - ${recommended}</option>
            <option value="40">40 (5GHz)</option>
            <option value="44">44 (5GHz)</option>
            <option value="48">48 (5GHz)</option>
            <option value="149">149 (5GHz)</option>
            <option value="153">153 (5GHz)</option>
            <option value="157">157 (5GHz)</option>
            <option value="161">161 (5GHz)</option>
        `;
    } else {
        channelSelect.innerHTML = `
            <option value="1">1 (2.4GHz)</option>
            <option value="6" selected>6 (2.4GHz) - ${recommended}</option>
            <option value="11">11 (2.4GHz)</option>
        `;
    }
}

/**
 * Render connected clients list
 * @param {Object} data - Clients data from API
 */
export function renderConnectedClients(data) {
    const container = document.getElementById('connected-clients');
    if (!container) return;

    const clients = data.clients || [];
    if (clients.length === 0) {
        container.innerHTML = `
            <div class="text-gray-400 text-sm p-4 bg-gray-700/50 rounded-lg text-center flex items-center justify-center gap-2">
                ${icon('wifi-off')} ${t('no_clients')}
            </div>
        `;
        refreshIcons();
        return;
    }

    container.innerHTML = `
        <div class="space-y-2">
            ${clients.map(client => `
                <div class="bg-gray-700 rounded-lg p-3">
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <div class="flex items-center gap-2 min-w-0">
                            <div class="w-2 h-2 bg-green-500 rounded-full flex-shrink-0"></div>
                            <span class="font-medium truncate">${escapeHtml(client.hostname || client.ip || 'Unknown')}</span>
                        </div>
                        <span class="text-xs text-gray-400 flex-shrink-0">${escapeHtml(client.signal || '')}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-xs text-gray-400">
                        <div>
                            <span class="text-gray-500">${t('client_ip')}:</span> ${escapeHtml(client.ip || 'N/A')}
                        </div>
                        <div>
                            <span class="text-gray-500">${t('client_mac')}:</span> ${escapeHtml(client.mac || 'N/A')}
                        </div>
                    </div>
                    <div class="mt-2 text-xs text-gray-500">
                        ${t('client_traffic')}: ↓${formatBytes(client.rx_bytes || 0)} ↑${formatBytes(client.tx_bytes || 0)}
                    </div>
                </div>
            `).join('')}
        </div>
        <div class="mt-3 text-xs text-gray-500 text-center">
            ${clients.length} ${t('clients_connected')}
        </div>
    `;
}

/**
 * Initialize hotspot form handlers
 */
export function initHotspotForm() {
    const form = document.getElementById('hotspot-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const btn = document.getElementById('hotspot-submit-btn');
        const formData = new FormData(e.target);

        // Validate required fields before sending
        const ssid = formData.get('ssid')?.trim() || '';
        const password = formData.get('password') || '';

        if (!ssid) {
            document.getElementById('hotspot-message').innerHTML = `
                <div class="p-3 bg-red-900 border border-red-700 rounded-lg text-red-200 text-sm flex items-center gap-2">
                    ${icon('x-circle')} ${t('ssid_required') || 'SSID is required'}
                </div>`;
            refreshIcons();
            return;
        }

        if (!password || password.length < 8) {
            document.getElementById('hotspot-message').innerHTML = `
                <div class="p-3 bg-red-900 border border-red-700 rounded-lg text-red-200 text-sm flex items-center gap-2">
                    ${icon('x-circle')} ${t('password_min_length') || 'Password must be at least 8 characters'}
                </div>`;
            refreshIcons();
            return;
        }

        const data = {
            ssid: ssid,
            password: password,
            country: formData.get('country') || 'BE',
            channel: parseInt(formData.get('channel')) || 6,
            band: formData.get('band') || '2.4GHz',
            wpa3: formData.get('wpa3') === 'on'
        };

        setButtonLoading(btn, true);
        fetch('/api/hotspot/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(r => {
                if (r.ok) return r.json();
                // Try to parse as JSON, fall back to text if it fails
                return r.text().then(text => {
                    try {
                        return Promise.reject(JSON.parse(text));
                    } catch {
                        return Promise.reject({ detail: text || `Error ${r.status}` });
                    }
                });
            })
            .then(() => {
                document.getElementById('hotspot-message').innerHTML = `
                <div class="p-3 bg-green-900 border border-green-700 rounded-lg text-green-200 text-sm flex items-center gap-2">
                    ${icon('check-circle')} ${t('config_applied')}
                </div>`;
                refreshIcons();
                setTimeout(() => htmx.trigger('#status-cards', 'htmx:load'), 3000);
            })
            .catch((err) => {
                // Handle both string and object error responses
                let msg = t('error');
                if (typeof err === 'string') {
                    msg = err;
                } else if (err && err.detail) {
                    // FastAPI validation errors return array of errors
                    if (Array.isArray(err.detail)) {
                        msg = err.detail.map(e => {
                            // Include field location for debugging
                            const loc = e.loc ? e.loc.join('.') : '';
                            return loc ? `${loc}: ${e.msg}` : (e.msg || e.message || String(e));
                        }).join(', ');
                    } else {
                        msg = String(err.detail);
                    }
                } else if (err && err.message) {
                    msg = err.message;
                }
                document.getElementById('hotspot-message').innerHTML = `
                <div class="p-3 bg-red-900 border border-red-700 rounded-lg text-red-200 text-sm flex items-center gap-2">
                    ${icon('x-circle')} ${escapeHtml(msg)}
                </div>`;
                refreshIcons();
            })
            .finally(() => setButtonLoading(btn, false));
    });
}

// Make updateChannels globally available for onchange handlers
window.updateChannels = updateChannels;
