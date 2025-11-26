/**
 * Tests for Hotspot Component
 */

// Mock dependencies before importing
jest.mock('../../js/utils/dom.js', () => ({
    escapeHtml: jest.fn(text => text || ''),
    icon: jest.fn(name => `<i data-lucide="${name}"></i>`),
    refreshIcons: jest.fn(),
    setButtonLoading: jest.fn(),
    formatBytes: jest.fn(bytes => `${bytes} B`)
}));

jest.mock('../../js/i18n.js', () => ({
    t: jest.fn(key => key)
}));

jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

import { updateChannels, renderConnectedClients, initHotspotForm } from '../../js/components/hotspot.js';
import { escapeHtml, icon, refreshIcons, setButtonLoading, formatBytes } from '../../js/utils/dom.js';
import { t } from '../../js/i18n.js';
import { showToast } from '../../js/utils/toast.js';

describe('Hotspot Component', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <select id="wifi-band">
                <option value="2.4GHz">2.4GHz</option>
                <option value="5GHz">5GHz</option>
            </select>
            <select id="wifi-channel"></select>
            <div id="connected-clients"></div>
            <form id="hotspot-form">
                <input name="ssid" value="TestNetwork" />
                <input name="password" value="password123" />
                <input name="country" value="US" />
                <input name="channel" value="6" />
                <input name="band" value="2.4GHz" />
                <input type="checkbox" name="wpa3" />
                <button type="submit" id="hotspot-submit-btn">Apply</button>
            </form>
            <div id="hotspot-message"></div>
        `;
        jest.clearAllMocks();
    });

    describe('updateChannels', () => {
        it('should update channels for 2.4GHz band', () => {
            document.getElementById('wifi-band').value = '2.4GHz';

            updateChannels();

            const channelSelect = document.getElementById('wifi-channel');
            expect(channelSelect.innerHTML).toContain('value="1"');
            expect(channelSelect.innerHTML).toContain('value="6"');
            expect(channelSelect.innerHTML).toContain('value="11"');
            expect(t).toHaveBeenCalledWith('recommended');
        });

        it('should update channels for 5GHz band', () => {
            document.getElementById('wifi-band').value = '5GHz';

            updateChannels();

            const channelSelect = document.getElementById('wifi-channel');
            expect(channelSelect.innerHTML).toContain('value="36"');
            expect(channelSelect.innerHTML).toContain('value="40"');
            expect(channelSelect.innerHTML).toContain('value="44"');
            expect(channelSelect.innerHTML).toContain('value="149"');
        });

        it('should default to 2.4GHz channels when band is not set', () => {
            document.getElementById('wifi-band').value = '';

            updateChannels();

            const channelSelect = document.getElementById('wifi-channel');
            expect(channelSelect.innerHTML).toContain('value="6"');
        });

        it('should handle missing band select gracefully', () => {
            document.body.innerHTML = '<select id="wifi-channel"></select>';

            expect(() => updateChannels()).not.toThrow();
        });

        it('should handle missing channel select gracefully', () => {
            document.body.innerHTML = '<select id="wifi-band"><option value="5GHz">5GHz</option></select>';

            expect(() => updateChannels()).not.toThrow();
        });

        it('should mark channel 6 as recommended for 2.4GHz', () => {
            document.getElementById('wifi-band').value = '2.4GHz';

            updateChannels();

            const channelSelect = document.getElementById('wifi-channel');
            expect(channelSelect.innerHTML).toContain('value="6"');
            // Channel 6 option should contain the recommended text
            const option6 = Array.from(channelSelect.options).find(o => o.value === '6');
            expect(option6.text).toContain('recommended');
        });

        it('should mark channel 36 as recommended for 5GHz', () => {
            document.getElementById('wifi-band').value = '5GHz';

            updateChannels();

            const channelSelect = document.getElementById('wifi-channel');
            const option36 = Array.from(channelSelect.options).find(o => o.value === '36');
            expect(option36.text).toContain('recommended');
        });
    });

    describe('renderConnectedClients', () => {
        it('should render list of connected clients', () => {
            const data = {
                clients: [
                    { hostname: 'Client1', ip: '192.168.1.10', mac: 'AA:BB:CC:DD:EE:FF', rx_bytes: 1000, tx_bytes: 500 },
                    { hostname: 'Client2', ip: '192.168.1.11', mac: '11:22:33:44:55:66', rx_bytes: 2000, tx_bytes: 1000 }
                ]
            };

            renderConnectedClients(data);

            const container = document.getElementById('connected-clients');
            expect(container.innerHTML).toContain('Client1');
            expect(container.innerHTML).toContain('Client2');
        });

        it('should display client count', () => {
            const data = {
                clients: [
                    { hostname: 'Client1', ip: '192.168.1.10' },
                    { hostname: 'Client2', ip: '192.168.1.11' }
                ]
            };

            renderConnectedClients(data);

            const container = document.getElementById('connected-clients');
            expect(container.innerHTML).toContain('2');
            expect(t).toHaveBeenCalledWith('clients_connected');
        });

        it('should show no clients message when empty', () => {
            const data = { clients: [] };

            renderConnectedClients(data);

            expect(t).toHaveBeenCalledWith('no_clients');
            expect(icon).toHaveBeenCalledWith('wifi-off');
        });

        it('should handle missing clients array', () => {
            const data = {};

            renderConnectedClients(data);

            expect(t).toHaveBeenCalledWith('no_clients');
        });

        it('should escape client hostname', () => {
            const data = {
                clients: [
                    { hostname: '<script>evil</script>', ip: '192.168.1.10' }
                ]
            };

            renderConnectedClients(data);

            expect(escapeHtml).toHaveBeenCalledWith('<script>evil</script>');
        });

        it('should escape client IP address', () => {
            const data = {
                clients: [
                    { hostname: 'Client', ip: '192.168.1.10', mac: 'AA:BB:CC:DD:EE:FF' }
                ]
            };

            renderConnectedClients(data);

            expect(escapeHtml).toHaveBeenCalledWith('192.168.1.10');
        });

        it('should escape client MAC address', () => {
            const data = {
                clients: [
                    { hostname: 'Client', ip: '192.168.1.10', mac: 'AA:BB:CC:DD:EE:FF' }
                ]
            };

            renderConnectedClients(data);

            expect(escapeHtml).toHaveBeenCalledWith('AA:BB:CC:DD:EE:FF');
        });

        it('should format traffic bytes', () => {
            const data = {
                clients: [
                    { hostname: 'Client', ip: '192.168.1.10', rx_bytes: 1024, tx_bytes: 512 }
                ]
            };

            renderConnectedClients(data);

            expect(formatBytes).toHaveBeenCalledWith(1024);
            expect(formatBytes).toHaveBeenCalledWith(512);
        });

        it('should handle missing traffic data', () => {
            const data = {
                clients: [
                    { hostname: 'Client', ip: '192.168.1.10' }
                ]
            };

            renderConnectedClients(data);

            expect(formatBytes).toHaveBeenCalledWith(0);
        });

        it('should use IP when hostname is missing', () => {
            const data = {
                clients: [
                    { ip: '192.168.1.10' }
                ]
            };

            renderConnectedClients(data);

            expect(escapeHtml).toHaveBeenCalledWith('192.168.1.10');
        });

        it('should show Unknown when both hostname and IP are missing', () => {
            const data = {
                clients: [
                    { mac: 'AA:BB:CC:DD:EE:FF' }
                ]
            };

            renderConnectedClients(data);

            expect(escapeHtml).toHaveBeenCalledWith('Unknown');
        });

        it('should display signal strength when available', () => {
            const data = {
                clients: [
                    { hostname: 'Client', ip: '192.168.1.10', signal: '-50 dBm' }
                ]
            };

            renderConnectedClients(data);

            expect(escapeHtml).toHaveBeenCalledWith('-50 dBm');
        });

        it('should call refreshIcons when no clients', () => {
            const data = { clients: [] };

            renderConnectedClients(data);

            expect(refreshIcons).toHaveBeenCalled();
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            expect(() => renderConnectedClients({ clients: [] })).not.toThrow();
        });
    });

    describe('initHotspotForm', () => {
        it('should attach submit handler to form', () => {
            const form = document.getElementById('hotspot-form');
            const addEventListenerSpy = jest.spyOn(form, 'addEventListener');

            initHotspotForm();

            expect(addEventListenerSpy).toHaveBeenCalledWith('submit', expect.any(Function));
        });

        it('should handle missing form gracefully', () => {
            document.body.innerHTML = '';

            expect(() => initHotspotForm()).not.toThrow();
        });

        it('should prevent default form submission', () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            const event = new Event('submit', { bubbles: true, cancelable: true });
            const preventDefault = jest.spyOn(event, 'preventDefault');

            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(event);

            expect(preventDefault).toHaveBeenCalled();
        });

        it('should call API with form data', () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            expect(global.fetch).toHaveBeenCalledWith('/api/hotspot/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: expect.any(String)
            });
        });

        it('should set button loading during submission', () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            const btn = document.getElementById('hotspot-submit-btn');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            expect(setButtonLoading).toHaveBeenCalledWith(btn, true);
        });

        it('should show success message on successful apply', async () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(t).toHaveBeenCalledWith('config_applied');
            const message = document.getElementById('hotspot-message');
            expect(message.innerHTML).toContain('bg-green-900');
        });

        it('should show error message on failure', async () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Invalid SSID' })
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            const message = document.getElementById('hotspot-message');
            expect(message.innerHTML).toContain('bg-red-900');
            expect(escapeHtml).toHaveBeenCalledWith('Invalid SSID');
        });

        it('should reset button loading after completion', async () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            const btn = document.getElementById('hotspot-submit-btn');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(setButtonLoading).toHaveBeenCalledWith(btn, false);
        });

        it('should parse channel as integer', () => {
            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            const fetchCall = global.fetch.mock.calls[0];
            const body = JSON.parse(fetchCall[1].body);
            expect(typeof body.channel).toBe('number');
        });

        it('should handle wpa3 checkbox', () => {
            document.querySelector('input[name="wpa3"]').checked = true;

            initHotspotForm();

            const form = document.getElementById('hotspot-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            const fetchCall = global.fetch.mock.calls[0];
            const body = JSON.parse(fetchCall[1].body);
            expect(body.wpa3).toBe(true);
        });
    });

    describe('window global functions', () => {
        it('should expose updateChannels globally', () => {
            expect(typeof window.updateChannels).toBe('function');
        });
    });
});
