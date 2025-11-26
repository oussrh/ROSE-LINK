/**
 * Tests for Configuration Module
 */

describe('Configuration Module', () => {
    let originalTailwind;

    beforeEach(() => {
        originalTailwind = global.tailwind;
        jest.resetModules();
    });

    afterEach(() => {
        if (originalTailwind) {
            global.tailwind = originalTailwind;
        } else {
            delete global.tailwind;
        }
    });

    describe('Tailwind configuration', () => {
        it('should configure tailwind when available', async () => {
            global.tailwind = {};

            await import('../../js/config.js');

            expect(global.tailwind.config).toBeDefined();
            expect(global.tailwind.config.darkMode).toBe('class');
            expect(global.tailwind.config.theme.extend.fontFamily.alexandria).toEqual(['Alexandria', 'sans-serif']);
        });

        it('should configure rose color palette', async () => {
            global.tailwind = {};

            await import('../../js/config.js');

            const roseColors = global.tailwind.config.theme.extend.colors.rose;
            expect(roseColors[500]).toBe('#ca2625');
            expect(roseColors[50]).toBe('#fff1f1');
            expect(roseColors[900]).toBe('#671918');
        });

        it('should not throw when tailwind is undefined', async () => {
            delete global.tailwind;

            await expect(import('../../js/config.js')).resolves.not.toThrow();
        });
    });

    describe('CHART_THEME export', () => {
        it('should export chart theme configuration', async () => {
            const { CHART_THEME } = await import('../../js/config.js');

            expect(CHART_THEME).toBeDefined();
            expect(CHART_THEME.primaryColor).toBe('#ca2625');
        });

        it('should have color palette', async () => {
            const { CHART_THEME } = await import('../../js/config.js');

            expect(CHART_THEME.colors).toBeDefined();
            expect(CHART_THEME.colors.primary).toBe('#ca2625');
            expect(CHART_THEME.colors.background).toBe('#1f2937');
            expect(CHART_THEME.colors.text).toBe('#f3f4f6');
        });

        it('should have font configuration', async () => {
            const { CHART_THEME } = await import('../../js/config.js');

            expect(CHART_THEME.font).toBeDefined();
            expect(CHART_THEME.font.family).toContain('Alexandria');
            expect(CHART_THEME.font.weight).toBe(600);
        });

        it('should have color palette array', async () => {
            const { CHART_THEME } = await import('../../js/config.js');

            expect(CHART_THEME.palette).toBeDefined();
            expect(Array.isArray(CHART_THEME.palette)).toBe(true);
            expect(CHART_THEME.palette.length).toBeGreaterThan(0);
            expect(CHART_THEME.palette[0]).toBe('#ca2625');
        });
    });

    describe('APP_VERSION export', () => {
        it('should export app version', async () => {
            const { APP_VERSION } = await import('../../js/config.js');

            expect(APP_VERSION).toBeDefined();
            expect(typeof APP_VERSION).toBe('string');
            expect(APP_VERSION).toMatch(/^v\d+\.\d+\.\d+$/);
        });
    });

    describe('API endpoints export', () => {
        it('should export API configuration', async () => {
            const { API } = await import('../../js/config.js');

            expect(API).toBeDefined();
            expect(API.STATUS).toBe('/api/status');
        });

        it('should have WiFi endpoints', async () => {
            const { API } = await import('../../js/config.js');

            expect(API.WIFI).toBeDefined();
            expect(API.WIFI.SCAN).toBe('/api/wifi/scan');
            expect(API.WIFI.CONNECT).toBe('/api/wifi/connect');
            expect(API.WIFI.DISCONNECT).toBe('/api/wifi/disconnect');
        });

        it('should have VPN endpoints', async () => {
            const { API } = await import('../../js/config.js');

            expect(API.VPN).toBeDefined();
            expect(API.VPN.STATUS).toBe('/api/vpn/status');
            expect(API.VPN.PROFILES).toBe('/api/vpn/profiles');
            expect(API.VPN.IMPORT).toBe('/api/vpn/import');
            expect(API.VPN.ACTIVATE).toBe('/api/vpn/activate');
            expect(API.VPN.RESTART).toBe('/api/vpn/restart');
            expect(API.VPN.STOP).toBe('/api/vpn/stop');
            expect(API.VPN.START).toBe('/api/vpn/start');
        });

        it('should have Hotspot endpoints', async () => {
            const { API } = await import('../../js/config.js');

            expect(API.HOTSPOT).toBeDefined();
            expect(API.HOTSPOT.APPLY).toBe('/api/hotspot/apply');
            expect(API.HOTSPOT.CLIENTS).toBe('/api/hotspot/clients');
            expect(API.HOTSPOT.RESTART).toBe('/api/hotspot/restart');
        });

        it('should have System endpoints', async () => {
            const { API } = await import('../../js/config.js');

            expect(API.SYSTEM).toBeDefined();
            expect(API.SYSTEM.INFO).toBe('/api/system/info');
            expect(API.SYSTEM.REBOOT).toBe('/api/system/reboot');
        });

        it('should have Settings endpoints', async () => {
            const { API } = await import('../../js/config.js');

            expect(API.SETTINGS).toBeDefined();
            expect(API.SETTINGS.VPN).toBe('/api/settings/vpn');
        });
    });

    describe('POLLING intervals export', () => {
        it('should export polling intervals', async () => {
            const { POLLING } = await import('../../js/config.js');

            expect(POLLING).toBeDefined();
            expect(typeof POLLING.STATUS).toBe('number');
        });

        it('should have correct polling values', async () => {
            const { POLLING } = await import('../../js/config.js');

            expect(POLLING.STATUS).toBe(5000);
            expect(POLLING.WIFI_STATUS).toBe(10000);
            expect(POLLING.VPN_STATUS).toBe(10000);
            expect(POLLING.VPN_PROFILES).toBe(30000);
            expect(POLLING.SYSTEM_INFO).toBe(30000);
            expect(POLLING.CLIENTS).toBe(10000);
        });
    });
});
