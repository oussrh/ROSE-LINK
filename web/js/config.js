/**
 * ROSE Link - Configuration
 * Tailwind configuration and app constants
 */

// Tailwind CSS configuration
if (typeof tailwind !== 'undefined') {
    tailwind.config = {
        darkMode: 'class',
        theme: {
            extend: {
                colors: {
                    rose: {
                        50: '#fff1f2',
                        100: '#ffe4e6',
                        200: '#fecdd3',
                        300: '#fda4af',
                        400: '#fb7185',
                        500: '#f43f5e',
                        600: '#e11d48',
                        700: '#be123c',
                        800: '#9f1239',
                        900: '#881337',
                    }
                }
            }
        }
    };
}

// App version
export const APP_VERSION = 'v0.2.0';

// API endpoints
export const API = {
    STATUS: '/api/status',
    WIFI: {
        SCAN: '/api/wifi/scan',
        CONNECT: '/api/wifi/connect',
        DISCONNECT: '/api/wifi/disconnect'
    },
    VPN: {
        STATUS: '/api/vpn/status',
        PROFILES: '/api/vpn/profiles',
        IMPORT: '/api/vpn/import',
        ACTIVATE: '/api/vpn/activate',
        RESTART: '/api/vpn/restart',
        STOP: '/api/vpn/stop',
        START: '/api/vpn/start'
    },
    HOTSPOT: {
        APPLY: '/api/hotspot/apply',
        CLIENTS: '/api/hotspot/clients',
        RESTART: '/api/hotspot/restart'
    },
    SYSTEM: {
        INFO: '/api/system/info',
        REBOOT: '/api/system/reboot'
    },
    SETTINGS: {
        VPN: '/api/settings/vpn'
    }
};

// Polling intervals (ms)
export const POLLING = {
    STATUS: 5000,
    WIFI_STATUS: 10000,
    VPN_STATUS: 10000,
    VPN_PROFILES: 30000,
    SYSTEM_INFO: 30000,
    CLIENTS: 10000
};
