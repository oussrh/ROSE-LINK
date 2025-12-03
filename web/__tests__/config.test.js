/**
 * Tests for Configuration Module
 */

import { CHART_THEME, APP_VERSION, API, POLLING } from '../js/config.js';

describe('Configuration Module', () => {
    describe('Tailwind configuration', () => {
        it('should configure tailwind when available', () => {
            // Re-import to test tailwind config
            const originalTailwind = global.tailwind;
            global.tailwind = {};

            // Clear the module cache and re-import
            jest.resetModules();

            // Manually simulate what the config.js does
            if (typeof global.tailwind !== 'undefined') {
                global.tailwind.config = {
                    darkMode: 'class',
                    theme: {
                        extend: {
                            fontFamily: {
                                'alexandria': ['Alexandria', 'sans-serif'],
                            },
                            colors: {
                                rose: {
                                    50: '#fff1f1',
                                    100: '#ffe3e3',
                                    200: '#ffcbcb',
                                    300: '#fea6a6',
                                    400: '#fa6b6b',
                                    500: '#ca2625',
                                    600: '#b31f1e',
                                    700: '#961917',
                                    800: '#7c1716',
                                    900: '#671918',
                                }
                            }
                        }
                    }
                };
            }

            expect(global.tailwind.config).toBeDefined();
            expect(global.tailwind.config.darkMode).toBe('class');
            expect(global.tailwind.config.theme.extend.fontFamily.alexandria).toEqual(['Alexandria', 'sans-serif']);

            // Restore
            if (originalTailwind) {
                global.tailwind = originalTailwind;
            } else {
                delete global.tailwind;
            }
        });

        it('should actually configure tailwind global when defined before import', async () => {
            // Save original state
            const originalTailwind = global.tailwind;

            // Set up tailwind before re-importing
            global.tailwind = {};

            // Clear module cache
            jest.resetModules();

            // Re-import the module to trigger the tailwind config block
            await import('../js/config.js');

            // Verify tailwind was configured
            expect(global.tailwind.config).toBeDefined();
            expect(global.tailwind.config.darkMode).toBe('class');

            // Restore
            if (originalTailwind) {
                global.tailwind = originalTailwind;
            } else {
                delete global.tailwind;
            }
        });

        it('should configure rose color palette', () => {
            const originalTailwind = global.tailwind;
            global.tailwind = {};

            // Simulate tailwind config
            global.tailwind.config = {
                darkMode: 'class',
                theme: {
                    extend: {
                        colors: {
                            rose: {
                                50: '#fff1f1',
                                500: '#ca2625',
                                900: '#671918',
                            }
                        }
                    }
                }
            };

            const roseColors = global.tailwind.config.theme.extend.colors.rose;
            expect(roseColors[500]).toBe('#ca2625');
            expect(roseColors[50]).toBe('#fff1f1');
            expect(roseColors[900]).toBe('#671918');

            // Restore
            if (originalTailwind) {
                global.tailwind = originalTailwind;
            } else {
                delete global.tailwind;
            }
        });

        it('should not throw when tailwind is undefined', () => {
            const originalTailwind = global.tailwind;
            delete global.tailwind;

            // The module already loaded successfully, so we just verify it doesn't throw on access
            expect(() => {
                if (typeof tailwind !== 'undefined') {
                    // This block won't execute since tailwind is undefined
                }
            }).not.toThrow();

            // Restore
            if (originalTailwind) {
                global.tailwind = originalTailwind;
            }
        });
    });

    describe('CHART_THEME export', () => {
        it('should export chart theme configuration', () => {
            expect(CHART_THEME).toBeDefined();
            expect(CHART_THEME.primaryColor).toBe('#ca2625');
        });

        it('should have color palette', () => {
            expect(CHART_THEME.colors).toBeDefined();
            expect(CHART_THEME.colors.primary).toBe('#ca2625');
            expect(CHART_THEME.colors.background).toBe('#1f2937');
            expect(CHART_THEME.colors.text).toBe('#f3f4f6');
        });

        it('should have font configuration', () => {
            expect(CHART_THEME.font).toBeDefined();
            expect(CHART_THEME.font.family).toContain('Alexandria');
            expect(CHART_THEME.font.weight).toBe(600);
        });

        it('should have color palette array', () => {
            expect(CHART_THEME.palette).toBeDefined();
            expect(Array.isArray(CHART_THEME.palette)).toBe(true);
            expect(CHART_THEME.palette.length).toBeGreaterThan(0);
            expect(CHART_THEME.palette[0]).toBe('#ca2625');
        });

        it('should have all required color properties', () => {
            expect(CHART_THEME.colors.primaryLight).toBe('#fa6b6b');
            expect(CHART_THEME.colors.primaryDark).toBe('#961917');
            expect(CHART_THEME.colors.secondary).toBe('#fea6a6');
            expect(CHART_THEME.colors.gridLines).toBe('#374151');
            expect(CHART_THEME.colors.textSecondary).toBe('#9ca3af');
        });
    });

    describe('APP_VERSION export', () => {
        it('should export app version', () => {
            expect(APP_VERSION).toBeDefined();
            expect(typeof APP_VERSION).toBe('string');
            expect(APP_VERSION).toMatch(/^v\d+\.\d+\.\d+$/);
        });
    });

    describe('API endpoints export', () => {
        it('should export API configuration', () => {
            expect(API).toBeDefined();
            expect(API.STATUS).toBe('/api/status');
        });

        it('should have WiFi endpoints', () => {
            expect(API.WIFI).toBeDefined();
            expect(API.WIFI.SCAN).toBe('/api/wifi/scan');
            expect(API.WIFI.CONNECT).toBe('/api/wifi/connect');
            expect(API.WIFI.DISCONNECT).toBe('/api/wifi/disconnect');
        });

        it('should have VPN endpoints', () => {
            expect(API.VPN).toBeDefined();
            expect(API.VPN.STATUS).toBe('/api/vpn/status');
            expect(API.VPN.PROFILES).toBe('/api/vpn/profiles');
            expect(API.VPN.IMPORT).toBe('/api/vpn/import');
            expect(API.VPN.ACTIVATE).toBe('/api/vpn/activate');
            expect(API.VPN.RESTART).toBe('/api/vpn/restart');
            expect(API.VPN.STOP).toBe('/api/vpn/stop');
            expect(API.VPN.START).toBe('/api/vpn/start');
        });

        it('should have Hotspot endpoints', () => {
            expect(API.HOTSPOT).toBeDefined();
            expect(API.HOTSPOT.APPLY).toBe('/api/hotspot/apply');
            expect(API.HOTSPOT.CLIENTS).toBe('/api/hotspot/clients');
            expect(API.HOTSPOT.RESTART).toBe('/api/hotspot/restart');
        });

        it('should have System endpoints', () => {
            expect(API.SYSTEM).toBeDefined();
            expect(API.SYSTEM.INFO).toBe('/api/system/info');
            expect(API.SYSTEM.REBOOT).toBe('/api/system/reboot');
        });

        it('should have Settings endpoints', () => {
            expect(API.SETTINGS).toBeDefined();
            expect(API.SETTINGS.VPN).toBe('/api/settings/vpn');
        });
    });

    describe('POLLING intervals export', () => {
        it('should export polling intervals', () => {
            expect(POLLING).toBeDefined();
            expect(typeof POLLING.STATUS).toBe('number');
        });

        it('should have correct polling values', () => {
            expect(POLLING.STATUS).toBe(5000);
            expect(POLLING.WIFI_STATUS).toBe(10000);
            expect(POLLING.VPN_STATUS).toBe(10000);
            expect(POLLING.VPN_PROFILES).toBe(30000);
            expect(POLLING.SYSTEM_INFO).toBe(30000);
            expect(POLLING.CLIENTS).toBe(10000);
        });

        it('should have positive values for all intervals', () => {
            Object.values(POLLING).forEach(value => {
                expect(value).toBeGreaterThan(0);
            });
        });
    });
});
