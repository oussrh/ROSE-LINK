/**
 * Tests for Status Cards Component
 */

// Mock dependencies before importing
jest.mock('../../js/utils/dom.js', () => ({
    escapeHtml: jest.fn(text => text || ''),
    icon: jest.fn(name => `<i data-lucide="${name}"></i>`),
    refreshIcons: jest.fn()
}));

jest.mock('../../js/i18n.js', () => ({
    t: jest.fn(key => key)
}));

import { renderStatusCards } from '../../js/components/statusCards.js';
import { escapeHtml, icon, refreshIcons } from '../../js/utils/dom.js';
import { t } from '../../js/i18n.js';

describe('Status Cards Component', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="status-cards"></div>';
        jest.clearAllMocks();
    });

    describe('renderStatusCards', () => {
        it('should render container with three cards', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            const container = document.getElementById('status-cards');
            expect(container.children.length).toBe(3);
        });

        it('should show ethernet connected status', () => {
            const data = {
                wan: {
                    ethernet: { connected: true, ip: '192.168.1.100' },
                    wifi: { connected: false }
                },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            const container = document.getElementById('status-cards');
            expect(container.innerHTML).toContain('bg-green-500');
            expect(t).toHaveBeenCalledWith('ethernet_connected');
        });

        it('should show wifi connected status when ethernet is not connected', () => {
            const data = {
                wan: {
                    ethernet: { connected: false },
                    wifi: { connected: true, ssid: 'MyNetwork', ip: '192.168.1.101' }
                },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            const container = document.getElementById('status-cards');
            expect(container.innerHTML).toContain('bg-blue-500');
            expect(escapeHtml).toHaveBeenCalledWith('MyNetwork');
        });

        it('should show disconnected status when nothing is connected', () => {
            const data = {
                wan: {
                    ethernet: { connected: false },
                    wifi: { connected: false }
                },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            const container = document.getElementById('status-cards');
            expect(container.innerHTML).toContain('bg-red-500');
            expect(t).toHaveBeenCalledWith('disconnected');
        });

        it('should show VPN active status', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: true, transfer: { received: '1.5 MB' } },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            expect(t).toHaveBeenCalledWith('vpn_active');
            const container = document.getElementById('status-cards');
            expect(container.innerHTML).toContain('pulse-slow');
        });

        it('should show VPN inactive status', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            expect(t).toHaveBeenCalledWith('vpn_inactive');
        });

        it('should show hotspot active status with client count', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: true, ssid: 'ROSE-Link', clients: 3 }
            };

            renderStatusCards(data);

            expect(t).toHaveBeenCalledWith('clients_connected');
            const container = document.getElementById('status-cards');
            expect(container.innerHTML).toContain('3');
        });

        it('should show hotspot inactive status', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            expect(t).toHaveBeenCalledWith('hotspot_inactive');
        });

        it('should call refreshIcons after rendering', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            expect(refreshIcons).toHaveBeenCalled();
        });

        it('should escape all API data to prevent XSS', () => {
            const data = {
                wan: {
                    ethernet: { connected: true, ip: '<script>alert("xss")</script>' },
                    wifi: { connected: false }
                },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            expect(escapeHtml).toHaveBeenCalledWith('<script>alert("xss")</script>');
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            expect(() => renderStatusCards(data)).not.toThrow();
        });

        it('should handle null/undefined values in data', () => {
            const data = {
                wan: { ethernet: null, wifi: undefined },
                vpn: { active: false, transfer: null },
                ap: { active: false, clients: null, ssid: null }
            };

            expect(() => renderStatusCards(data)).not.toThrow();
        });

        it('should render icons for each status card', () => {
            const data = {
                wan: { ethernet: { connected: false }, wifi: { connected: false } },
                vpn: { active: false, transfer: {} },
                ap: { active: false, clients: 0 }
            };

            renderStatusCards(data);

            expect(icon).toHaveBeenCalledWith('wifi');
            expect(icon).toHaveBeenCalledWith('shield-check');
            expect(icon).toHaveBeenCalledWith('radio-tower');
        });
    });
});
