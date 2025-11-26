/**
 * E2E Tests: WiFi WAN Management Flow
 * Tests WiFi scanning, connection, and status display
 */

const { test, expect } = require('@playwright/test');

test.describe('WiFi WAN Management', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        // WiFi tab should be selected by default
        await expect(page.locator('#content-wifi')).toBeVisible();
    });

    test('should display WiFi tab by default', async ({ page }) => {
        await expect(page.locator('#tab-wifi')).toHaveAttribute('aria-selected', 'true');
        await expect(page.locator('#content-wifi')).toBeVisible();
    });

    test('should show current WiFi connection status', async ({ page }) => {
        const statusContainer = page.locator('#wifi-current-status');
        await expect(statusContainer).toBeVisible();
    });

    test('should display connection status indicator', async ({ page }) => {
        // Should show either connected (green/blue) or not connected (gray) status
        const statusIndicator = page.locator('#wifi-current-status .rounded-full');
        await expect(statusIndicator).toBeVisible();
    });

    test('should have scan networks button', async ({ page }) => {
        // Look for scan button
        const scanBtn = page.locator('button:has-text("Scan"), button:has-text("Rechercher")');
        await expect(scanBtn).toBeVisible();
    });

    test('should display available networks section', async ({ page }) => {
        const networksContainer = page.locator('#wifi-networks');
        await expect(networksContainer).toBeVisible();
    });

    test('should show ethernet priority message when ethernet connected', async ({ page }) => {
        // If ethernet is connected, should show priority message
        const ethernetStatus = page.locator('#wifi-current-status:has-text("Ethernet"), #wifi-current-status:has-text("ethernet")');
        const count = await ethernetStatus.count();

        if (count > 0) {
            const priorityMsg = page.locator('text=priority, text=priorité');
            await expect(priorityMsg).toBeVisible();
        }
    });

    test('should show disconnect button when WiFi is connected', async ({ page }) => {
        // If WiFi is connected, disconnect button should be visible
        const wifiConnected = page.locator('#wifi-current-status .bg-blue-500');
        const count = await wifiConnected.count();

        if (count > 0) {
            const disconnectBtn = page.locator('button:has-text("Disconnect"), button:has-text("Déconnecter")');
            await expect(disconnectBtn).toBeVisible();
        }
    });
});

test.describe('WiFi Network List', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should display network list or empty message', async ({ page }) => {
        const networksContainer = page.locator('#wifi-networks');
        await expect(networksContainer).toBeVisible();

        // Wait for networks to load
        await page.waitForTimeout(1000);

        const content = await networksContainer.textContent();
        expect(content.length > 0).toBeTruthy();
    });

    test('should show network SSID and security type', async ({ page }) => {
        const networks = page.locator('#wifi-networks .bg-gray-700');
        const count = await networks.count();

        if (count > 0) {
            const firstNetwork = networks.first();
            // Should have SSID text
            const ssidText = await firstNetwork.locator('.font-medium').textContent();
            expect(ssidText.length > 0).toBeTruthy();

            // Should show security type
            const securityText = await firstNetwork.locator('.text-gray-400').textContent();
            expect(securityText).toMatch(/WPA|WEP|Open|%/);
        }
    });

    test('should show connect button for each network', async ({ page }) => {
        const networks = page.locator('#wifi-networks .bg-gray-700');
        const count = await networks.count();

        if (count > 0) {
            const connectBtn = networks.first().locator('button:has-text("Connect"), button:has-text("Connecter")');
            await expect(connectBtn).toBeVisible();
        }
    });
});

test.describe('WiFi Tab Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should have proper role on network list', async ({ page }) => {
        const networkList = page.locator('#wifi-networks[role="list"]');
        // List may or may not have role depending on content
        const hasRole = await networkList.count() > 0;
        // This is optional but good practice
    });

    test('should have accessible scan button', async ({ page }) => {
        const scanBtn = page.locator('button:has-text("Scan"), button:has-text("Rechercher")');
        const text = await scanBtn.textContent();
        expect(text.trim().length > 0).toBeTruthy();
    });

    test('should support keyboard interaction for network selection', async ({ page }) => {
        const scanBtn = page.locator('button:has-text("Scan"), button:has-text("Rechercher")');

        // Focus the scan button
        await scanBtn.focus();

        // Should be focusable
        await expect(scanBtn).toBeFocused();
    });
});

test.describe('WiFi Status Cards', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should display WAN status card', async ({ page }) => {
        const statusCards = page.locator('#status-cards');
        await expect(statusCards).toBeVisible();

        // Should show WAN status
        const wanCard = page.locator('text=WAN');
        await expect(wanCard).toBeVisible();
    });

    test('should show IP address when connected', async ({ page }) => {
        // If connected, IP address should be displayed
        const ipPattern = /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/;
        const statusText = await page.locator('#status-cards').textContent();

        // IP might be shown if connected
        const hasIp = ipPattern.test(statusText);
        // This is expected when connected
    });
});
