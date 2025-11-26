/**
 * ROSE Link - Main Entry Point
 * Initializes all modules and handles htmx events
 */

// Import configuration
import './config.js';

// Import i18n
import { initI18n, t } from './i18n.js';

// Import utilities
import './utils/toast.js';
import { initWebSocket } from './utils/websocket.js';

// Import components
import { initTabs } from './components/tabs.js';
import { renderStatusCards } from './components/statusCards.js';
import { renderWifiNetworks, renderWifiCurrentStatus, initWifiEvents } from './components/wifi.js';
import { renderVPNStatus, renderVPNProfiles, loadVPNSettings, initVPNEvents } from './components/vpn.js';
import { renderConnectedClients, initHotspotForm } from './components/hotspot.js';
import { renderSystemInfo, initVPNSettingsForm, updateRebootConfirmations } from './components/system.js';
import { initWizard, showWizard, resetWizard } from './components/wizard.js';

// Make t() function globally available
window.t = t;

/**
 * Handle htmx afterSwap events for rendering dynamic content
 */
function setupHtmxHandlers() {
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
                case 'system-info':
                    renderSystemInfo(data);
                    break;
                case 'connected-clients':
                    renderConnectedClients(data);
                    break;
            }
        } catch {
            // Non-JSON response, ignore
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

    // Initialize i18n (loads translations and updates DOM)
    await initI18n();

    // Initialize components
    initTabs();
    initWifiEvents();
    initVPNEvents();
    initHotspotForm();
    initVPNSettingsForm();

    // Initialize setup wizard (checks if first run)
    initWizard();

    // Set up run wizard button in System tab
    setupWizardButton();

    // Load VPN settings
    loadVPNSettings();

    // Setup htmx event handlers
    setupHtmxHandlers();

    // Setup WebSocket real-time updates
    setupWebSocketHandlers();
    initWebSocket();

    // Update confirmation messages with translations
    updateRebootConfirmations();
}

/**
 * Setup the "Run Setup Wizard" button in System tab
 */
function setupWizardButton() {
    const wizardBtn = document.getElementById('run-wizard-btn');
    if (wizardBtn) {
        wizardBtn.addEventListener('click', () => {
            if (confirm(t('confirm_run_wizard'))) {
                resetWizard();
                showWizard();
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
