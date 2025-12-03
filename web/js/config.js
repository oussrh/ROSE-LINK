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

// Chart.js Theme Configuration
export const CHART_THEME = {
    // Main brand color
    primaryColor: '#ca2625',

    // Color palette for charts (based on primary)
    colors: {
        primary: '#ca2625',
        primaryLight: '#fa6b6b',
        primaryDark: '#961917',
        secondary: '#fea6a6',
        background: '#1f2937',
        gridLines: '#374151',
        text: '#f3f4f6',
        textSecondary: '#9ca3af',
    },

    // Font configuration
    font: {
        family: "'Alexandria', sans-serif",
        weight: 600, // Semi Bold
    },

    // Chart color schemes for different data series
    palette: [
        '#ca2625', // Primary red
        '#fa6b6b', // Light red
        '#fea6a6', // Lighter red
        '#ffcbcb', // Very light red
        '#b31f1e', // Dark red
        '#961917', // Darker red
    ],
};

// App version - fetched dynamically from backend API
// This will be updated by fetchAppVersion() on page load
export let APP_VERSION = 'loading...';

/**
 * Fetch the app version from the backend API
 * Updates APP_VERSION and any DOM elements with data-version attribute
 */
export async function fetchAppVersion() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            const data = await response.json();
            APP_VERSION = data.version ? `v${data.version}` : 'v1.0.0';
        }
    } catch {
        APP_VERSION = 'v1.0.0'; // Fallback
    }

    // Update any DOM elements displaying the version
    document.querySelectorAll('[data-version]').forEach(el => {
        el.textContent = APP_VERSION;
    });

    return APP_VERSION;
}

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
