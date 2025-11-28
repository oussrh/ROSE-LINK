/**
 * E2E Test Helpers and Utilities
 * Common functions used across E2E tests
 */

/**
 * Wait for splash screen to disappear
 * @param {import('@playwright/test').Page} page - Playwright page object
 */
async function waitForAppReady(page) {
    await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
}

/**
 * Navigate to a specific tab
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} tabName - Tab name: 'wifi', 'vpn', 'hotspot', 'system'
 */
async function navigateToTab(page, tabName) {
    await page.click(`#tab-${tabName}`);
    await page.waitForSelector(`#content-${tabName}`, { state: 'visible' });
}

/**
 * Set language preference
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} lang - Language code: 'en' or 'fr'
 */
async function setLanguage(page, lang) {
    await page.click(`#lang-${lang}`);
    await page.waitForTimeout(500); // Allow time for i18n update
}

/**
 * Check if an element is loading (has loading indicator)
 * @param {import('@playwright/test').Locator} locator - Element locator
 */
async function isLoading(locator) {
    const hasAnimatePulse = await locator.locator('.animate-pulse').count() > 0;
    const hasLoadingText = (await locator.textContent()).includes('Loading');
    return hasAnimatePulse || hasLoadingText;
}

/**
 * Wait for HTMX content to load
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @param {number} timeout - Timeout in milliseconds
 */
async function waitForHtmxLoad(page, selector, timeout = 10000) {
    // Wait for element to not have loading indicator
    await page.waitForFunction(
        (sel) => {
            const el = document.querySelector(sel);
            if (!el) return false;
            const hasLoading = el.querySelector('.animate-pulse') !== null;
            const hasLoadingText = el.textContent.includes('Loading');
            return !hasLoading && !hasLoadingText;
        },
        selector,
        { timeout }
    );
}

/**
 * Mock API response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - URL pattern to intercept
 * @param {object} response - Response data
 * @param {number} status - HTTP status code
 */
async function mockApiResponse(page, url, response, status = 200) {
    await page.route(url, (route) => {
        route.fulfill({
            status,
            contentType: 'application/json',
            body: JSON.stringify(response),
        });
    });
}

/**
 * Mock API error response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - URL pattern to intercept
 * @param {string} message - Error message
 * @param {number} status - HTTP status code
 */
async function mockApiError(page, url, message, status = 500) {
    await page.route(url, (route) => {
        route.fulfill({
            status,
            contentType: 'application/json',
            body: JSON.stringify({ detail: message }),
        });
    });
}

/**
 * Intercept and capture API requests
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - URL pattern to intercept
 * @returns {Promise<object[]>} - Array of captured requests
 */
async function captureApiRequests(page, url) {
    const requests = [];
    await page.route(url, (route) => {
        requests.push({
            url: route.request().url(),
            method: route.request().method(),
            postData: route.request().postData(),
            headers: route.request().headers(),
        });
        route.continue();
    });
    return requests;
}

/**
 * Fill form and submit
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {object} fields - Field selectors and values
 * @param {string} submitSelector - Submit button selector
 */
async function fillAndSubmitForm(page, fields, submitSelector) {
    for (const [selector, value] of Object.entries(fields)) {
        const input = page.locator(selector);
        await input.clear();
        await input.fill(value);
    }
    await page.click(submitSelector);
}

/**
 * Check for toast notification
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} type - Toast type: 'success', 'error', 'info'
 * @param {string} text - Expected text content (optional)
 */
async function expectToast(page, type, text = null) {
    const toastSelector = `[data-toast-type="${type}"], .toast-${type}, .bg-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue'}-500`;
    const toast = page.locator(toastSelector).first();

    await expect(toast).toBeVisible({ timeout: 5000 });

    if (text) {
        await expect(toast).toContainText(text);
    }
}

/**
 * Common selectors used across tests
 */
const SELECTORS = {
    // Navigation
    tabs: {
        wifi: '#tab-wifi',
        vpn: '#tab-vpn',
        hotspot: '#tab-hotspot',
        system: '#tab-system',
    },
    content: {
        wifi: '#content-wifi',
        vpn: '#content-vpn',
        hotspot: '#content-hotspot',
        system: '#content-system',
    },
    language: {
        en: '#lang-en',
        fr: '#lang-fr',
    },

    // WiFi
    wifi: {
        currentStatus: '#wifi-current-status',
        networks: '#wifi-networks',
        scanBtn: 'button:has-text("Scan"), button:has-text("Rechercher")',
    },

    // VPN
    vpn: {
        status: '#vpn-status-detail',
        profiles: '#vpn-profiles',
        fileInput: 'input[type="file"][accept=".conf"]',
        importBtn: 'button:has-text("Import"), button:has-text("Importer")',
    },

    // Hotspot
    hotspot: {
        form: '#hotspot-form',
        ssid: '#hotspot-ssid',
        password: '#hotspot-password',
        countryCode: '#country-code',
        band: '#wifi-band',
        channel: '#wifi-channel',
        wpa3: '#wpa3',
        submitBtn: '#hotspot-submit-btn',
        clients: '#connected-clients',
        message: '#hotspot-message',
    },

    // System
    system: {
        info: '#system-info',
        vpnForm: '#vpn-settings-form',
        pingHost: '#vpn-ping-host',
        checkInterval: '#vpn-check-interval',
        vpnSettingsBtn: '#vpn-settings-submit-btn',
        vpnMessage: '#vpn-settings-message',
        actionMessage: '#system-action-message',
        wizardBtn: '#run-wizard-btn',
    },

    // Status Cards
    statusCards: '#status-cards',

    // Common
    splashScreen: '#splash-screen',
    toastContainer: '#toast-container, [role="alert"]',
};

/**
 * Test data fixtures
 */
const TEST_DATA = {
    wifi: {
        networks: [
            { ssid: 'TestNetwork1', signal: -45, security: 'WPA2' },
            { ssid: 'TestNetwork2', signal: -60, security: 'WPA3' },
            { ssid: 'OpenNetwork', signal: -70, security: 'Open' },
        ],
        connection: {
            ssid: 'TestNetwork1',
            password: 'test123456',
        },
    },
    vpn: {
        profile: {
            name: 'test-vpn',
            content: `[Interface]
PrivateKey = test123
Address = 10.0.0.2/24

[Peer]
PublicKey = peer123
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0`,
        },
        settings: {
            ping_host: '1.1.1.1',
            check_interval: 120,
        },
    },
    hotspot: {
        config: {
            ssid: 'ROSE-Test',
            password: 'testpass123',
            country: 'US',
            band: '2.4GHz',
            channel: 6,
            wpa3: false,
        },
    },
    system: {
        info: {
            model: 'Raspberry Pi 4 Model B',
            model_short: 'Pi 4B',
            architecture: 'aarch64',
            ram_mb: 4096,
            ram_free_mb: 2048,
            disk_total_gb: 32,
            disk_free_gb: 20,
            cpu_temp_c: 45,
            uptime_seconds: 86400,
            wifi_capabilities: {
                supports_5ghz: true,
                supports_ac: true,
                supports_ax: false,
                ap_mode: true,
            },
        },
    },
};

module.exports = {
    waitForAppReady,
    navigateToTab,
    setLanguage,
    isLoading,
    waitForHtmxLoad,
    mockApiResponse,
    mockApiError,
    captureApiRequests,
    fillAndSubmitForm,
    expectToast,
    SELECTORS,
    TEST_DATA,
};
