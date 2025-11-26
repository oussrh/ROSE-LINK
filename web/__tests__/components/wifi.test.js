/**
 * Tests for WiFi Component
 */

// Mock dependencies before importing
jest.mock('../../js/utils/dom.js', () => ({
    escapeHtml: jest.fn(text => text || ''),
    escapeJs: jest.fn(text => text || ''),
    icon: jest.fn(name => `<i data-lucide="${name}"></i>`),
    refreshIcons: jest.fn(),
    setButtonLoading: jest.fn()
}));

jest.mock('../../js/i18n.js', () => ({
    t: jest.fn(key => key)
}));

jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

import { renderWifiNetworks, renderWifiCurrentStatus, connectToWifi, disconnectWifi } from '../../js/components/wifi.js';
import { escapeHtml, escapeJs, icon, refreshIcons, setButtonLoading } from '../../js/utils/dom.js';
import { t } from '../../js/i18n.js';
import { showToast } from '../../js/utils/toast.js';

describe('WiFi Component', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="wifi-networks"></div>
            <div id="wifi-current-status"></div>
        `;
        jest.clearAllMocks();
        global.prompt = jest.fn();
        global.confirm = jest.fn();
    });

    describe('renderWifiNetworks', () => {
        it('should render list of networks', () => {
            const networks = [
                { ssid: 'Network1', security: 'WPA2', signal: 80 },
                { ssid: 'Network2', security: 'WPA3', signal: 60 }
            ];

            renderWifiNetworks(networks);

            const container = document.getElementById('wifi-networks');
            expect(container.children.length).toBe(2);
        });

        it('should display network SSID', () => {
            const networks = [{ ssid: 'MyNetwork', security: 'WPA2', signal: 75 }];

            renderWifiNetworks(networks);

            expect(escapeHtml).toHaveBeenCalledWith('MyNetwork');
        });

        it('should display network security type', () => {
            const networks = [{ ssid: 'MyNetwork', security: 'WPA2-PSK', signal: 75 }];

            renderWifiNetworks(networks);

            expect(escapeHtml).toHaveBeenCalledWith('WPA2-PSK');
        });

        it('should display signal strength', () => {
            const networks = [{ ssid: 'MyNetwork', security: 'WPA2', signal: 85 }];

            renderWifiNetworks(networks);

            const container = document.getElementById('wifi-networks');
            expect(container.innerHTML).toContain('85%');
        });

        it('should include connect button for each network', () => {
            const networks = [{ ssid: 'MyNetwork', security: 'WPA2', signal: 75 }];

            renderWifiNetworks(networks);

            const container = document.getElementById('wifi-networks');
            expect(container.innerHTML).toContain('onclick="connectToWifi');
            expect(t).toHaveBeenCalledWith('connect');
        });

        it('should show message when no networks available', () => {
            renderWifiNetworks([]);

            expect(t).toHaveBeenCalledWith('no_networks');
        });

        it('should show message when networks is null', () => {
            renderWifiNetworks(null);

            expect(t).toHaveBeenCalledWith('no_networks');
        });

        it('should escape SSID in onclick handler', () => {
            const networks = [{ ssid: "Network'With'Quotes", security: 'WPA2', signal: 75 }];

            renderWifiNetworks(networks);

            expect(escapeJs).toHaveBeenCalledWith("Network'With'Quotes");
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            expect(() => renderWifiNetworks([{ ssid: 'Test', security: 'WPA2', signal: 50 }]))
                .not.toThrow();
        });
    });

    describe('renderWifiCurrentStatus', () => {
        it('should show ethernet connected status when ethernet is connected', () => {
            const data = {
                wan: {
                    ethernet: { connected: true, ip: '192.168.1.100' },
                    wifi: { connected: false }
                }
            };

            renderWifiCurrentStatus(data);

            expect(t).toHaveBeenCalledWith('ethernet_connected');
            expect(t).toHaveBeenCalledWith('wan_priority_ethernet');
        });

        it('should show wifi connected status with disconnect button', () => {
            const data = {
                wan: {
                    ethernet: { connected: false },
                    wifi: { connected: true, ssid: 'MyNetwork', ip: '192.168.1.101' }
                }
            };

            renderWifiCurrentStatus(data);

            const container = document.getElementById('wifi-current-status');
            expect(container.innerHTML).toContain('disconnectWifi');
            expect(t).toHaveBeenCalledWith('disconnect');
        });

        it('should display wifi SSID and IP when connected', () => {
            const data = {
                wan: {
                    ethernet: { connected: false },
                    wifi: { connected: true, ssid: 'TestNetwork', ip: '10.0.0.50' }
                }
            };

            renderWifiCurrentStatus(data);

            expect(escapeHtml).toHaveBeenCalledWith('TestNetwork');
            expect(escapeHtml).toHaveBeenCalledWith('10.0.0.50');
        });

        it('should call refreshIcons after rendering wifi status', () => {
            const data = {
                wan: {
                    ethernet: { connected: false },
                    wifi: { connected: true, ssid: 'Test', ip: '1.2.3.4' }
                }
            };

            renderWifiCurrentStatus(data);

            expect(refreshIcons).toHaveBeenCalled();
        });

        it('should show not connected status', () => {
            const data = {
                wan: {
                    ethernet: { connected: false },
                    wifi: { connected: false }
                }
            };

            renderWifiCurrentStatus(data);

            expect(t).toHaveBeenCalledWith('wifi_not_connected');
            expect(t).toHaveBeenCalledWith('scan_to_connect');
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } }
            };

            expect(() => renderWifiCurrentStatus(data)).not.toThrow();
        });
    });

    describe('connectToWifi', () => {
        let button;

        beforeEach(() => {
            button = document.createElement('button');
            document.body.appendChild(button);
        });

        it('should prompt for password', () => {
            global.prompt.mockReturnValue('password123');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            connectToWifi('TestNetwork', button);

            expect(global.prompt).toHaveBeenCalled();
        });

        it('should not proceed if password is not provided', () => {
            global.prompt.mockReturnValue(null);

            connectToWifi('TestNetwork', button);

            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should set button loading state', () => {
            global.prompt.mockReturnValue('password123');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            connectToWifi('TestNetwork', button);

            expect(setButtonLoading).toHaveBeenCalledWith(button, true);
        });

        it('should call API with correct payload', () => {
            global.prompt.mockReturnValue('mypassword');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            connectToWifi('MyNetwork', button);

            expect(global.fetch).toHaveBeenCalledWith('/api/wifi/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: 'MyNetwork', password: 'mypassword' })
            });
        });

        it('should show success toast on successful connection', async () => {
            global.prompt.mockReturnValue('password123');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await connectToWifi('TestNetwork', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith(
                expect.stringContaining('TestNetwork'),
                'success'
            );
        });

        it('should show error toast on failed connection', async () => {
            global.prompt.mockReturnValue('password123');
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Wrong password' })
            });

            await connectToWifi('TestNetwork', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('Wrong password', 'error');
        });

        it('should reset button loading state after completion', async () => {
            global.prompt.mockReturnValue('password123');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await connectToWifi('TestNetwork', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(setButtonLoading).toHaveBeenCalledWith(button, false);
        });
    });

    describe('disconnectWifi', () => {
        let button;

        beforeEach(() => {
            button = document.createElement('button');
            document.body.appendChild(button);
        });

        it('should ask for confirmation', () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            disconnectWifi(button);

            expect(global.confirm).toHaveBeenCalledWith('confirm_disconnect');
        });

        it('should not proceed if not confirmed', () => {
            global.confirm.mockReturnValue(false);

            disconnectWifi(button);

            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should call disconnect API', () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            disconnectWifi(button);

            expect(global.fetch).toHaveBeenCalledWith('/api/wifi/disconnect', {
                method: 'POST'
            });
        });

        it('should show success toast on disconnect', async () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await disconnectWifi(button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('wifi_disconnected', 'success');
        });
    });

    describe('window global functions', () => {
        it('should expose connectToWifi globally', () => {
            expect(typeof window.connectToWifi).toBe('function');
        });

        it('should expose disconnectWifi globally', () => {
            expect(typeof window.disconnectWifi).toBe('function');
        });
    });
});
