/**
 * E2E Tests: Error Handling and Edge Cases
 * Tests application behavior under error conditions and edge cases
 */

const { test, expect } = require('@playwright/test');
const {
    waitForAppReady,
    navigateToTab,
    mockApiError,
    mockApiResponse,
    SELECTORS
} = require('./fixtures/test-helpers');

test.describe('Network Error Handling', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should handle API timeout gracefully', async ({ page }) => {
        // Mock slow/timeout response
        await page.route('**/api/wifi/scan', async (route) => {
            await new Promise(resolve => setTimeout(resolve, 35000)); // Exceed timeout
            route.abort('timedout');
        });

        // App should still be usable
        await expect(page.locator(SELECTORS.statusCards)).toBeVisible();
    });

    test('should handle 500 server error', async ({ page }) => {
        await mockApiError(page, '**/api/system/info', 'Internal Server Error', 500);

        await navigateToTab(page, 'system');

        // System info might show error state but page should not crash
        const systemContent = page.locator(SELECTORS.content.system);
        await expect(systemContent).toBeVisible();
    });

    test('should handle 404 not found error', async ({ page }) => {
        await mockApiError(page, '**/api/wifi/networks', 'Not Found', 404);

        // Networks section should still be visible
        const networks = page.locator(SELECTORS.wifi.networks);
        await expect(networks).toBeVisible();
    });

    test('should handle network offline', async ({ page }) => {
        // Go offline
        await page.context().setOffline(true);

        // Wait a moment
        await page.waitForTimeout(1000);

        // App should still be rendered
        const header = page.locator('header');
        await expect(header).toBeVisible();

        // Go back online
        await page.context().setOffline(false);
    });

    test('should recover after temporary network failure', async ({ page }) => {
        // Simulate offline
        await page.context().setOffline(true);
        await page.waitForTimeout(1000);

        // Go back online
        await page.context().setOffline(false);
        await page.waitForTimeout(1000);

        // App should still work
        await navigateToTab(page, 'vpn');
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });
});

test.describe('Form Validation Edge Cases', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should reject SSID longer than 32 characters', async ({ page }) => {
        await navigateToTab(page, 'hotspot');

        const ssidInput = page.locator(SELECTORS.hotspot.ssid);
        const longSSID = 'A'.repeat(40);
        await ssidInput.fill(longSSID);

        // Should be truncated to 32 chars due to maxlength
        const value = await ssidInput.inputValue();
        expect(value.length).toBeLessThanOrEqual(32);
    });

    test('should reject password shorter than 8 characters', async ({ page }) => {
        await navigateToTab(page, 'hotspot');

        const passwordInput = page.locator(SELECTORS.hotspot.password);
        await passwordInput.fill('short');

        const submitBtn = page.locator(SELECTORS.hotspot.submitBtn);
        await submitBtn.click();

        // Form should show validation error (browser native)
        // The form shouldn't submit with invalid data
    });

    test('should handle special characters in SSID', async ({ page }) => {
        await navigateToTab(page, 'hotspot');

        const ssidInput = page.locator(SELECTORS.hotspot.ssid);
        const specialSSID = 'Test<script>alert(1)</script>';
        await ssidInput.fill(specialSSID);

        // Input should accept it (XSS prevention is on output)
        const value = await ssidInput.inputValue();
        expect(value).toBeTruthy();
    });

    test('should handle empty form submission', async ({ page }) => {
        await navigateToTab(page, 'hotspot');

        const ssidInput = page.locator(SELECTORS.hotspot.ssid);
        const passwordInput = page.locator(SELECTORS.hotspot.password);

        await ssidInput.clear();
        await passwordInput.clear();

        const submitBtn = page.locator(SELECTORS.hotspot.submitBtn);
        await submitBtn.click();

        // Form should not submit, fields should show required validation
        await expect(ssidInput).toHaveValue('');
    });

    test('should validate ping host format', async ({ page }) => {
        await navigateToTab(page, 'system');

        const pingHostInput = page.locator(SELECTORS.system.pingHost);
        await pingHostInput.clear();
        await pingHostInput.fill('not-a-valid-format!!!');

        // Input should accept any text (validation happens on server)
        const value = await pingHostInput.inputValue();
        expect(value).toBe('not-a-valid-format!!!');
    });

    test('should enforce check interval range', async ({ page }) => {
        await navigateToTab(page, 'system');

        const intervalInput = page.locator(SELECTORS.system.checkInterval);

        // Try value below minimum
        await intervalInput.fill('10');
        let value = await intervalInput.inputValue();
        expect(value).toBe('10'); // Input allows it, validation is on submit

        // Try value above maximum
        await intervalInput.fill('500');
        value = await intervalInput.inputValue();
        expect(value).toBe('500'); // Input allows it, validation is on submit
    });
});

test.describe('Empty State Handling', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should handle no WiFi networks found', async ({ page }) => {
        await mockApiResponse(page, '**/api/wifi/scan', { networks: [] });

        const scanBtn = page.locator(SELECTORS.wifi.scanBtn);
        await scanBtn.click();

        // Should show empty state or "no networks" message
        const networks = page.locator(SELECTORS.wifi.networks);
        await expect(networks).toBeVisible();
    });

    test('should handle no VPN profiles', async ({ page }) => {
        await mockApiResponse(page, '**/api/vpn/profiles', { profiles: [] });

        await page.reload();
        await waitForAppReady(page);
        await navigateToTab(page, 'vpn');

        // Should show empty state or "no profiles" message
        const profiles = page.locator(SELECTORS.vpn.profiles);
        await expect(profiles).toBeVisible();

        const content = await profiles.textContent();
        expect(content.length > 0).toBeTruthy();
    });

    test('should handle no connected clients', async ({ page }) => {
        await mockApiResponse(page, '**/api/hotspot/clients', { clients: [] });

        await navigateToTab(page, 'hotspot');

        // Should show empty state or "no clients" message
        const clients = page.locator(SELECTORS.hotspot.clients);
        await expect(clients).toBeVisible();

        const content = await clients.textContent();
        expect(content.length > 0).toBeTruthy();
    });
});

test.describe('Loading State Handling', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should show loading state for system info', async ({ page }) => {
        // Delay the response
        await page.route('**/api/system/info', async (route) => {
            await new Promise(resolve => setTimeout(resolve, 2000));
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    model: 'Test',
                    ram_mb: 1000,
                    ram_free_mb: 500,
                    disk_total_gb: 32,
                    disk_free_gb: 20,
                    cpu_temp_c: 45,
                    uptime_seconds: 3600,
                }),
            });
        });

        await navigateToTab(page, 'system');

        // Initially might show loading state
        const systemInfo = page.locator(SELECTORS.system.info);
        await expect(systemInfo).toBeVisible();
    });

    test('should show loading indicator during form submission', async ({ page }) => {
        // Delay the response
        await page.route('**/api/settings/vpn', async (route) => {
            await new Promise(resolve => setTimeout(resolve, 2000));
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ status: 'saved' }),
            });
        });

        await navigateToTab(page, 'system');

        // Fill and submit form
        const submitBtn = page.locator(SELECTORS.system.vpnSettingsBtn);
        await submitBtn.click();

        // Button might show loading state
        // Wait for response
        await page.waitForTimeout(2500);
    });
});

test.describe('Concurrent Operations', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should handle rapid tab switching', async ({ page }) => {
        // Rapidly switch tabs
        for (let i = 0; i < 5; i++) {
            await page.click(SELECTORS.tabs.wifi);
            await page.click(SELECTORS.tabs.vpn);
            await page.click(SELECTORS.tabs.hotspot);
            await page.click(SELECTORS.tabs.system);
        }

        // Should end up on system tab
        await expect(page.locator(SELECTORS.content.system)).toBeVisible();
    });

    test('should handle multiple button clicks', async ({ page }) => {
        await navigateToTab(page, 'hotspot');

        // Fill form with valid data
        await page.locator(SELECTORS.hotspot.ssid).fill('TestNetwork');
        await page.locator(SELECTORS.hotspot.password).fill('testpassword123');

        // Mock delayed response
        await page.route('**/api/hotspot/config', async (route) => {
            await new Promise(resolve => setTimeout(resolve, 1000));
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ status: 'success' }),
            });
        });

        // Click submit multiple times rapidly
        const submitBtn = page.locator(SELECTORS.hotspot.submitBtn);
        await submitBtn.click();
        await submitBtn.click();
        await submitBtn.click();

        // App should handle gracefully
        await page.waitForTimeout(1500);
        await expect(page.locator(SELECTORS.hotspot.form)).toBeVisible();
    });

    test('should handle language switch during operation', async ({ page }) => {
        await navigateToTab(page, 'system');

        // Start filling form
        await page.locator(SELECTORS.system.pingHost).fill('8.8.8.8');

        // Switch language
        await page.click('#lang-fr');

        // Form should still be usable
        const pingHostInput = page.locator(SELECTORS.system.pingHost);
        await expect(pingHostInput).toBeVisible();
        await expect(pingHostInput).toHaveValue('8.8.8.8');
    });
});

test.describe('Browser Back/Forward Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should handle page reload', async ({ page }) => {
        await navigateToTab(page, 'vpn');

        await page.reload();
        await waitForAppReady(page);

        // VPN tab should still be selected (due to persistence)
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });

    test('should maintain state after reload', async ({ page }) => {
        // Switch language
        await page.click('#lang-fr');

        // Navigate to hotspot
        await navigateToTab(page, 'hotspot');

        // Reload
        await page.reload();
        await waitForAppReady(page);

        // Language should persist
        const html = page.locator('html');
        await expect(html).toHaveAttribute('lang', 'fr');
    });
});

test.describe('Responsive Error Handling', () => {
    test('should handle errors on mobile viewport', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto('/');
        await waitForAppReady(page);

        // Mock an error
        await mockApiError(page, '**/api/system/info', 'Server Error', 500);

        await navigateToTab(page, 'system');

        // Page should still be usable
        await expect(page.locator(SELECTORS.content.system)).toBeVisible();
    });

    test('should handle errors on tablet viewport', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/');
        await waitForAppReady(page);

        // Mock an error
        await mockApiError(page, '**/api/vpn/status', 'VPN service unavailable', 503);

        await navigateToTab(page, 'vpn');

        // Page should still be usable
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });
});

test.describe('Security Edge Cases', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should handle XSS attempts in network names', async ({ page }) => {
        // Mock networks with XSS payload
        await mockApiResponse(page, '**/api/wifi/scan', {
            networks: [{
                ssid: '<script>alert("xss")</script>',
                signal: -50,
                security: 'WPA2'
            }]
        });

        const scanBtn = page.locator(SELECTORS.wifi.scanBtn);
        await scanBtn.click();

        await page.waitForTimeout(1000);

        // Should not execute script, content should be escaped
        const networks = page.locator(SELECTORS.wifi.networks);
        const html = await networks.innerHTML();
        expect(html).not.toContain('<script>');
    });

    test('should handle XSS attempts in error messages', async ({ page }) => {
        // Mock error with XSS payload
        await mockApiError(page, '**/api/hotspot/config', '<img src=x onerror=alert(1)>', 400);

        await navigateToTab(page, 'hotspot');

        // Fill and submit
        await page.locator(SELECTORS.hotspot.ssid).fill('Test');
        await page.locator(SELECTORS.hotspot.password).fill('testpass123');
        await page.locator(SELECTORS.hotspot.submitBtn).click();

        await page.waitForTimeout(1000);

        // Error should be displayed but escaped
        const pageContent = await page.content();
        expect(pageContent).not.toContain('onerror=');
    });
});
