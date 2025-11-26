/**
 * ROSE Link - Global Type Declarations
 * Type definitions for external dependencies and global variables
 */

// htmx library types
declare const htmx: {
    process: (element: HTMLElement) => void;
    trigger: (selector: string, event: string) => void;
    ajax: (method: string, url: string, options?: object) => void;
    on: (event: string, handler: (evt: Event) => void) => void;
    off: (event: string, handler: (evt: Event) => void) => void;
};

// Lucide icons library types
declare const lucide: {
    createIcons: () => void;
};

// Global translation function (from i18n.js)
interface Window {
    t: (key: string, params?: Record<string, string | number>) => string;
    showTab: (tabName: string, focus?: boolean) => void;
    connectToWifi: (ssid: string, btn: HTMLElement) => void;
    disconnectWifi: (btn: HTMLElement) => void;
    setLanguage: (lang: string) => void;
}

// API Response types
interface ApiResponse<T = unknown> {
    status?: string;
    data?: T;
    error?: string;
    detail?: string;
}

// Status API types
interface WANStatus {
    ethernet: {
        connected: boolean;
        ip?: string;
        interface?: string;
    } | null;
    wifi: {
        connected: boolean;
        ssid?: string;
        ip?: string;
        signal?: number;
    } | null;
}

interface VPNStatus {
    active: boolean;
    endpoint?: string;
    profile?: string;
    transfer?: {
        received: string;
        sent: string;
    };
}

interface HotspotStatus {
    active: boolean;
    ssid?: string;
    channel?: number;
    frequency?: string;
    clients: number;
}

interface StatusResponse {
    wan: WANStatus;
    vpn: VPNStatus;
    ap: HotspotStatus;
}

// WiFi Network types
interface WiFiNetwork {
    ssid: string;
    signal: number;
    security: string;
}

// Hotspot Client types
interface HotspotClient {
    mac: string;
    ip?: string;
    hostname?: string;
    signal?: number;
    rx_bytes?: number;
    tx_bytes?: number;
}

// VPN Profile types
interface VPNProfile {
    name: string;
    active: boolean;
}

// System Info types
interface SystemInfo {
    hostname: string;
    model: string;
    os: string;
    cpu_temp: number;
    uptime: string;
    memory: {
        total: number;
        used: number;
        percent: number;
    };
    disk: {
        total: number;
        used: number;
        percent: number;
    };
}

// i18n types
type TranslationKey = string;
type TranslationParams = Record<string, string | number>;

// Toast types
type ToastType = 'success' | 'error' | 'info' | 'warning';

// Tab names
type TabName = 'wifi' | 'vpn' | 'hotspot' | 'system';

// Hotspot configuration
interface HotspotConfig {
    ssid: string;
    password: string;
    country: string;
    channel: number;
    band: '2.4' | '5';
    wpa3: boolean;
}

// VPN Settings
interface VPNSettings {
    watchdog_enabled: boolean;
    ping_host: string;
    check_interval: number;
}

// Event types for custom events
interface CustomEventMap {
    'rose:status:update': CustomEvent<StatusResponse>;
    'rose:bandwidth:update': CustomEvent<{ download: number; upload: number }>;
    'rose:language:change': CustomEvent<{ lang: string }>;
}

declare global {
    interface WindowEventMap extends CustomEventMap {}
}

export {};
