/**
 * ROSE Link - Main Entry Point
 * Initializes all modules and handles htmx events
 */

// Import configuration
import './config.js';

// Import i18n
import { initI18n, t } from './i18n.js';

// Import utilities
import { refreshIcons } from './utils/dom.js';
import './utils/toast.js';

// Import components
import { initTabs } from './components/tabs.js';
import { renderStatusCards } from './components/statusCards.js';
import { renderWifiNetworks, renderWifiCurrentStatus } from './components/wifi.js';
import { renderVPNStatus, renderVPNProfiles, loadVPNSettings } from './components/vpn.js';
import { renderConnectedClients, initHotspotForm } from './components/hotspot.js';
import { renderSystemInfo, initVPNSettingsForm, updateRebootConfirmations } from './components/system.js';

// Make t() function globally available
window.t = t;

/**
 * Handle htmx afterSwap events for rendering dynamic content
 */
function setupHtmxHandlers() {
    document.body.addEventListener('htmx:afterSwap', function(event) {
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
        } catch (e) {
            // Non-JSON response, ignore
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
    initHotspotForm();
    initVPNSettingsForm();

    // Load VPN settings
    loadVPNSettings();

    // Setup htmx event handlers
    setupHtmxHandlers();

    // Update confirmation messages with translations
    updateRebootConfirmations();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
