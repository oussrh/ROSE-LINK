/**
 * ROSE Link - Status Cards Component
 * Renders the main status cards (WAN, VPN, Hotspot)
 */

import { escapeHtml, icon, refreshIcons } from '../utils/dom.js';
import { t } from '../i18n.js';

/**
 * Render status cards with data from API
 * @param {Object} data - Status data from /api/status
 */
export function renderStatusCards(data) {
    const wan = data.wan;
    const vpn = data.vpn;
    const ap = data.ap;

    // Escape all API data to prevent XSS
    const ethIp = escapeHtml(wan.ethernet?.ip || '');
    const wifiSsid = escapeHtml(wan.wifi?.ssid || '');
    const wifiIp = escapeHtml(wan.wifi?.ip || '');
    const vpnReceived = escapeHtml(vpn.transfer?.received || '0 B');
    const apSsid = escapeHtml(ap.ssid || '');
    const apClients = parseInt(ap.clients) || 0;

    // WAN status
    const wanStatus = wan.ethernet?.connected
        ? `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-green-500 rounded-full"></div><span class="text-xs sm:text-base">${t('ethernet_connected')}</span></div><p class="text-xs text-gray-400 mt-1 truncate">${ethIp}</p>`
        : wan.wifi?.connected
            ? `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-blue-500 rounded-full"></div><span class="text-xs sm:text-base truncate">${wifiSsid}</span></div><p class="text-xs text-gray-400 mt-1 truncate">${wifiIp}</p>`
            : `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-red-500 rounded-full"></div><span class="text-xs sm:text-base">${t('disconnected')}</span></div>`;

    // VPN status
    const vpnStatus = vpn.active
        ? `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-green-500 rounded-full pulse-slow"></div><span class="text-xs sm:text-base">${t('vpn_active')}</span></div><p class="text-xs text-gray-400 mt-1">↓${vpnReceived}</p>`
        : `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-red-500 rounded-full"></div><span class="text-xs sm:text-base">${t('vpn_inactive')}</span></div>`;

    // AP/Hotspot status
    const apStatus = ap.active
        ? `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-green-500 rounded-full pulse-slow"></div><span class="text-xs sm:text-base truncate">${apSsid || t('hotspot_active')}</span></div><p class="text-xs text-gray-400 mt-1">${apClients} ${t('clients_connected')}</p>`
        : `<div class="flex items-center gap-1 sm:gap-2"><div class="w-2 h-2 sm:w-3 sm:h-3 bg-red-500 rounded-full"></div><span class="text-xs sm:text-base">${t('hotspot_inactive')}</span></div>`;

    const container = document.getElementById('status-cards');
    if (!container) return;

    container.innerHTML = `
        <div class="bg-gray-800 rounded-lg p-3 sm:p-6 border border-gray-700">
            <h3 class="text-xs sm:text-sm font-medium text-gray-400 mb-1 sm:mb-2 flex items-center gap-1"><span class="text-blue-400">${icon('wifi')}</span> ${t('status_wan')}</h3>
            <div class="text-sm sm:text-lg">${wanStatus}</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 sm:p-6 border border-gray-700">
            <h3 class="text-xs sm:text-sm font-medium text-gray-400 mb-1 sm:mb-2 flex items-center gap-1"><span class="text-green-400">${icon('shield-check')}</span> ${t('status_vpn')}</h3>
            <div class="text-sm sm:text-lg">${vpnStatus}</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 sm:p-6 border border-gray-700">
            <h3 class="text-xs sm:text-sm font-medium text-gray-400 mb-1 sm:mb-2 flex items-center gap-1"><span class="text-purple-400">${icon('radio-tower')}</span> ${t('status_hotspot')}</h3>
            <div class="text-sm sm:text-lg">${apStatus}</div>
        </div>
    `;
    refreshIcons();
}
