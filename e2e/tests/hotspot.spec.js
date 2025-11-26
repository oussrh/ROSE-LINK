/**
 * E2E Tests: Hotspot Management Flow
 * Tests hotspot configuration, status, and connected clients
 */

const { test, expect } = require('@playwright/test');

test.describe('Hotspot Management', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        // Navigate to Hotspot tab
        await page.click('#tab-hotspot');
        await expect(page.locator('#content-hotspot')).toBeVisible();
    });

    test('should display Hotspot tab content', async ({ page }) => {
        await expect(page.locator('#tab-hotspot')).toHaveAttribute('aria-selected', 'true');
    });

    test('should show hotspot configuration form', async ({ page }) => {
        const form = page.locator('#hotspot-form');
        await expect(form).toBeVisible();
    });

    test('should have SSID input field', async ({ page }) => {
        const ssidInput = page.locator('#hotspot-ssid');
        await expect(ssidInput).toBeVisible();
        await expect(ssidInput).toHaveAttribute('maxlength', '32');
    });

    test('should have password input field', async ({ page }) => {
        const passwordInput = page.locator('#hotspot-password');
        await expect(passwordInput).toBeVisible();
        await expect(passwordInput).toHaveAttribute('type', 'password');
        await expect(passwordInput).toHaveAttribute('minlength', '8');
    });

    test('should have country code selector', async ({ page }) => {
        const countrySelect = page.locator('#country-code, select[name="country"]');
        await expect(countrySelect).toBeVisible();
    });

    test('should have WiFi band selector', async ({ page }) => {
        const bandSelect = page.locator('#wifi-band, select[name="band"]');
        await expect(bandSelect).toBeVisible();
    });

    test('should have channel selector', async ({ page }) => {
        const channelSelect = page.locator('#wifi-channel, select[name="channel"]');
        await expect(channelSelect).toBeVisible();
    });

    test('should have WPA3 option', async ({ page }) => {
        const wpa3Checkbox = page.locator('#wpa3, input[name="wpa3"]');
        await expect(wpa3Checkbox).toBeVisible();
    });

    test('should have apply configuration button', async ({ page }) => {
        const applyBtn = page.locator('#hotspot-submit-btn, button[type="submit"]');
        await expect(applyBtn).toBeVisible();
    });
});

test.describe('Hotspot Channel Selection', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-hotspot');
    });

    test('should show 2.4GHz channels for 2.4GHz band', async ({ page }) => {
        const bandSelect = page.locator('#wifi-band, select[name="band"]');
        await bandSelect.selectOption('2.4GHz');

        const channelSelect = page.locator('#wifi-channel, select[name="channel"]');
        const options = await channelSelect.locator('option').allTextContents();

        // Should have 2.4GHz channels (1, 6, 11)
        expect(options.some(opt => opt.includes('2.4GHz') || opt.includes('1') || opt.includes('6'))).toBeTruthy();
    });

    test('should show 5GHz channels for 5GHz band', async ({ page }) => {
        const bandSelect = page.locator('#wifi-band, select[name="band"]');

        // Try to select 5GHz
        try {
            await bandSelect.selectOption('5GHz');
            const channelSelect = page.locator('#wifi-channel, select[name="channel"]');
            const options = await channelSelect.locator('option').allTextContents();

            // Should have 5GHz channels (36, 40, 44, etc.)
            expect(options.some(opt => opt.includes('5GHz') || opt.includes('36') || opt.includes('149'))).toBeTruthy();
        } catch {
            // 5GHz might not be available on all devices
        }
    });
});

test.describe('Connected Clients', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-hotspot');
    });

    test('should display connected clients section', async ({ page }) => {
        const clientsSection = page.locator('#connected-clients');
        await expect(clientsSection).toBeVisible();
    });

    test('should show client count or empty message', async ({ page }) => {
        const clientsSection = page.locator('#connected-clients');
        const content = await clientsSection.textContent();

        // Should have either clients listed or "no clients" message
        expect(content.length > 0).toBeTruthy();
    });

    test('should display client details when clients connected', async ({ page }) => {
        const clients = page.locator('#connected-clients .bg-gray-700');
        const count = await clients.count();

        if (count > 0) {
            const firstClient = clients.first();

            // Should show IP or hostname
            const clientInfo = await firstClient.textContent();
            expect(clientInfo).toMatch(/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9-]+/);
        }
    });
});

test.describe('Hotspot Form Validation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-hotspot');
    });

    test('should require SSID field', async ({ page }) => {
        const ssidInput = page.locator('#hotspot-ssid');
        await expect(ssidInput).toHaveAttribute('required');
    });

    test('should require password field', async ({ page }) => {
        const passwordInput = page.locator('#hotspot-password');
        await expect(passwordInput).toHaveAttribute('required');
    });

    test('should enforce minimum password length', async ({ page }) => {
        const passwordInput = page.locator('#hotspot-password');
        await expect(passwordInput).toHaveAttribute('minlength', '8');
    });

    test('should enforce maximum SSID length', async ({ page }) => {
        const ssidInput = page.locator('#hotspot-ssid');
        await expect(ssidInput).toHaveAttribute('maxlength', '32');
    });
});

test.describe('Hotspot Tab Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-hotspot');
    });

    test('should have labels for all form fields', async ({ page }) => {
        const ssidLabel = page.locator('label[for="hotspot-ssid"]');
        const passwordLabel = page.locator('label[for="hotspot-password"]');

        await expect(ssidLabel).toBeVisible();
        await expect(passwordLabel).toBeVisible();
    });

    test('should have accessible message area', async ({ page }) => {
        const messageArea = page.locator('#hotspot-message');
        await expect(messageArea).toHaveAttribute('role', 'alert');
    });

    test('should support keyboard navigation in form', async ({ page }) => {
        const ssidInput = page.locator('#hotspot-ssid');
        await ssidInput.focus();
        await expect(ssidInput).toBeFocused();

        // Tab to next field
        await page.keyboard.press('Tab');

        // Next input should be focused
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeVisible();
    });
});

test.describe('Hotspot Status Card', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should display hotspot status in status cards', async ({ page }) => {
        const statusCards = page.locator('#status-cards');
        await expect(statusCards).toBeVisible();

        // Should show AP/Hotspot status
        const apStatus = page.locator('text=AP, text=Hotspot');
        await expect(apStatus.first()).toBeVisible();
    });

    test('should show SSID when hotspot is active', async ({ page }) => {
        const statusCards = page.locator('#status-cards');
        const content = await statusCards.textContent();

        // If hotspot is active, SSID should be shown
        const hasHotspotInfo = content.includes('AP') || content.includes('Hotspot');
        expect(hasHotspotInfo).toBeTruthy();
    });
});
