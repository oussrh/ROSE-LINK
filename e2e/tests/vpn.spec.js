/**
 * E2E Tests: VPN Management Flow
 * Tests VPN profile management, activation, and status display
 */

const { test, expect } = require('@playwright/test');

test.describe('VPN Management', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        // Navigate to VPN tab
        await page.click('#tab-vpn');
        await expect(page.locator('#content-vpn')).toBeVisible();
    });

    test('should display VPN tab content', async ({ page }) => {
        // Check for VPN status section
        await expect(page.locator('#vpn-status-detail')).toBeVisible();
    });

    test('should display VPN profiles section', async ({ page }) => {
        // Check for profiles section
        await expect(page.locator('#vpn-profiles')).toBeVisible();
    });

    test('should show VPN status indicator', async ({ page }) => {
        // Either connected (green) or disconnected (red) indicator should be visible
        const statusIndicator = page.locator('#vpn-status-detail .rounded-full');
        await expect(statusIndicator).toBeVisible();
    });

    test('should have upload profile form', async ({ page }) => {
        // Check for file input for VPN profile upload
        const fileInput = page.locator('input[type="file"][accept=".conf"]');
        await expect(fileInput).toBeVisible();
    });

    test('should display profile list or empty message', async ({ page }) => {
        const profilesContainer = page.locator('#vpn-profiles');
        await expect(profilesContainer).toBeVisible();

        // Should have either profiles or "no profiles" message
        const hasProfiles = await page.locator('#vpn-profiles .bg-gray-700').count() > 0;
        const hasEmptyMessage = await page.locator('#vpn-profiles').textContent();

        expect(hasProfiles || hasEmptyMessage.length > 0).toBeTruthy();
    });

    test('should show activate button for inactive profiles', async ({ page }) => {
        // If there are inactive profiles, they should have activate buttons
        const inactiveProfiles = page.locator('#vpn-profiles .bg-gray-700:has(.bg-gray-500)');
        const count = await inactiveProfiles.count();

        if (count > 0) {
            const activateBtn = inactiveProfiles.first().locator('button:has-text("Activate"), button:has-text("Activer")');
            await expect(activateBtn).toBeVisible();
        }
    });

    test('should show active indicator for active profile', async ({ page }) => {
        // If there's an active profile, it should have a green indicator
        const activeProfile = page.locator('#vpn-profiles .bg-gray-700:has(.bg-green-500.pulse-slow)');
        const count = await activeProfile.count();

        if (count > 0) {
            const activeLabel = activeProfile.first().locator('text=Active, text=Actif');
            await expect(activeLabel).toBeVisible();
        }
    });

    test('should have VPN settings section', async ({ page }) => {
        // Check for VPN watchdog settings
        const pingHostInput = page.locator('#vpn-ping-host');
        const checkIntervalInput = page.locator('#vpn-check-interval');

        // Settings may be in a collapsible section
        const settingsSection = page.locator('text=VPN Settings, text=Paramètres VPN').first();
        if (await settingsSection.isVisible()) {
            await expect(pingHostInput).toBeVisible();
            await expect(checkIntervalInput).toBeVisible();
        }
    });

    test('should display transfer statistics when VPN is active', async ({ page }) => {
        const transferStats = page.locator('#vpn-status-detail:has-text("Transfer"), #vpn-status-detail:has-text("Transfert")');

        // If VPN is active, transfer stats should be visible
        const vpnActive = await page.locator('#vpn-status-detail .bg-green-500').count() > 0;
        if (vpnActive) {
            await expect(transferStats).toBeVisible();
        }
    });
});

test.describe('VPN Profile Upload', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-vpn');
    });

    test('should have file input accepting .conf files', async ({ page }) => {
        const fileInput = page.locator('input[type="file"]');
        await expect(fileInput).toHaveAttribute('accept', '.conf');
    });

    test('should have upload/import button', async ({ page }) => {
        // Look for import or upload button
        const uploadBtn = page.locator('button:has-text("Import"), button:has-text("Importer"), button:has-text("Upload")');
        await expect(uploadBtn).toBeVisible();
    });
});

test.describe('VPN Tab Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-vpn');
    });

    test('should have proper ARIA labels on VPN controls', async ({ page }) => {
        // File input should be accessible
        const fileInput = page.locator('input[type="file"]');
        const hasLabel = await fileInput.evaluate(el => {
            const label = document.querySelector(`label[for="${el.id}"]`);
            return label !== null || el.getAttribute('aria-label') !== null;
        });
        expect(hasLabel).toBeTruthy();
    });

    test('should have accessible buttons', async ({ page }) => {
        const buttons = page.locator('#content-vpn button');
        const count = await buttons.count();

        for (let i = 0; i < count; i++) {
            const button = buttons.nth(i);
            const text = await button.textContent();
            const ariaLabel = await button.getAttribute('aria-label');
            const title = await button.getAttribute('title');

            // Button should have some accessible name
            expect(text.trim().length > 0 || ariaLabel || title).toBeTruthy();
        }
    });
});
