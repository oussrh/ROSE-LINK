/**
 * ROSE Link - AdGuard Component
 * Handles AdGuard Home ad-blocking status and statistics
 */

import { escapeHtml, icon, refreshIcons } from '../utils/dom.js';
import { t } from '../i18n.js';

/**
 * Render AdGuard status section
 * @param {Object} data - Status data from API
 */
export function renderAdGuardStatus(data) {
    const container = document.getElementById('adguard-status');
    const notInstalledEl = document.getElementById('adguard-not-installed');
    const controlsEl = document.getElementById('adguard-controls');

    if (!container) return;

    // Handle not installed state
    if (!data.installed) {
        container.innerHTML = `
            <div class="text-yellow-400 text-sm flex items-center gap-2">
                ${icon('alert-triangle')} ${t('adguard_not_installed')}
            </div>
        `;
        if (notInstalledEl) notInstalledEl.classList.remove('hidden');
        if (controlsEl) controlsEl.classList.add('hidden');
        refreshIcons();
        return;
    }

    if (notInstalledEl) notInstalledEl.classList.add('hidden');
    if (controlsEl) controlsEl.classList.remove('hidden');

    // Handle not running state
    if (!data.running) {
        container.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span class="text-red-400">${t('not_running')}</span>
                </div>
                ${data.version ? `<div class="text-sm text-gray-400">${t('adguard_version')}: ${escapeHtml(data.version)}</div>` : ''}
            </div>
        `;
        refreshIcons();
        return;
    }

    // Running state - show protection and filtering status
    const protectionStatus = data.protection_enabled
        ? `<span class="text-green-400">${icon('shield-check')} ${t('adguard_protection_enabled')}</span>`
        : `<span class="text-yellow-400">${icon('shield-off')} ${t('adguard_protection_disabled')}</span>`;

    const filteringStatus = data.filtering_enabled
        ? `<span class="text-green-400">${icon('filter')} ${t('adguard_filtering_enabled')}</span>`
        : `<span class="text-gray-400">${icon('filter-x')} ${t('adguard_filtering_disabled')}</span>`;

    container.innerHTML = `
        <div class="space-y-3">
            <div class="flex items-center gap-2">
                <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span class="text-green-400">${t('running')}</span>
                ${data.version ? `<span class="text-gray-500 text-sm">v${escapeHtml(data.version)}</span>` : ''}
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                <div class="flex items-center gap-2">${protectionStatus}</div>
                <div class="flex items-center gap-2">${filteringStatus}</div>
            </div>
            ${data.dns_addresses && data.dns_addresses.length > 0 ? `
                <div class="text-xs text-gray-500">
                    DNS: ${data.dns_addresses.map(addr => escapeHtml(addr)).join(', ')}
                </div>
            ` : ''}
        </div>
    `;
    refreshIcons();
}

/**
 * Render AdGuard statistics
 * @param {Object} data - Stats data from API
 */
export function renderAdGuardStats(data) {
    const container = document.getElementById('adguard-stats');
    const topBlockedContainer = document.getElementById('adguard-top-blocked');
    const topClientsContainer = document.getElementById('adguard-top-clients');

    if (!container) return;

    // Format numbers with locale
    const formatNumber = (num) => {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    };

    container.innerHTML = `
        <div class="grid grid-cols-3 gap-2 sm:gap-4">
            <div class="bg-gray-700 rounded-lg p-3 text-center">
                <div class="text-xl sm:text-2xl font-bold text-blue-400">${formatNumber(data.dns_queries || 0)}</div>
                <div class="text-xs text-gray-400">${t('adguard_dns_queries')}</div>
            </div>
            <div class="bg-gray-700 rounded-lg p-3 text-center">
                <div class="text-xl sm:text-2xl font-bold text-red-400">${formatNumber(data.blocked_total || 0)}</div>
                <div class="text-xs text-gray-400">${t('adguard_blocked')}</div>
            </div>
            <div class="bg-gray-700 rounded-lg p-3 text-center">
                <div class="text-xl sm:text-2xl font-bold text-green-400">${data.blocked_percent || 0}%</div>
                <div class="text-xs text-gray-400">${t('adguard_blocked_percent')}</div>
            </div>
        </div>
        <div class="mt-4 text-sm text-gray-400 flex items-center gap-4">
            <span>${icon('clock')} ${t('adguard_avg_time')}: ${data.avg_processing_time_ms || 0} ${t('ms')}</span>
        </div>
    `;
    refreshIcons();

    // Render top blocked domains
    if (topBlockedContainer && data.top_blocked_domains) {
        renderTopList(topBlockedContainer, data.top_blocked_domains, 'ban', 'text-red-400');
    }

    // Render top clients
    if (topClientsContainer && data.top_clients) {
        renderTopList(topClientsContainer, data.top_clients, 'monitor', 'text-cyan-400');
    }
}

/**
 * Render a top list (blocked domains or clients)
 * @param {HTMLElement} container - Container element
 * @param {Array} items - List of items
 * @param {string} iconName - Icon name for items
 * @param {string} iconClass - CSS class for icon color
 */
function renderTopList(container, items, iconName, iconClass) {
    if (!items || items.length === 0) {
        container.innerHTML = `<p class="text-gray-400 text-sm">${t('stats_loading')}</p>`;
        return;
    }

    // Items come as array of objects like { "domain.com": 123 }
    const sortedItems = items.slice(0, 5);

    container.innerHTML = `
        <div class="space-y-2">
            ${sortedItems.map(item => {
                const [name, count] = Object.entries(item)[0] || ['Unknown', 0];
                return `
                    <div class="flex items-center justify-between bg-gray-700 rounded px-3 py-2">
                        <div class="flex items-center gap-2 min-w-0">
                            <span class="${iconClass}">${icon(iconName)}</span>
                            <span class="truncate text-sm">${escapeHtml(name)}</span>
                        </div>
                        <span class="text-xs text-gray-400 flex-shrink-0">${count}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    refreshIcons();
}

/**
 * Render query log entries
 * @param {Object} data - Query log data from API
 */
export function renderAdGuardQueryLog(data) {
    const container = document.getElementById('adguard-querylog');
    if (!container) return;

    const queries = data.queries || [];

    if (queries.length === 0) {
        container.innerHTML = `<p class="text-gray-400">${t('stats_loading')}</p>`;
        return;
    }

    container.innerHTML = `
        <div class="space-y-1">
            ${queries.slice(0, 50).map(query => {
                const isBlocked = query.reason && query.reason !== 'NotFilteredNotFound';
                const statusIcon = isBlocked ? icon('shield-ban') : icon('check');
                const statusClass = isBlocked ? 'text-red-400' : 'text-green-400';
                const domain = query.question?.name || 'Unknown';
                const client = query.client || 'Unknown';
                const time = query.time ? new Date(query.time).toLocaleTimeString() : '';

                return `
                    <div class="flex items-center justify-between bg-gray-700/50 rounded px-2 py-1.5 text-xs">
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <span class="${statusClass} flex-shrink-0">${statusIcon}</span>
                            <span class="truncate">${escapeHtml(domain)}</span>
                        </div>
                        <div class="flex items-center gap-3 text-gray-500 flex-shrink-0">
                            <span>${escapeHtml(client)}</span>
                            <span>${time}</span>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    refreshIcons();
}

/**
 * Handle AdGuard action response (enable/disable/restart)
 * @param {Object} data - Response data
 * @param {string} targetId - Target element ID for message
 */
export function handleAdGuardAction(data, targetId) {
    const messageEl = document.getElementById(targetId);
    if (!messageEl) return;

    const status = data.status;
    const isSuccess = ['enabled', 'disabled', 'restarted', 'reset', 'started', 'stopped'].includes(status);

    if (isSuccess) {
        messageEl.innerHTML = `
            <div class="p-2 bg-green-900/50 border border-green-700 rounded text-green-200 text-sm flex items-center gap-2">
                ${icon('check-circle')} ${t('success')}: ${status}
            </div>
        `;
        // Refresh status after action
        setTimeout(() => {
            htmx.trigger('#adguard-status', 'htmx:load');
            htmx.trigger('#adguard-stats', 'htmx:load');
        }, 1000);
    } else {
        messageEl.innerHTML = `
            <div class="p-2 bg-red-900/50 border border-red-700 rounded text-red-200 text-sm flex items-center gap-2">
                ${icon('x-circle')} ${t('failed')}
            </div>
        `;
    }
    refreshIcons();

    // Clear message after 3 seconds
    setTimeout(() => {
        messageEl.innerHTML = '';
    }, 3000);
}
