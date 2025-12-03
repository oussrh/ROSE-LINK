/**
 * Tests for System Component
 */

// Mock dependencies before importing
jest.mock('../../js/utils/dom.js', () => ({
    escapeHtml: jest.fn(text => text || ''),
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

import { renderSystemInfo, initVPNSettingsForm } from '../../js/components/system.js';
import { escapeHtml, icon, refreshIcons, setButtonLoading } from '../../js/utils/dom.js';
import { t } from '../../js/i18n.js';
import { showToast } from '../../js/utils/toast.js';

describe('System Component', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="system-info"></div>
            <form id="vpn-settings-form">
                <input name="ping_host" value="8.8.8.8" />
                <input name="check_interval" value="60" />
                <button type="submit" id="vpn-settings-submit-btn">Save</button>
            </form>
            <button>Reboot</button>
            <button>Shutdown</button>
        `;
        jest.clearAllMocks();
    });

    describe('renderSystemInfo', () => {
        const mockData = {
            model: 'Raspberry Pi 4 Model B Rev 1.4',
            model_short: 'Pi 4B',
            architecture: 'aarch64',
            uptime_seconds: 3661, // 1 hour 1 minute 1 second
            ram_mb: 4096,
            ram_free_mb: 2048,
            disk_total_gb: 32,
            disk_free_gb: 20,
            cpu_temp_c: 45,
            wifi_capabilities: {
                supports_5ghz: true,
                supports_ac: true,
                supports_ax: false,
                ap_mode: true
            }
        };

        it('should render system information', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toBeTruthy();
        });

        it('should display model name', () => {
            renderSystemInfo(mockData);

            expect(escapeHtml).toHaveBeenCalledWith('Pi 4B');
            expect(t).toHaveBeenCalledWith('model');
        });

        it('should use full model when model_short is missing', () => {
            const data = { ...mockData, model_short: undefined };

            renderSystemInfo(data);

            expect(escapeHtml).toHaveBeenCalledWith('Raspberry Pi 4 Model B Rev 1.4');
        });

        it('should show unknown when model is missing', () => {
            const data = { ...mockData, model: undefined, model_short: undefined };

            renderSystemInfo(data);

            expect(t).toHaveBeenCalledWith('unknown');
        });

        it('should display architecture', () => {
            renderSystemInfo(mockData);

            expect(escapeHtml).toHaveBeenCalledWith('aarch64');
            expect(t).toHaveBeenCalledWith('architecture');
        });

        it('should calculate and display uptime correctly', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('1h 1m');
            expect(t).toHaveBeenCalledWith('uptime');
        });

        it('should handle zero uptime', () => {
            const data = { ...mockData, uptime_seconds: 0 };

            renderSystemInfo(data);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('0h 0m');
        });

        it('should display RAM usage', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('2048/4096MB');
            expect(t).toHaveBeenCalledWith('ram');
        });

        it('should display disk usage', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('20/32GB');
            expect(t).toHaveBeenCalledWith('disk');
        });

        it('should display CPU temperature', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('45°C');
            expect(t).toHaveBeenCalledWith('cpu');
        });

        it('should highlight high CPU temperature', () => {
            const data = { ...mockData, cpu_temp_c: 75 };

            renderSystemInfo(data);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('text-orange-400');
        });

        it('should not highlight normal CPU temperature', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            // 45°C is normal, should not have orange class
            const cpuSection = container.innerHTML;
            // Count occurrences of text-orange-400
            const matches = cpuSection.match(/text-orange-400/g);
            expect(matches).toBeNull();
        });

        it('should display WiFi capabilities', () => {
            renderSystemInfo(mockData);

            expect(t).toHaveBeenCalledWith('wifi_capabilities');
            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('5GHz');
            expect(container.innerHTML).toContain('AC');
            expect(container.innerHTML).toContain('AP');
        });

        it('should show 5GHz as supported when available', () => {
            renderSystemInfo(mockData);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('bg-green-900');
        });

        it('should show 5GHz as unsupported when not available', () => {
            const data = {
                ...mockData,
                wifi_capabilities: { supports_5ghz: false }
            };

            renderSystemInfo(data);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('bg-gray-600');
        });

        it('should handle missing wifi_capabilities', () => {
            const data = { ...mockData, wifi_capabilities: undefined };

            expect(() => renderSystemInfo(data)).not.toThrow();
        });

        it('should handle missing numeric values', () => {
            const data = {
                model_short: 'Pi',
                architecture: 'arm',
                uptime_seconds: 0
                // Missing ram, disk, cpu values
            };

            renderSystemInfo(data);

            const container = document.getElementById('system-info');
            expect(container.innerHTML).toContain('0/0MB');
            expect(container.innerHTML).toContain('0/0GB');
            expect(container.innerHTML).toContain('0°C');
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            expect(() => renderSystemInfo(mockData)).not.toThrow();
        });
    });

    describe('initVPNSettingsForm', () => {
        it('should attach submit handler to form', () => {
            const form = document.getElementById('vpn-settings-form');
            const addEventListenerSpy = jest.spyOn(form, 'addEventListener');

            initVPNSettingsForm();

            expect(addEventListenerSpy).toHaveBeenCalledWith('submit', expect.any(Function));
        });

        it('should handle missing form gracefully', () => {
            document.body.innerHTML = '';

            expect(() => initVPNSettingsForm()).not.toThrow();
        });

        it('should prevent default form submission', () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
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
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/vpn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: expect.any(String)
            });
        });

        it('should send correct payload', () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            const fetchCall = global.fetch.mock.calls[0];
            const body = JSON.parse(fetchCall[1].body);
            expect(body.ping_host).toBe('8.8.8.8');
            expect(body.check_interval).toBe(60);
        });

        it('should parse check_interval as integer', () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            const fetchCall = global.fetch.mock.calls[0];
            const body = JSON.parse(fetchCall[1].body);
            expect(typeof body.check_interval).toBe('number');
        });

        it('should set button loading during submission', () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            const btn = document.getElementById('vpn-settings-submit-btn');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));

            expect(setButtonLoading).toHaveBeenCalledWith(btn, true);
        });

        it('should show success toast on save', async () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(t).toHaveBeenCalledWith('vpn_settings_saved');
            expect(showToast).toHaveBeenCalledWith('vpn_settings_saved', 'success');
        });

        it('should show error toast on failure', async () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Invalid host' })
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('Invalid host', 'error');
        });

        it('should show default error message when detail is missing', async () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(t).toHaveBeenCalledWith('settings_save_failed');
        });

        it('should reset button loading after completion', async () => {
            initVPNSettingsForm();

            const form = document.getElementById('vpn-settings-form');
            const btn = document.getElementById('vpn-settings-submit-btn');
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            form.dispatchEvent(new Event('submit'));
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(setButtonLoading).toHaveBeenCalledWith(btn, false);
        });
    });

});
