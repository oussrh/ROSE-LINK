/**
 * Tests for Main Entry Point Module
 */

// Mock all dependencies before importing
jest.mock('../js/config.js', () => ({}));

jest.mock('../js/i18n.js', () => ({
    initI18n: jest.fn().mockResolvedValue(),
    t: jest.fn(key => key)
}));

jest.mock('../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

jest.mock('../js/utils/websocket.js', () => ({
    initWebSocket: jest.fn()
}));

jest.mock('../js/components/tabs.js', () => ({
    initTabs: jest.fn()
}));

jest.mock('../js/components/statusCards.js', () => ({
    renderStatusCards: jest.fn()
}));

jest.mock('../js/components/wifi.js', () => ({
    renderWifiNetworks: jest.fn(),
    renderWifiCurrentStatus: jest.fn(),
    initWifiEvents: jest.fn()
}));

jest.mock('../js/components/vpn.js', () => ({
    renderVPNStatus: jest.fn(),
    renderVPNProfiles: jest.fn(),
    loadVPNSettings: jest.fn(),
    initVPNEvents: jest.fn()
}));

jest.mock('../js/components/hotspot.js', () => ({
    renderConnectedClients: jest.fn(),
    initHotspotForm: jest.fn()
}));

jest.mock('../js/components/system.js', () => ({
    renderSystemInfo: jest.fn(),
    initVPNSettingsForm: jest.fn(),
    updateRebootConfirmations: jest.fn()
}));

jest.mock('../js/components/wizard.js', () => ({
    initWizard: jest.fn(),
    showWizard: jest.fn(),
    resetWizard: jest.fn()
}));

describe('Main Entry Point', () => {
    let initI18n, initTabs, initWifiEvents, initVPNEvents, initHotspotForm;
    let initVPNSettingsForm, initWizard, loadVPNSettings, initWebSocket;
    let updateRebootConfirmations, renderStatusCards, renderWifiNetworks;
    let renderWifiCurrentStatus, renderVPNStatus, renderVPNProfiles;
    let renderSystemInfo, renderConnectedClients, showWizard, resetWizard, t;

    beforeEach(async () => {
        jest.clearAllMocks();
        jest.resetModules();

        // Set up DOM
        document.body.innerHTML = `
            <div id="status-cards"></div>
            <div id="wifi-current-status"></div>
            <div id="wifi-networks"></div>
            <div id="vpn-status-detail"></div>
            <div id="vpn-profiles"></div>
            <div id="system-info"></div>
            <div id="connected-clients"></div>
            <div id="bandwidth-stats"></div>
            <button id="run-wizard-btn"></button>
        `;

        // Mock global objects
        global.lucide = { createIcons: jest.fn() };
        global.confirm = jest.fn();

        // Get mocked modules
        const i18nModule = await import('../js/i18n.js');
        initI18n = i18nModule.initI18n;
        t = i18nModule.t;

        const tabsModule = await import('../js/components/tabs.js');
        initTabs = tabsModule.initTabs;

        const wifiModule = await import('../js/components/wifi.js');
        initWifiEvents = wifiModule.initWifiEvents;
        renderWifiNetworks = wifiModule.renderWifiNetworks;
        renderWifiCurrentStatus = wifiModule.renderWifiCurrentStatus;

        const vpnModule = await import('../js/components/vpn.js');
        initVPNEvents = vpnModule.initVPNEvents;
        loadVPNSettings = vpnModule.loadVPNSettings;
        renderVPNStatus = vpnModule.renderVPNStatus;
        renderVPNProfiles = vpnModule.renderVPNProfiles;

        const hotspotModule = await import('../js/components/hotspot.js');
        initHotspotForm = hotspotModule.initHotspotForm;
        renderConnectedClients = hotspotModule.renderConnectedClients;

        const systemModule = await import('../js/components/system.js');
        initVPNSettingsForm = systemModule.initVPNSettingsForm;
        updateRebootConfirmations = systemModule.updateRebootConfirmations;
        renderSystemInfo = systemModule.renderSystemInfo;

        const wizardModule = await import('../js/components/wizard.js');
        initWizard = wizardModule.initWizard;
        showWizard = wizardModule.showWizard;
        resetWizard = wizardModule.resetWizard;

        const websocketModule = await import('../js/utils/websocket.js');
        initWebSocket = websocketModule.initWebSocket;

        const statusCardsModule = await import('../js/components/statusCards.js');
        renderStatusCards = statusCardsModule.renderStatusCards;
    });

    afterEach(() => {
        delete global.lucide;
        delete global.confirm;
    });

    describe('DOMContentLoaded initialization', () => {
        it('should register DOMContentLoaded listener', async () => {
            const addEventListenerSpy = jest.spyOn(document, 'addEventListener');

            await import('../js/main.js');

            expect(addEventListenerSpy).toHaveBeenCalledWith('DOMContentLoaded', expect.any(Function));
        });

        it('should initialize all components on DOMContentLoaded', async () => {
            await import('../js/main.js');

            // Trigger DOMContentLoaded
            const event = new Event('DOMContentLoaded');
            document.dispatchEvent(event);

            // Wait for async init
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(initI18n).toHaveBeenCalled();
            expect(initTabs).toHaveBeenCalled();
            expect(initWifiEvents).toHaveBeenCalled();
            expect(initVPNEvents).toHaveBeenCalled();
            expect(initHotspotForm).toHaveBeenCalled();
            expect(initVPNSettingsForm).toHaveBeenCalled();
            expect(initWizard).toHaveBeenCalled();
            expect(loadVPNSettings).toHaveBeenCalled();
            expect(initWebSocket).toHaveBeenCalled();
            expect(updateRebootConfirmations).toHaveBeenCalled();
        });

        it('should initialize Lucide icons when available', async () => {
            await import('../js/main.js');

            const event = new Event('DOMContentLoaded');
            document.dispatchEvent(event);

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(global.lucide.createIcons).toHaveBeenCalled();
        });

        it('should not throw when lucide is undefined', async () => {
            delete global.lucide;

            await import('../js/main.js');

            const event = new Event('DOMContentLoaded');
            expect(() => document.dispatchEvent(event)).not.toThrow();
        });

        it('should expose t function globally', async () => {
            await import('../js/main.js');

            expect(window.t).toBeDefined();
        });
    });

    describe('htmx event handlers', () => {
        beforeEach(async () => {
            await import('../js/main.js');
            document.dispatchEvent(new Event('DOMContentLoaded'));
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        it('should handle status-cards afterSwap event', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'status-cards' },
                    xhr: { responseText: '{"wan": true, "vpn": false}' }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderStatusCards).toHaveBeenCalledWith({ wan: true, vpn: false });
        });

        it('should handle wifi-current-status afterSwap event', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'wifi-current-status' },
                    xhr: { responseText: '{"connected": true, "ssid": "Test"}' }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderWifiCurrentStatus).toHaveBeenCalledWith({ connected: true, ssid: 'Test' });
        });

        it('should handle wifi-networks afterSwap event', () => {
            const networks = [{ ssid: 'Network1' }, { ssid: 'Network2' }];
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'wifi-networks' },
                    xhr: { responseText: JSON.stringify({ networks }) }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderWifiNetworks).toHaveBeenCalledWith(networks);
        });

        it('should handle vpn-status-detail afterSwap event', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'vpn-status-detail' },
                    xhr: { responseText: '{"active": true}' }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderVPNStatus).toHaveBeenCalledWith({ active: true });
        });

        it('should handle vpn-profiles afterSwap event', () => {
            const profiles = [{ name: 'Profile1' }];
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'vpn-profiles' },
                    xhr: { responseText: JSON.stringify({ profiles }) }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderVPNProfiles).toHaveBeenCalledWith(profiles);
        });

        it('should handle system-info afterSwap event', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'system-info' },
                    xhr: { responseText: '{"cpu": 50, "ram": 60}' }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderSystemInfo).toHaveBeenCalledWith({ cpu: 50, ram: 60 });
        });

        it('should handle connected-clients afterSwap event', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'connected-clients' },
                    xhr: { responseText: '{"clients": []}' }
                }
            });

            document.body.dispatchEvent(event);

            expect(renderConnectedClients).toHaveBeenCalledWith({ clients: [] });
        });

        it('should ignore non-JSON responses', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'status-cards' },
                    xhr: { responseText: 'not json' }
                }
            });

            expect(() => document.body.dispatchEvent(event)).not.toThrow();
            expect(renderStatusCards).not.toHaveBeenCalled();
        });

        it('should ignore unknown target ids', () => {
            const event = new CustomEvent('htmx:afterSwap', {
                detail: {
                    target: { id: 'unknown-target' },
                    xhr: { responseText: '{}' }
                }
            });

            expect(() => document.body.dispatchEvent(event)).not.toThrow();
        });
    });

    describe('WebSocket event handlers', () => {
        beforeEach(async () => {
            await import('../js/main.js');
            document.dispatchEvent(new Event('DOMContentLoaded'));
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        it('should handle rose:status event', () => {
            const statusData = { wan: true, vpn: true };
            const event = new CustomEvent('rose:status', { detail: statusData });

            window.dispatchEvent(event);

            expect(renderStatusCards).toHaveBeenCalledWith(statusData);
        });

        it('should not render status cards when data is null', () => {
            const event = new CustomEvent('rose:status', { detail: null });

            window.dispatchEvent(event);

            expect(renderStatusCards).not.toHaveBeenCalled();
        });

        it('should handle rose:bandwidth event with bandwidth element', () => {
            const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
            const bandwidthData = { rx: 100, tx: 50 };
            const event = new CustomEvent('rose:bandwidth', { detail: bandwidthData });

            window.dispatchEvent(event);

            // Should dispatch rose:bandwidth:update
            const updateCall = dispatchEventSpy.mock.calls.find(
                call => call[0].type === 'rose:bandwidth:update'
            );
            expect(updateCall).toBeDefined();
        });

        it('should not dispatch bandwidth update when element is missing', () => {
            document.getElementById('bandwidth-stats').remove();

            const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
            const event = new CustomEvent('rose:bandwidth', { detail: { rx: 100 } });

            window.dispatchEvent(event);

            const updateCall = dispatchEventSpy.mock.calls.find(
                call => call[0].type === 'rose:bandwidth:update'
            );
            expect(updateCall).toBeUndefined();
        });

        it('should not dispatch bandwidth update when data is null', () => {
            const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
            const event = new CustomEvent('rose:bandwidth', { detail: null });

            window.dispatchEvent(event);

            const updateCall = dispatchEventSpy.mock.calls.find(
                call => call[0].type === 'rose:bandwidth:update'
            );
            expect(updateCall).toBeUndefined();
        });
    });

    describe('Wizard button setup', () => {
        beforeEach(async () => {
            await import('../js/main.js');
            document.dispatchEvent(new Event('DOMContentLoaded'));
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        it('should set up click handler for wizard button', () => {
            const wizardBtn = document.getElementById('run-wizard-btn');
            global.confirm.mockReturnValue(true);

            wizardBtn.click();

            expect(global.confirm).toHaveBeenCalledWith('confirm_run_wizard');
        });

        it('should reset and show wizard when confirmed', () => {
            const wizardBtn = document.getElementById('run-wizard-btn');
            global.confirm.mockReturnValue(true);

            wizardBtn.click();

            expect(resetWizard).toHaveBeenCalled();
            expect(showWizard).toHaveBeenCalled();
        });

        it('should not show wizard when cancelled', () => {
            const wizardBtn = document.getElementById('run-wizard-btn');
            global.confirm.mockReturnValue(false);

            wizardBtn.click();

            expect(resetWizard).not.toHaveBeenCalled();
            expect(showWizard).not.toHaveBeenCalled();
        });

        it('should handle missing wizard button gracefully', async () => {
            document.getElementById('run-wizard-btn').remove();
            jest.resetModules();

            // Clear mocks
            jest.clearAllMocks();

            await import('../js/main.js');
            expect(() => document.dispatchEvent(new Event('DOMContentLoaded'))).not.toThrow();
        });
    });
});
