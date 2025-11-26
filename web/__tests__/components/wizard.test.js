/**
 * Tests for Setup Wizard Component
 */

// Mock modules before importing
jest.mock('../../js/utils/dom.js', () => ({
    escapeHtml: jest.fn(str => str),
    icon: jest.fn((name, className) => `<i data-lucide="${name}" class="${className || ''}"></i>`),
    refreshIcons: jest.fn(),
    setButtonLoading: jest.fn()
}));

jest.mock('../../js/i18n.js', () => ({
    t: jest.fn(key => key)
}));

jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

import {
    shouldShowWizard,
    markWizardCompleted,
    resetWizard,
    showWizard,
    hideWizard,
    nextStep,
    prevStep,
    goToStep,
    completeWizard,
    skipWizard,
    initWizard
} from '../../js/components/wizard.js';
import { showToast } from '../../js/utils/toast.js';
import { t } from '../../js/i18n.js';

describe('Setup Wizard Component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();

        // Set up wizard DOM
        document.body.innerHTML = `
            <div id="setup-wizard" class="hidden">
                <div id="wizard-step-counter">1 / 5</div>
                <div class="wizard-step-indicator"></div>
                <div class="wizard-step-indicator"></div>
                <div class="wizard-step-indicator"></div>
                <div class="wizard-step-indicator"></div>
                <div class="wizard-step-indicator"></div>
                <div id="wizard-content"></div>
            </div>
        `;

        // Reset wizard state
        resetWizard();

        // Mock confirm
        global.confirm = jest.fn();

        // Mock htmx
        global.htmx = { trigger: jest.fn() };
    });

    afterEach(() => {
        delete global.confirm;
        delete global.htmx;
    });

    describe('shouldShowWizard', () => {
        it('should return true when wizard has not been completed', () => {
            expect(shouldShowWizard()).toBe(true);
        });

        it('should return false when wizard has been completed', () => {
            localStorage.setItem('rose-link-wizard-completed', 'true');
            expect(shouldShowWizard()).toBe(false);
        });
    });

    describe('markWizardCompleted', () => {
        it('should set localStorage flag', () => {
            markWizardCompleted();
            expect(localStorage.getItem('rose-link-wizard-completed')).toBe('true');
        });
    });

    describe('resetWizard', () => {
        it('should clear localStorage flag', () => {
            localStorage.setItem('rose-link-wizard-completed', 'true');
            resetWizard();
            expect(localStorage.getItem('rose-link-wizard-completed')).toBeNull();
        });

        it('should reset current step to 0', () => {
            // Navigate forward then reset
            nextStep();
            nextStep();
            resetWizard();

            // After reset, showing wizard should render welcome step
            showWizard();
            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_welcome_title');
        });
    });

    describe('showWizard', () => {
        it('should remove hidden class from wizard element', () => {
            const wizard = document.getElementById('setup-wizard');
            expect(wizard.classList.contains('hidden')).toBe(true);

            showWizard();

            expect(wizard.classList.contains('hidden')).toBe(false);
        });

        it('should render current step content', () => {
            showWizard();

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).not.toBe('');
        });

        it('should handle missing wizard element gracefully', () => {
            document.body.innerHTML = '';
            expect(() => showWizard()).not.toThrow();
        });
    });

    describe('hideWizard', () => {
        it('should add hidden class to wizard element', () => {
            const wizard = document.getElementById('setup-wizard');
            wizard.classList.remove('hidden');

            hideWizard();

            expect(wizard.classList.contains('hidden')).toBe(true);
        });

        it('should handle missing wizard element gracefully', () => {
            document.body.innerHTML = '';
            expect(() => hideWizard()).not.toThrow();
        });
    });

    describe('nextStep', () => {
        it('should advance to next step', () => {
            showWizard();
            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('1 / 5');

            nextStep();

            expect(stepCounter.textContent).toBe('2 / 5');
        });

        it('should not advance past last step', () => {
            showWizard();

            // Go to last step
            nextStep(); // 2
            nextStep(); // 3
            nextStep(); // 4
            nextStep(); // 5 (last)
            nextStep(); // Should stay at 5

            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('5 / 5');
        });
    });

    describe('prevStep', () => {
        it('should go back to previous step', () => {
            showWizard();
            nextStep(); // Go to step 2
            nextStep(); // Go to step 3

            prevStep();

            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('2 / 5');
        });

        it('should not go before first step', () => {
            showWizard();

            prevStep(); // Should stay at 1

            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('1 / 5');
        });
    });

    describe('goToStep', () => {
        it('should go to specific step', () => {
            showWizard();

            goToStep(3);

            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('4 / 5');
        });

        it('should not go to negative step', () => {
            showWizard();

            goToStep(-1);

            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('1 / 5');
        });

        it('should not go past last step', () => {
            showWizard();

            goToStep(10);

            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('1 / 5');
        });
    });

    describe('completeWizard', () => {
        it('should mark wizard as completed', () => {
            completeWizard();
            expect(localStorage.getItem('rose-link-wizard-completed')).toBe('true');
        });

        it('should hide wizard', () => {
            showWizard();
            completeWizard();

            const wizard = document.getElementById('setup-wizard');
            expect(wizard.classList.contains('hidden')).toBe(true);
        });

        it('should show success toast', () => {
            completeWizard();
            expect(showToast).toHaveBeenCalledWith('wizard_complete_message', 'success');
        });

        it('should trigger htmx refresh if available', () => {
            document.body.innerHTML += '<div id="status-cards"></div>';
            completeWizard();
            expect(global.htmx.trigger).toHaveBeenCalled();
        });
    });

    describe('skipWizard', () => {
        it('should show confirmation dialog', () => {
            global.confirm.mockReturnValue(false);
            skipWizard();
            expect(global.confirm).toHaveBeenCalledWith('wizard_skip_confirm');
        });

        it('should mark completed and hide wizard when confirmed', () => {
            global.confirm.mockReturnValue(true);
            showWizard();

            skipWizard();

            expect(localStorage.getItem('rose-link-wizard-completed')).toBe('true');
            const wizard = document.getElementById('setup-wizard');
            expect(wizard.classList.contains('hidden')).toBe(true);
        });

        it('should not do anything when cancelled', () => {
            global.confirm.mockReturnValue(false);
            showWizard();

            skipWizard();

            expect(localStorage.getItem('rose-link-wizard-completed')).toBeNull();
            const wizard = document.getElementById('setup-wizard');
            expect(wizard.classList.contains('hidden')).toBe(false);
        });
    });

    describe('initWizard', () => {
        it('should expose functions globally', () => {
            initWizard();

            expect(typeof window.nextStep).toBe('function');
            expect(typeof window.prevStep).toBe('function');
            expect(typeof window.skipWizard).toBe('function');
            expect(typeof window.completeWizard).toBe('function');
            expect(typeof window.resetWizard).toBe('function');
            expect(typeof window.showWizard).toBe('function');
        });

        it('should show wizard if first run', () => {
            initWizard();

            const wizard = document.getElementById('setup-wizard');
            expect(wizard.classList.contains('hidden')).toBe(false);
        });

        it('should not show wizard if already completed', () => {
            localStorage.setItem('rose-link-wizard-completed', 'true');

            initWizard();

            const wizard = document.getElementById('setup-wizard');
            expect(wizard.classList.contains('hidden')).toBe(true);
        });
    });

    describe('Step rendering', () => {
        it('should render welcome step correctly', () => {
            showWizard();

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_welcome_title');
            expect(content.innerHTML).toContain('wizard_welcome_desc');
            expect(content.innerHTML).toContain('wizard_get_started');
        });

        it('should render wifi step correctly', () => {
            showWizard();
            nextStep(); // Go to wifi step

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_wifi_title');
            expect(content.innerHTML).toContain('scan_networks');
        });

        it('should render vpn step correctly', () => {
            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_vpn_title');
            expect(content.innerHTML).toContain('import_profile');
        });

        it('should render hotspot step correctly', () => {
            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn
            nextStep(); // hotspot

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_hotspot_title');
            expect(content.innerHTML).toContain('ssid_label');
            expect(content.innerHTML).toContain('password_label');
        });

        it('should render complete step correctly', () => {
            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn
            nextStep(); // hotspot
            nextStep(); // complete

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_complete_title');
            expect(content.innerHTML).toContain('wizard_summary');
            expect(content.innerHTML).toContain('wizard_finish');
        });
    });

    describe('Progress indicators', () => {
        it('should update progress indicators on step change', () => {
            showWizard();

            const indicators = document.querySelectorAll('.wizard-step-indicator');

            // First step - only first indicator is rose
            expect(indicators[0].classList.contains('bg-rose-500')).toBe(true);
            expect(indicators[1].classList.contains('bg-gray-600')).toBe(true);

            nextStep();

            // Second step - first two indicators are rose
            expect(indicators[0].classList.contains('bg-rose-500')).toBe(true);
            expect(indicators[1].classList.contains('bg-rose-500')).toBe(true);
            expect(indicators[2].classList.contains('bg-gray-600')).toBe(true);
        });
    });

    describe('WiFi scanning', () => {
        it('should have scan button in wifi step', () => {
            showWizard();
            nextStep(); // wifi step

            const scanBtn = document.getElementById('wizard-wifi-scan');
            expect(scanBtn).not.toBeNull();
        });

        it('should scan networks when button clicked', async () => {
            const mockNetworks = [
                { ssid: 'Network1', signal: 80 },
                { ssid: 'Network2', signal: 60 }
            ];

            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ networks: mockNetworks })
            });

            showWizard();
            nextStep(); // wifi step

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(global.fetch).toHaveBeenCalledWith('/api/wifi/scan', { method: 'POST' });
        });

        it('should handle scan error', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Scan failed' })
            });

            showWizard();
            nextStep();

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            const container = document.getElementById('wizard-wifi-networks');
            expect(container.innerHTML).toContain('error');
        });
    });

    describe('VPN import', () => {
        it('should have import elements in vpn step', () => {
            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn

            const fileInput = document.getElementById('wizard-vpn-file');
            const importBtn = document.getElementById('wizard-vpn-import');

            expect(fileInput).not.toBeNull();
            expect(importBtn).not.toBeNull();
        });

        it('should show error when no file selected', async () => {
            showWizard();
            nextStep();
            nextStep();

            const importBtn = document.getElementById('wizard-vpn-import');
            importBtn.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('wizard_select_file', 'error');
        });
    });

    describe('Hotspot config', () => {
        it('should have form fields in hotspot step', () => {
            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn
            nextStep(); // hotspot

            const ssidInput = document.getElementById('wizard-hotspot-ssid');
            const passwordInput = document.getElementById('wizard-hotspot-password');
            const countrySelect = document.getElementById('wizard-hotspot-country');
            const bandSelect = document.getElementById('wizard-hotspot-band');

            expect(ssidInput).not.toBeNull();
            expect(passwordInput).not.toBeNull();
            expect(countrySelect).not.toBeNull();
            expect(bandSelect).not.toBeNull();
        });

        it('should have default SSID value', () => {
            showWizard();
            nextStep();
            nextStep();
            nextStep();

            const ssidInput = document.getElementById('wizard-hotspot-ssid');
            expect(ssidInput.value).toBe('ROSE-Link');
        });

        it('should validate empty SSID', async () => {
            showWizard();
            nextStep();
            nextStep();
            nextStep();

            const ssidInput = document.getElementById('wizard-hotspot-ssid');
            ssidInput.value = '';

            const saveBtn = document.getElementById('wizard-hotspot-save');
            saveBtn.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('wizard_ssid_required', 'error');
        });

        it('should validate password length', async () => {
            showWizard();
            nextStep();
            nextStep();
            nextStep();

            const ssidInput = document.getElementById('wizard-hotspot-ssid');
            ssidInput.value = 'TestSSID';

            const passwordInput = document.getElementById('wizard-hotspot-password');
            passwordInput.value = 'short';

            const saveBtn = document.getElementById('wizard-hotspot-save');
            saveBtn.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('wizard_password_min', 'error');
        });
    });

    describe('Content rendering edge cases', () => {
        it('should handle missing content container', () => {
            document.getElementById('wizard-content').remove();

            expect(() => showWizard()).not.toThrow();
            expect(() => nextStep()).not.toThrow();
        });

        it('should handle missing step counter', () => {
            document.getElementById('wizard-step-counter').remove();

            expect(() => showWizard()).not.toThrow();
            expect(() => nextStep()).not.toThrow();
        });
    });

    describe('WiFi network list rendering', () => {
        it('should render network list after scan', async () => {
            const mockNetworks = [
                { ssid: 'Network1', signal: 80 },
                { ssid: 'Network2', signal: 60 }
            ];

            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ networks: mockNetworks })
            });

            showWizard();
            nextStep(); // wifi step

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            const container = document.getElementById('wizard-wifi-networks');
            expect(container.innerHTML).toContain('Network1');
            expect(container.innerHTML).toContain('Network2');
        });

        it('should show no networks message when list is empty', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ networks: [] })
            });

            showWizard();
            nextStep();

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            const container = document.getElementById('wizard-wifi-networks');
            expect(container.innerHTML).toContain('no_networks');
        });

        it('should handle network click to connect', async () => {
            const mockNetworks = [{ ssid: 'TestNet', signal: 80 }];

            global.fetch = jest.fn()
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ networks: mockNetworks })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({})
                });

            global.prompt = jest.fn().mockReturnValue('password123');

            showWizard();
            nextStep();

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            const networkEl = document.querySelector('[data-ssid="TestNet"]');
            networkEl.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(global.fetch).toHaveBeenCalledWith('/api/wifi/connect', expect.any(Object));
        });

        it('should handle connection error', async () => {
            const mockNetworks = [{ ssid: 'TestNet', signal: 80 }];

            global.fetch = jest.fn()
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ networks: mockNetworks })
                })
                .mockResolvedValueOnce({
                    ok: false,
                    json: () => Promise.resolve({ detail: 'Wrong password' })
                });

            global.prompt = jest.fn().mockReturnValue('wrongpass');

            showWizard();
            nextStep();

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            const networkEl = document.querySelector('[data-ssid="TestNet"]');
            networkEl.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(showToast).toHaveBeenCalledWith(expect.any(String), 'error');
        });

        it('should not connect if password prompt cancelled', async () => {
            const mockNetworks = [{ ssid: 'TestNet', signal: 80 }];

            global.fetch = jest.fn().mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ networks: mockNetworks })
            });

            global.prompt = jest.fn().mockReturnValue(null);

            showWizard();
            nextStep();

            const scanBtn = document.getElementById('wizard-wifi-scan');
            scanBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            const networkEl = document.querySelector('[data-ssid="TestNet"]');
            networkEl.click();

            // fetch should only be called once for scan, not for connect
            expect(global.fetch).toHaveBeenCalledTimes(1);
        });
    });

    describe('VPN import success', () => {
        it('should import VPN profile successfully', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ name: 'TestVPN' })
            });

            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn

            const fileInput = document.getElementById('wizard-vpn-file');
            const file = new File(['[Interface]'], 'test.conf', { type: 'text/plain' });
            Object.defineProperty(fileInput, 'files', { value: [file] });

            const importBtn = document.getElementById('wizard-vpn-import');
            importBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(showToast).toHaveBeenCalledWith('upload_success', 'success');
        });

        it('should handle VPN import error', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Invalid file' })
            });

            showWizard();
            nextStep();
            nextStep();

            const fileInput = document.getElementById('wizard-vpn-file');
            const file = new File(['bad'], 'bad.conf', { type: 'text/plain' });
            Object.defineProperty(fileInput, 'files', { value: [file] });

            const importBtn = document.getElementById('wizard-vpn-import');
            importBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            const statusEl = document.getElementById('wizard-vpn-status');
            expect(statusEl.innerHTML).toContain('Invalid file');
        });
    });

    describe('Hotspot config save', () => {
        it('should save valid hotspot config', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            showWizard();
            nextStep(); // wifi
            nextStep(); // vpn
            nextStep(); // hotspot

            const ssidInput = document.getElementById('wizard-hotspot-ssid');
            ssidInput.value = 'MyHotspot';

            const passwordInput = document.getElementById('wizard-hotspot-password');
            passwordInput.value = 'password123';

            const saveBtn = document.getElementById('wizard-hotspot-save');
            saveBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(global.fetch).toHaveBeenCalledWith('/api/hotspot/apply', expect.any(Object));
            expect(showToast).toHaveBeenCalledWith('config_applied', 'success');
        });

        it('should continue even if hotspot API fails', async () => {
            global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

            showWizard();
            nextStep();
            nextStep();
            nextStep();

            const saveBtn = document.getElementById('wizard-hotspot-save');
            saveBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            // Should advance to complete step despite error
            const stepCounter = document.getElementById('wizard-step-counter');
            expect(stepCounter.textContent).toBe('5 / 5');
        });

        it('should set channel to 36 for 5GHz band', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            showWizard();
            nextStep();
            nextStep();
            nextStep();

            const bandSelect = document.getElementById('wizard-hotspot-band');
            bandSelect.value = '5GHz';

            const saveBtn = document.getElementById('wizard-hotspot-save');
            saveBtn.click();

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(global.fetch).toHaveBeenCalledWith('/api/hotspot/apply', expect.objectContaining({
                body: expect.stringContaining('"channel":36')
            }));
        });
    });

    describe('Wizard summary display', () => {
        it('should show configured items in summary', () => {
            showWizard();

            // Simulate wizard data being set
            nextStep(); // wifi
            nextStep(); // vpn
            nextStep(); // hotspot
            nextStep(); // complete

            const content = document.getElementById('wizard-content');
            expect(content.innerHTML).toContain('wizard_summary');
        });
    });
});
