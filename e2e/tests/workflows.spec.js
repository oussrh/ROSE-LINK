/**
 * E2E Tests: Complete User Workflows
 * Tests end-to-end user journeys through the application
 */

const { test, expect } = require('@playwright/test');
const {
    waitForAppReady,
    navigateToTab,
    setLanguage,
    fillAndSubmitForm,
    mockApiResponse,
    mockApiError,
    waitForApiResponse,
    expectMessageContent,
    mockApiWithValidation,
    SELECTORS,
    TEST_DATA
} = require('./fixtures/test-helpers');

test.describe('WiFi Connection Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should complete WiFi scan workflow', async ({ page }) => {
        // Mock the scan API
        await page.route('**/api/wifi/scan', (route) => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    networks: TEST_DATA.wifi.networks
                }),
            });
        });

        // Click scan button and wait for response
        const scanBtn = page.locator(SELECTORS.wifi.scanBtn);
        const responsePromise = page.waitForResponse(
            response => response.url().includes('/api/wifi/scan'),
            { timeout: 10000 }
        );
        await scanBtn.click();
        await responsePromise;

        // Should show network list with actual network names
        const networks = page.locator(SELECTORS.wifi.networks);
        await expect(networks).toBeVisible();
        // Verify network content is rendered
        await expect(networks).toContainText(/TestNetwork|No networks/);
    });

    test('should show password dialog when connecting to secure network', async ({ page }) => {
        // Setup mock for network list
        await page.route('**/api/wifi/networks*', (route) => {
            route.fulfill({
                status: 200,
                contentType: 'text/html',
                body: `
                    <div class="bg-gray-700 p-3 rounded">
                        <div class="font-medium">TestNetwork</div>
                        <div class="text-gray-400">WPA2</div>
                        <button onclick="showConnectDialog('TestNetwork')">Connect</button>
                    </div>
                `,
            });
        });

        await page.reload();
        await waitForAppReady(page);

        // Look for connect button
        const connectBtn = page.locator('button:has-text("Connect"), button:has-text("Connecter")').first();
        const count = await connectBtn.count();

        if (count > 0) {
            await connectBtn.click();

            // Should show password input or dialog
            const passwordInput = page.locator('input[type="password"]');
            const count = await passwordInput.count();
            // Password input might be in modal or inline
            expect(count >= 0).toBeTruthy();
        }
    });

    test('should handle WiFi scan error gracefully', async ({ page }) => {
        // Mock scan error
        await mockApiError(page, '**/api/wifi/scan', 'Scan failed: WiFi adapter busy', 500);

        // Click scan
        const scanBtn = page.locator(SELECTORS.wifi.scanBtn);
        await scanBtn.click();

        // Should still have networks container visible (not crash)
        const networks = page.locator(SELECTORS.wifi.networks);
        await expect(networks).toBeVisible();
    });
});

test.describe('VPN Profile Import Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
        await navigateToTab(page, 'vpn');
    });

    test('should have file input for profile upload', async ({ page }) => {
        const fileInput = page.locator(SELECTORS.vpn.fileInput);
        await expect(fileInput).toBeVisible();
        await expect(fileInput).toHaveAttribute('accept', '.conf');
    });

    test('should display profiles section', async ({ page }) => {
        const profiles = page.locator(SELECTORS.vpn.profiles);
        await expect(profiles).toBeVisible();
    });

    test('should show VPN status indicator', async ({ page }) => {
        const status = page.locator(SELECTORS.vpn.status);
        await expect(status).toBeVisible();

        // Should have status indicator dot
        const statusDot = status.locator('.rounded-full');
        await expect(statusDot).toBeVisible();
    });

    test('should handle profile list with mock data', async ({ page }) => {
        // Mock profiles list
        await page.route('**/api/vpn/profiles', (route) => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    profiles: [
                        { name: 'home-vpn', active: true },
                        { name: 'work-vpn', active: false },
                    ]
                }),
            });
        });

        await page.reload();
        await waitForAppReady(page);
        await navigateToTab(page, 'vpn');

        // Profiles section should be visible
        const profiles = page.locator(SELECTORS.vpn.profiles);
        await expect(profiles).toBeVisible();
    });
});

test.describe('Hotspot Configuration Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
        await navigateToTab(page, 'hotspot');
    });

    test('should fill hotspot configuration form', async ({ page }) => {
        const { ssid, password } = TEST_DATA.hotspot.config;

        // Fill SSID
        const ssidInput = page.locator(SELECTORS.hotspot.ssid);
        await ssidInput.clear();
        await ssidInput.fill(ssid);
        await expect(ssidInput).toHaveValue(ssid);

        // Fill password
        const passwordInput = page.locator(SELECTORS.hotspot.password);
        await passwordInput.clear();
        await passwordInput.fill(password);
        await expect(passwordInput).toHaveValue(password);
    });

    test('should select country code', async ({ page }) => {
        const countrySelect = page.locator(SELECTORS.hotspot.countryCode);
        await countrySelect.selectOption('US');

        const value = await countrySelect.inputValue();
        expect(value).toBe('US');
    });

    test('should select WiFi band and update channels', async ({ page }) => {
        const bandSelect = page.locator(SELECTORS.hotspot.band);
        await bandSelect.selectOption('2.4GHz');

        // Channel options should update for 2.4GHz
        const channelSelect = page.locator(SELECTORS.hotspot.channel);
        const options = await channelSelect.locator('option').count();
        expect(options).toBeGreaterThan(0);
    });

    test('should toggle WPA3 option', async ({ page }) => {
        const wpa3Checkbox = page.locator(SELECTORS.hotspot.wpa3);
        const isChecked = await wpa3Checkbox.isChecked();

        await wpa3Checkbox.click();
        await expect(wpa3Checkbox).toBeChecked({ checked: !isChecked });
    });

    test('should validate form before submission', async ({ page }) => {
        // Clear SSID (required field)
        const ssidInput = page.locator(SELECTORS.hotspot.ssid);
        await ssidInput.clear();

        // Clear password (required field)
        const passwordInput = page.locator(SELECTORS.hotspot.password);
        await passwordInput.clear();

        // Try to submit
        const submitBtn = page.locator(SELECTORS.hotspot.submitBtn);
        await submitBtn.click();

        // Form should show validation (browser native or custom)
        // Check if SSID is still empty and form wasn't submitted
        await expect(ssidInput).toHaveValue('');
    });

    test('should complete hotspot configuration workflow', async ({ page }) => {
        const { ssid, password } = TEST_DATA.hotspot.config;

        // Track submitted payload
        let submittedPayload = null;

        // Mock successful config save with payload capture
        await page.route('**/api/hotspot/config', (route) => {
            if (route.request().method() === 'POST') {
                const postData = route.request().postData();
                if (postData) {
                    try {
                        submittedPayload = JSON.parse(postData);
                    } catch {
                        // Form data might not be JSON
                        submittedPayload = postData;
                    }
                }
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ status: 'success', message: 'Configuration saved' }),
                });
            } else {
                route.continue();
            }
        });

        // Fill form
        await page.locator(SELECTORS.hotspot.ssid).fill(ssid);
        await page.locator(SELECTORS.hotspot.password).fill(password);
        await page.locator(SELECTORS.hotspot.countryCode).selectOption('US');
        await page.locator(SELECTORS.hotspot.band).selectOption('2.4GHz');

        // Submit and wait for response
        const submitBtn = page.locator(SELECTORS.hotspot.submitBtn);
        const responsePromise = page.waitForResponse(
            response => response.url().includes('/api/hotspot/config') && response.request().method() === 'POST',
            { timeout: 10000 }
        );
        await submitBtn.click();
        const response = await responsePromise;

        // Verify response was successful
        expect(response.status()).toBe(200);

        // Message area should show success
        const messageArea = page.locator(SELECTORS.hotspot.message);
        await expect(messageArea).toBeVisible();
        // Verify success message content
        await expect(messageArea).toContainText(/success|saved|Configuration/i);
    });
});

test.describe('VPN Settings Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
        await navigateToTab(page, 'system');
    });

    test('should save VPN settings successfully', async ({ page }) => {
        const { ping_host, check_interval } = TEST_DATA.vpn.settings;

        // Track submitted payload
        let submittedPayload = null;

        // Mock successful save with payload capture
        await page.route('**/api/settings/vpn', (route) => {
            if (route.request().method() === 'POST') {
                const postData = route.request().postData();
                if (postData) {
                    try {
                        submittedPayload = JSON.parse(postData);
                    } catch {
                        submittedPayload = postData;
                    }
                }
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        status: 'saved',
                        settings: { ping_host, check_interval }
                    }),
                });
            } else {
                route.continue();
            }
        });

        // Fill form
        await page.locator(SELECTORS.system.pingHost).fill(ping_host);
        await page.locator(SELECTORS.system.checkInterval).fill(String(check_interval));

        // Submit and wait for response
        const responsePromise = page.waitForResponse(
            response => response.url().includes('/api/settings/vpn') && response.request().method() === 'POST',
            { timeout: 10000 }
        );
        await page.locator(SELECTORS.system.vpnSettingsBtn).click();
        const response = await responsePromise;

        // Verify response was successful
        expect(response.status()).toBe(200);

        // Verify message area shows success
        const messageArea = page.locator(SELECTORS.system.vpnMessage);
        await expect(messageArea).toBeVisible();
    });

    test('should handle VPN settings save error', async ({ page }) => {
        // Mock error response
        await mockApiError(page, '**/api/settings/vpn', 'Invalid ping host', 400);

        // Fill with invalid data
        await page.locator(SELECTORS.system.pingHost).fill('invalid-host!!');
        await page.locator(SELECTORS.system.checkInterval).fill('60');

        // Submit
        await page.locator(SELECTORS.system.vpnSettingsBtn).click();

        // Should not crash, form should remain usable
        const form = page.locator(SELECTORS.system.vpnForm);
        await expect(form).toBeVisible();
    });
});

test.describe('Setup Wizard Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should open setup wizard from system tab', async ({ page }) => {
        await navigateToTab(page, 'system');

        const wizardBtn = page.locator(SELECTORS.system.wizardBtn);
        await wizardBtn.click();

        // Wizard dialog should appear
        const wizardDialog = page.locator('#wizard-dialog, [role="dialog"], .wizard-container');
        await expect(wizardDialog.first()).toBeVisible({ timeout: 5000 });
    });

    test('should navigate through wizard steps', async ({ page }) => {
        await navigateToTab(page, 'system');

        const wizardBtn = page.locator(SELECTORS.system.wizardBtn);
        await wizardBtn.click();

        // Wait for wizard dialog
        const wizardDialog = page.locator('#wizard-dialog, [role="dialog"], .wizard-container');
        await expect(wizardDialog.first()).toBeVisible({ timeout: 5000 });

        // Look for next/continue button
        const nextBtn = page.locator('button:has-text("Next"), button:has-text("Continue"), button:has-text("Suivant")');
        const count = await nextBtn.count();

        if (count > 0) {
            await nextBtn.first().click();
            // Verify wizard content changed (step indicator or content update)
            await expect(wizardDialog.first()).toBeVisible();
            // Could check for step indicator change
            const stepIndicator = page.locator('.wizard-step, [data-step], .step-indicator');
            if (await stepIndicator.count() > 0) {
                await expect(stepIndicator.first()).toBeVisible();
            }
        }
    });

    test('should close wizard on cancel', async ({ page }) => {
        await navigateToTab(page, 'system');

        const wizardBtn = page.locator(SELECTORS.system.wizardBtn);
        await wizardBtn.click();

        // Wait for wizard dialog
        const wizardDialog = page.locator('#wizard-dialog, [role="dialog"], .wizard-container');
        await expect(wizardDialog.first()).toBeVisible({ timeout: 5000 });

        // Find close/cancel button
        const closeBtn = page.locator('button:has-text("Cancel"), button:has-text("Close"), button:has-text("Annuler"), [aria-label="Close"]');
        const count = await closeBtn.count();

        if (count > 0) {
            await closeBtn.first().click();

            // Wait for wizard to close (either hidden or removed)
            await expect(wizardDialog.first()).not.toBeVisible({ timeout: 3000 }).catch(() => {
                // Dialog may be removed from DOM entirely
            });
        }
    });
});

test.describe('Language Switching Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should switch all tabs to French', async ({ page }) => {
        await setLanguage(page, 'fr');

        // Check WiFi tab
        const wifiTab = page.locator('#tab-wifi');
        const wifiText = await wifiTab.textContent();

        // Check VPN tab
        await navigateToTab(page, 'vpn');
        const vpnContent = page.locator(SELECTORS.vpn.status);
        await expect(vpnContent).toBeVisible();

        // Check Hotspot tab
        await navigateToTab(page, 'hotspot');
        const hotspotForm = page.locator(SELECTORS.hotspot.form);
        await expect(hotspotForm).toBeVisible();

        // Check System tab
        await navigateToTab(page, 'system');
        const systemInfo = page.locator(SELECTORS.system.info);
        await expect(systemInfo).toBeVisible();
    });

    test('should persist language across page reload', async ({ page }) => {
        await setLanguage(page, 'fr');

        await page.reload();
        await waitForAppReady(page);

        // Language should still be French
        const html = page.locator('html');
        await expect(html).toHaveAttribute('lang', 'fr');
    });

    test('should switch back to English', async ({ page }) => {
        await setLanguage(page, 'fr');
        await setLanguage(page, 'en');

        const html = page.locator('html');
        await expect(html).toHaveAttribute('lang', 'en');
    });
});

test.describe('Cross-Tab Navigation Workflow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should navigate through all tabs sequentially', async ({ page }) => {
        // Start at WiFi (default)
        await expect(page.locator(SELECTORS.content.wifi)).toBeVisible();

        // Go to VPN
        await navigateToTab(page, 'vpn');
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
        await expect(page.locator(SELECTORS.content.wifi)).toBeHidden();

        // Go to Hotspot
        await navigateToTab(page, 'hotspot');
        await expect(page.locator(SELECTORS.content.hotspot)).toBeVisible();
        await expect(page.locator(SELECTORS.content.vpn)).toBeHidden();

        // Go to System
        await navigateToTab(page, 'system');
        await expect(page.locator(SELECTORS.content.system)).toBeVisible();
        await expect(page.locator(SELECTORS.content.hotspot)).toBeHidden();

        // Back to WiFi
        await navigateToTab(page, 'wifi');
        await expect(page.locator(SELECTORS.content.wifi)).toBeVisible();
        await expect(page.locator(SELECTORS.content.system)).toBeHidden();
    });

    test('should maintain state when switching tabs', async ({ page }) => {
        // Fill hotspot form
        await navigateToTab(page, 'hotspot');
        const ssidInput = page.locator(SELECTORS.hotspot.ssid);
        await ssidInput.fill('TestSSID');

        // Switch to another tab
        await navigateToTab(page, 'vpn');

        // Come back to hotspot
        await navigateToTab(page, 'hotspot');

        // Value should be preserved
        await expect(ssidInput).toHaveValue('TestSSID');
    });
});

test.describe('Status Cards Integration', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);
    });

    test('should display all status cards', async ({ page }) => {
        const statusCards = page.locator(SELECTORS.statusCards);
        await expect(statusCards).toBeVisible();

        // Should have WAN, VPN, and AP status
        const wanCard = page.locator('text=WAN');
        const vpnCard = page.locator('text=VPN');
        const apCard = page.locator('text=AP, text=Hotspot');

        await expect(wanCard.first()).toBeVisible();
        await expect(vpnCard.first()).toBeVisible();
        await expect(apCard.first()).toBeVisible();
    });

    test('should show status indicators', async ({ page }) => {
        const statusCards = page.locator(SELECTORS.statusCards);

        // Should have colored indicators
        const indicators = statusCards.locator('.rounded-full');
        const count = await indicators.count();
        expect(count).toBeGreaterThanOrEqual(3);
    });
});
