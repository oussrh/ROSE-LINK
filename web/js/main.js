/**
 * ROSE Link - Main Entry Point
 * Initializes all modules and handles htmx events
 */

// Import configuration
import { fetchAppVersion } from './config.js';

// Import i18n
import { initI18n, t } from './i18n.js';

// Import utilities
import './utils/toast.js';
import './utils/modal.js';
import { initWebSocket } from './utils/websocket.js';
import { showConfirm } from './utils/modal.js';
import { escapeHtml } from './utils/dom.js';

// Import components
import { initTabs } from './components/tabs.js';
import { renderStatusCards } from './components/statusCards.js';
import { renderWifiNetworks, renderWifiCurrentStatus, initWifiEvents, initWifiTab } from './components/wifi.js';
import { renderVPNStatus, renderVPNProfiles, renderVPNActionResult, loadVPNSettings, initVPNEvents, initVPNImportForm } from './components/vpn.js';
import { renderConnectedClients, initHotspotForm } from './components/hotspot.js';
import { renderSystemInfo, initVPNSettingsForm, initRebootHandler, initServiceRestartHandlers } from './components/system.js';
import { initWizard, showWizard, resetWizard } from './components/wizard.js';
import { renderAdGuardStatus, renderAdGuardStats, renderAdGuardQueryLog, handleAdGuardAction } from './components/adguard.js';
import { initUpdater } from './components/updater.js';

// Make t() function globally available
window.t = t;

/**
 * Handle htmx afterSwap events for rendering dynamic content
 */
function setupHtmxHandlers() {
    // Handle HTMX errors (400, 500, etc.)
    document.body.addEventListener('htmx:responseError', (event) => {
        const targetId = event.detail.target?.id;
        const xhr = event.detail.xhr;

        // Handle VPN action errors
        if (targetId === 'vpn-message') {
            try {
                const data = JSON.parse(xhr.responseText);
                const errorMsg = data.detail || t('error');
                const container = document.getElementById('vpn-message');
                if (container) {
                    container.innerHTML = `
                        <div class="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm flex items-center gap-2">
                            <i data-lucide="alert-circle" class="w-4 h-4 flex-shrink-0"></i>
                            <span>${escapeHtml(errorMsg)}</span>
                        </div>`;
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
            } catch {
                // Ignore parse errors
            }
            return;
        }

        // Handle AdGuard errors gracefully
        if (targetId === 'adguard-status') {
            renderAdGuardStatus({ installed: false, running: false });
        } else if (targetId === 'adguard-stats') {
            const container = document.getElementById('adguard-stats');
            if (container) {
                container.innerHTML = '<div class="text-gray-400 text-sm p-4 text-center">AdGuard Home is not available</div>';
            }
        }
    });

    document.body.addEventListener('htmx:afterSwap', (event) => {
        const targetId = event.detail.target.id;
        try {
            const data = JSON.parse(event.detail.xhr.responseText);

            switch (targetId) {
                case 'status-cards':
                    renderStatusCards(data);
                    break;
                case 'wifi-current-status':
                    renderWifiCurrentStatus(data);
                    break;
                case 'wifi-networks':
                    renderWifiNetworks(data.networks);
                    break;
                case 'vpn-status-detail':
                    renderVPNStatus(data);
                    break;
                case 'vpn-profiles':
                    renderVPNProfiles(data.profiles);
                    break;
                case 'vpn-message':
                    renderVPNActionResult(data);
                    break;
                case 'system-info':
                    renderSystemInfo(data);
                    break;
                case 'connected-clients':
                    renderConnectedClients(data);
                    break;
                case 'adguard-status':
                    renderAdGuardStatus(data);
                    break;
                case 'adguard-stats':
                    renderAdGuardStats(data);
                    break;
                case 'adguard-querylog':
                    renderAdGuardQueryLog(data);
                    break;
                case 'adguard-message':
                    handleAdGuardAction(data, 'adguard-message');
                    break;
                case 'adguard-stats-message':
                    handleAdGuardAction(data, 'adguard-stats-message');
                    break;
            }
        } catch {
            // Non-JSON response, ignore
        }
    });
}

/**
 * Setup HTMX confirm interceptor for custom modal dialogs
 * Intercepts elements with data-confirm-* attributes before HTMX requests
 */
function setupHtmxConfirmInterceptor() {
    document.body.addEventListener('htmx:confirm', async (event) => {
        const el = event.detail.elt;

        // Check if element has custom confirm attributes
        const confirmTitle = el.dataset.confirmTitle;
        const confirmMessage = el.dataset.confirmMessage;

        if (!confirmMessage) {
            // No custom confirm, let HTMX handle it normally
            return;
        }

        // Prevent default HTMX confirm behavior
        event.preventDefault();

        // Show custom modal
        const confirmed = await showConfirm({
            title: confirmTitle || t('confirm') || 'Confirm',
            message: confirmMessage,
            confirmText: el.dataset.confirmText || t('confirm') || 'Confirm',
            cancelText: t('cancel') || 'Cancel',
            variant: el.dataset.confirmVariant || 'default',
            icon: el.dataset.confirmIcon || 'alert-circle'
        });

        if (confirmed) {
            // Issue the HTMX request
            event.detail.issueRequest();
        }
    });
}

/**
 * Setup WebSocket real-time update handlers
 */
function setupWebSocketHandlers() {
    // Listen for real-time status updates from WebSocket
    window.addEventListener('rose:status', (event) => {
        const data = event.detail;
        if (data) {
            renderStatusCards(data);
        }
    });

    // Listen for bandwidth updates
    window.addEventListener('rose:bandwidth', (event) => {
        const data = event.detail;
        // Dispatch to bandwidth component if it exists
        const bandwidthEl = document.getElementById('bandwidth-stats');
        if (bandwidthEl && data) {
            window.dispatchEvent(new CustomEvent('rose:bandwidth:update', { detail: data }));
        }
    });
}

/**
 * Initialize the application
 */
async function init() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Fetch app version from backend
    await fetchAppVersion();

    // Initialize i18n (loads translations and updates DOM)
    await initI18n();

    // Initialize components
    initTabs();
    initWifiEvents();
    initVPNEvents();
    initVPNImportForm();
    initHotspotForm();
    initVPNSettingsForm();

    // Initialize WiFi tab (checks for single WiFi device)
    initWifiTab();

    // Initialize setup wizard (checks if first run)
    initWizard();

    // Set up run wizard button in System tab
    setupWizardButton();

    // Load VPN settings
    loadVPNSettings();

    // Setup htmx event handlers
    setupHtmxHandlers();

    // Setup HTMX confirm interceptor for custom modal dialogs
    setupHtmxConfirmInterceptor();

    // Initialize reboot button handler
    initRebootHandler();

    // Initialize service restart handlers (VPN, Hotspot)
    initServiceRestartHandlers();

    // Setup WebSocket real-time updates
    setupWebSocketHandlers();
    initWebSocket();

    // Initialize update checker
    initUpdater();
}

/**
 * Setup the "Run Setup Wizard" button in System tab
 */
function setupWizardButton() {
    const wizardBtn = document.getElementById('run-wizard-btn');
    if (wizardBtn) {
        wizardBtn.addEventListener('click', async () => {
            const confirmed = await showConfirm({
                title: t('run_wizard') || 'Run Setup Wizard',
                message: t('confirm_run_wizard') || 'This will start the setup wizard to reconfigure your device. Continue?',
                confirmText: t('start') || 'Start',
                cancelText: t('cancel') || 'Cancel',
                variant: 'default',
                icon: 'wand-2'
            });

            if (confirmed) {
                resetWizard();
                showWizard();
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
