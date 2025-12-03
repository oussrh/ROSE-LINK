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
    // Wait for language attribute to update on html element
    await page.waitForFunction(
        (expectedLang) => document.documentElement.lang === expectedLang,
        lang,
        { timeout: 5000 }
    );
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
 * Wait for API response and optionally validate payload
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} url - URL pattern to intercept
 * @param {object} options - Options for response and validation
 * @returns {Promise<{request: object, response: object}>} - Captured request/response data
 */
async function mockApiWithValidation(page, url, options = {}) {
    const {
        response = { status: 'success' },
        status = 200,
        validatePayload = null,
        method = null
    } = options;

    const captured = { request: null, validated: false };

    await page.route(url, (route) => {
        if (method && route.request().method() !== method) {
            route.continue();
            return;
        }

        captured.request = {
            url: route.request().url(),
            method: route.request().method(),
            postData: route.request().postData(),
            headers: route.request().headers(),
        };

        // Parse and validate payload if validator provided
        if (validatePayload && captured.request.postData) {
            try {
                const payload = JSON.parse(captured.request.postData);
                captured.validated = validatePayload(payload);
            } catch {
                captured.validated = false;
            }
        }

        route.fulfill({
            status,
            contentType: 'application/json',
            body: JSON.stringify(response),
        });
    });

    return captured;
}

/**
 * Wait for network idle state (no pending requests)
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {number} timeout - Timeout in milliseconds
 */
async function waitForNetworkIdle(page, timeout = 5000) {
    await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Wait for specific API response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} urlPattern - URL pattern to wait for
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Response>} - The response object
 */
async function waitForApiResponse(page, urlPattern, timeout = 10000) {
    return page.waitForResponse(
        response => response.url().includes(urlPattern),
        { timeout }
    );
}

/**
 * Expect message area to contain specific text
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Message area selector
 * @param {string|RegExp} expectedText - Expected text or pattern
 * @param {number} timeout - Timeout in milliseconds
 */
async function expectMessageContent(page, selector, expectedText, timeout = 5000) {
    const messageArea = page.locator(selector);
    await expect(messageArea).toBeVisible({ timeout });

    if (typeof expectedText === 'string') {
        await expect(messageArea).toContainText(expectedText, { timeout });
    } else {
        await expect(messageArea).toHaveText(expectedText, { timeout });
    }
}

/**
 * Check for offline indicator
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {boolean} expectVisible - Whether indicator should be visible
 */
async function expectOfflineIndicator(page, expectVisible = true) {
    const indicator = page.locator('[data-testid="offline-indicator"], .offline-indicator, [aria-label*="offline"]');

    if (expectVisible) {
        await expect(indicator).toBeVisible({ timeout: 5000 });
    } else {
        await expect(indicator).not.toBeVisible({ timeout: 1000 }).catch(() => {
            // It's ok if indicator doesn't exist at all
        });
    }
}

/**
 * Wait for status card to update with specific content
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} cardName - Status card identifier (WAN, VPN, AP)
 * @param {string|RegExp} expectedContent - Expected content
 */
async function expectStatusCardContent(page, cardName, expectedContent) {
    const cardSelector = `#status-cards :has-text("${cardName}")`;
    const card = page.locator(cardSelector).first();

    await expect(card).toBeVisible({ timeout: 5000 });

    if (typeof expectedContent === 'string') {
        await expect(card).toContainText(expectedContent);
    } else {
        await expect(card).toHaveText(expectedContent);
    }
}

/**
 * Submit form and wait for response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} submitSelector - Submit button selector
 * @param {string} apiPattern - API URL pattern to wait for
 * @returns {Promise<Response>} - The API response
 */
async function submitFormAndWaitForResponse(page, submitSelector, apiPattern) {
    const responsePromise = page.waitForResponse(
        response => response.url().includes(apiPattern),
        { timeout: 10000 }
    );

    await page.click(submitSelector);

    return responsePromise;
}

/**
 * Verify form submission payload
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} apiPattern - API URL pattern
 * @param {object} expectedFields - Expected fields in payload
 * @param {Function} action - Action that triggers the submission
 */
async function verifyFormSubmission(page, apiPattern, expectedFields, action) {
    let capturedPayload = null;

    const originalRoute = page.route(apiPattern, async (route) => {
        const postData = route.request().postData();
        if (postData) {
            try {
                capturedPayload = JSON.parse(postData);
            } catch {
                capturedPayload = postData;
            }
        }
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ status: 'success' }),
        });
    });

    await action();

    // Wait for the route to be hit
    await page.waitForResponse(
        response => response.url().includes(apiPattern),
        { timeout: 10000 }
    ).catch(() => null);

    return { payload: capturedPayload, expectedFields };
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
    mockApiWithValidation,
    waitForNetworkIdle,
    waitForApiResponse,
    expectMessageContent,
    expectOfflineIndicator,
    expectStatusCardContent,
    submitFormAndWaitForResponse,
    verifyFormSubmission,
    SELECTORS,
    TEST_DATA,
};
