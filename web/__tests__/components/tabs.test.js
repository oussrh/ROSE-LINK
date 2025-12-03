/**
 * Tests for Tab Navigation Component
 */

import { showTab, restoreLastTab, initTabs, TAB_ORDER } from '../../js/components/tabs.js';

describe('Tab Navigation Component', () => {
    beforeEach(() => {
        // Set up DOM structure
        document.body.innerHTML = `
            <div class="tab-btn" id="tab-wifi" role="tab" aria-selected="true" aria-controls="content-wifi"></div>
            <div class="tab-btn" id="tab-vpn" role="tab" aria-selected="false" aria-controls="content-vpn"></div>
            <div class="tab-btn" id="tab-hotspot" role="tab" aria-selected="false" aria-controls="content-hotspot"></div>
            <div class="tab-btn" id="tab-system" role="tab" aria-selected="false" aria-controls="content-system"></div>
            <div class="tab-content" id="content-wifi"></div>
            <div class="tab-content hidden" id="content-vpn"></div>
            <div class="tab-content hidden" id="content-hotspot"></div>
            <div class="tab-content hidden" id="content-system"></div>
        `;
    });

    describe('TAB_ORDER', () => {
        it('should contain all expected tabs', () => {
            expect(TAB_ORDER).toEqual(['wifi', 'vpn', 'hotspot', 'system']);
        });

        it('should have wifi as the first tab', () => {
            expect(TAB_ORDER[0]).toBe('wifi');
        });
    });

    describe('showTab', () => {
        it('should show the specified tab content', () => {
            showTab('vpn');

            const vpnContent = document.getElementById('content-vpn');
            expect(vpnContent.classList.contains('hidden')).toBe(false);
        });

        it('should hide other tab contents', () => {
            showTab('vpn');

            const wifiContent = document.getElementById('content-wifi');
            expect(wifiContent.classList.contains('hidden')).toBe(true);
        });

        it('should set aria-selected to true on active tab button', () => {
            showTab('vpn');

            const vpnBtn = document.getElementById('tab-vpn');
            expect(vpnBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should set aria-selected to false on inactive tab buttons', () => {
            showTab('vpn');

            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.getAttribute('aria-selected')).toBe('false');
        });

        it('should add visual active styles to active tab', () => {
            showTab('hotspot');

            const hotspotBtn = document.getElementById('tab-hotspot');
            expect(hotspotBtn.classList.contains('border-rose-500')).toBe(true);
            expect(hotspotBtn.classList.contains('text-rose-500')).toBe(true);
        });

        it('should remove visual active styles from inactive tabs', () => {
            showTab('hotspot');

            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.classList.contains('border-rose-500')).toBe(false);
            expect(wifiBtn.classList.contains('border-transparent')).toBe(true);
        });

        it('should save tab to localStorage', () => {
            showTab('system');

            expect(localStorage.setItem).toHaveBeenCalledWith('rose-tab', 'system');
        });

        it('should not change anything for invalid tab names', () => {
            const wifiBtn = document.getElementById('tab-wifi');
            wifiBtn.setAttribute('aria-selected', 'true');

            showTab('invalid-tab');

            // localStorage should not be called with invalid tab
            expect(localStorage.setItem).not.toHaveBeenCalledWith('rose-tab', 'invalid-tab');
        });

        it('should set tabindex to 0 on active tab', () => {
            showTab('vpn');

            const vpnBtn = document.getElementById('tab-vpn');
            expect(vpnBtn.getAttribute('tabindex')).toBe('0');
        });

        it('should set tabindex to -1 on inactive tabs', () => {
            showTab('vpn');

            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.getAttribute('tabindex')).toBe('-1');
        });

        it('should focus the button when focus parameter is true', () => {
            const vpnBtn = document.getElementById('tab-vpn');
            vpnBtn.focus = jest.fn();

            showTab('vpn', true);

            expect(vpnBtn.focus).toHaveBeenCalled();
        });

        it('should not focus the button when focus parameter is false', () => {
            const vpnBtn = document.getElementById('tab-vpn');
            vpnBtn.focus = jest.fn();

            showTab('vpn', false);

            expect(vpnBtn.focus).not.toHaveBeenCalled();
        });
    });

    describe('restoreLastTab', () => {
        it('should restore saved tab from localStorage', () => {
            localStorage.getItem.mockReturnValue('hotspot');

            restoreLastTab();

            const hotspotContent = document.getElementById('content-hotspot');
            expect(hotspotContent.classList.contains('hidden')).toBe(false);
        });

        it('should default to first tab if no saved tab', () => {
            localStorage.getItem.mockReturnValue(null);

            restoreLastTab();

            const wifiContent = document.getElementById('content-wifi');
            expect(wifiContent.classList.contains('hidden')).toBe(false);
        });

        it('should default to first tab if saved tab is invalid', () => {
            localStorage.getItem.mockReturnValue('invalid-tab');

            restoreLastTab();

            const wifiContent = document.getElementById('content-wifi');
            expect(wifiContent.classList.contains('hidden')).toBe(false);
        });
    });

    describe('initTabs', () => {
        it('should call restoreLastTab', () => {
            localStorage.getItem.mockReturnValue('vpn');

            initTabs();

            const vpnContent = document.getElementById('content-vpn');
            expect(vpnContent.classList.contains('hidden')).toBe(false);
        });

        it('should add keydown listeners to tab buttons', () => {
            const addEventListenerSpy = jest.spyOn(
                document.getElementById('tab-wifi'),
                'addEventListener'
            );

            initTabs();

            expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
        });
    });

    describe('keyboard navigation', () => {
        beforeEach(() => {
            initTabs();
        });

        it('should navigate to next tab on ArrowRight', () => {
            showTab('wifi');
            const wifiBtn = document.getElementById('tab-wifi');

            const event = new KeyboardEvent('keydown', { key: 'ArrowRight' });
            wifiBtn.dispatchEvent(event);

            const vpnBtn = document.getElementById('tab-vpn');
            expect(vpnBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should navigate to previous tab on ArrowLeft', () => {
            showTab('vpn');
            const vpnBtn = document.getElementById('tab-vpn');

            const event = new KeyboardEvent('keydown', { key: 'ArrowLeft' });
            vpnBtn.dispatchEvent(event);

            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should wrap around from last to first tab', () => {
            showTab('system');
            const systemBtn = document.getElementById('tab-system');

            const event = new KeyboardEvent('keydown', { key: 'ArrowRight' });
            systemBtn.dispatchEvent(event);

            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should wrap around from first to last tab', () => {
            showTab('wifi');
            const wifiBtn = document.getElementById('tab-wifi');

            const event = new KeyboardEvent('keydown', { key: 'ArrowLeft' });
            wifiBtn.dispatchEvent(event);

            const systemBtn = document.getElementById('tab-system');
            expect(systemBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should navigate to first tab on Home key', () => {
            showTab('system');
            const systemBtn = document.getElementById('tab-system');

            const event = new KeyboardEvent('keydown', { key: 'Home' });
            systemBtn.dispatchEvent(event);

            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should navigate to last tab on End key', () => {
            showTab('wifi');
            const wifiBtn = document.getElementById('tab-wifi');

            const event = new KeyboardEvent('keydown', { key: 'End' });
            wifiBtn.dispatchEvent(event);

            const systemBtn = document.getElementById('tab-system');
            expect(systemBtn.getAttribute('aria-selected')).toBe('true');
        });
    });

    describe('window.showTab', () => {
        it('should be available globally', () => {
            expect(typeof window.showTab).toBe('function');
        });
    });

    describe('Branch coverage - edge cases', () => {
        it('should handle keyboard navigation when no tab is active', () => {
            initTabs();

            // Remove aria-selected from all buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.setAttribute('aria-selected', 'false');
            });

            const wifiBtn = document.getElementById('tab-wifi');
            const event = new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true });

            // Should not throw when no active tab
            expect(() => wifiBtn.dispatchEvent(event)).not.toThrow();
        });

        it('should use default tab when getCurrentTab finds no active button', () => {
            initTabs();

            // Remove active state from all tabs
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.setAttribute('aria-selected', 'false');
            });

            // Trigger a keyboard event - should default to first tab behavior
            const wifiBtn = document.getElementById('tab-wifi');
            const event = new KeyboardEvent('keydown', { key: 'Home', bubbles: true });
            wifiBtn.dispatchEvent(event);

            // Home key should navigate to first tab (wifi)
            expect(document.getElementById('tab-wifi').getAttribute('aria-selected')).toBe('true');
        });

        it('should handle ArrowUp the same as ArrowLeft', () => {
            initTabs();

            // First select VPN tab
            showTab('vpn');
            expect(document.getElementById('tab-vpn').getAttribute('aria-selected')).toBe('true');

            // Now press ArrowUp on VPN tab
            const vpnBtn = document.getElementById('tab-vpn');
            const event = new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true });
            vpnBtn.dispatchEvent(event);

            // Should navigate to wifi (previous tab)
            const wifiBtn = document.getElementById('tab-wifi');
            expect(wifiBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should handle ArrowDown the same as ArrowRight', () => {
            initTabs();

            // First select WiFi tab
            showTab('wifi');
            expect(document.getElementById('tab-wifi').getAttribute('aria-selected')).toBe('true');

            // Now press ArrowDown on WiFi tab
            const wifiBtn = document.getElementById('tab-wifi');
            const event = new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true });
            wifiBtn.dispatchEvent(event);

            // Should navigate to vpn (next tab)
            const vpnBtn = document.getElementById('tab-vpn');
            expect(vpnBtn.getAttribute('aria-selected')).toBe('true');
        });

        it('should ignore non-navigation keys', () => {
            initTabs();

            // First select WiFi tab
            showTab('wifi');
            expect(document.getElementById('tab-wifi').getAttribute('aria-selected')).toBe('true');

            // Press a non-navigation key
            const wifiBtn = document.getElementById('tab-wifi');
            const event = new KeyboardEvent('keydown', { key: 'a', bubbles: true });
            wifiBtn.dispatchEvent(event);

            // wifi should still be selected
            expect(wifiBtn.getAttribute('aria-selected')).toBe('true');
        });
    });
});
