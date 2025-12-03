/**
 * E2E Tests: System Management Flow
 * Tests system information, VPN settings, and system actions
 */

const { test, expect } = require('@playwright/test');

test.describe('System Tab Display', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        // Navigate to System tab
        await page.click('#tab-system');
        await expect(page.locator('#content-system')).toBeVisible();
    });

    test('should display System tab content', async ({ page }) => {
        await expect(page.locator('#tab-system')).toHaveAttribute('aria-selected', 'true');
        await expect(page.locator('#content-system')).toBeVisible();
    });

    test('should show system information section', async ({ page }) => {
        const systemInfo = page.locator('#system-info');
        await expect(systemInfo).toBeVisible();
    });

    test('should have System Information title', async ({ page }) => {
        const title = page.locator('text=System Information, text=Informations système').first();
        await expect(title).toBeVisible();
    });

    test('should have VPN Watchdog section', async ({ page }) => {
        const vpnTitle = page.locator('text=VPN Watchdog, text=Chien de garde VPN').first();
        await expect(vpnTitle).toBeVisible();
    });

    test('should have System Actions section', async ({ page }) => {
        const actionsTitle = page.locator('text=System Actions, text=Actions système').first();
        await expect(actionsTitle).toBeVisible();
    });

    test('should have Quick Guide section', async ({ page }) => {
        const guideTitle = page.locator('text=Quick Guide, text=Guide rapide').first();
        await expect(guideTitle).toBeVisible();
    });
});

test.describe('System Information Display', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-system');
        // Wait for system info to load via HTMX
        await page.waitForSelector('#system-info:not(:has(.animate-pulse))', { timeout: 10000 });
    });

    test('should display device model', async ({ page }) => {
        const modelLabel = page.locator('text=Model, text=Modèle');
        await expect(modelLabel.first()).toBeVisible();
    });

    test('should display architecture', async ({ page }) => {
        const archLabel = page.locator('text=Architecture');
        await expect(archLabel.first()).toBeVisible();
    });

    test('should display RAM information', async ({ page }) => {
        const ramLabel = page.locator('text=RAM');
        await expect(ramLabel.first()).toBeVisible();

        // Should show format like "XXX/XXXMB"
        const systemInfo = page.locator('#system-info');
        const content = await systemInfo.textContent();
        expect(content).toMatch(/\d+.*MB/);
    });

    test('should display disk information', async ({ page }) => {
        const diskLabel = page.locator('text=Disk, text=Disque');
        await expect(diskLabel.first()).toBeVisible();

        // Should show format like "X/XXGB"
        const systemInfo = page.locator('#system-info');
        const content = await systemInfo.textContent();
        expect(content).toMatch(/\d+.*GB/);
    });

    test('should display CPU temperature', async ({ page }) => {
        const cpuLabel = page.locator('text=CPU');
        await expect(cpuLabel.first()).toBeVisible();

        // Should show temperature in Celsius
        const systemInfo = page.locator('#system-info');
        const content = await systemInfo.textContent();
        expect(content).toMatch(/\d+°C/);
    });

    test('should display WiFi capabilities', async ({ page }) => {
        const wifiCapsLabel = page.locator('text=WiFi capabilities, text=Capacités WiFi');
        await expect(wifiCapsLabel.first()).toBeVisible();
    });

    test('should display uptime', async ({ page }) => {
        const uptimeLabel = page.locator('text=Uptime, text=Temps');
        await expect(uptimeLabel.first()).toBeVisible();

        // Should show format like "Xh Xm"
        const systemInfo = page.locator('#system-info');
        const content = await systemInfo.textContent();
        expect(content).toMatch(/\d+h\s*\d+m/);
    });

    test('should show WiFi capability badges', async ({ page }) => {
        const systemInfo = page.locator('#system-info');

        // Should have 5GHz badge (either enabled or disabled state)
        const badge5ghz = systemInfo.locator('text=5GHz');
        await expect(badge5ghz.first()).toBeVisible();
    });
});

test.describe('VPN Settings Form', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-system');
    });

    test('should have VPN settings form', async ({ page }) => {
        const form = page.locator('#vpn-settings-form');
        await expect(form).toBeVisible();
    });

    test('should have ping host input field', async ({ page }) => {
        const pingHostInput = page.locator('#vpn-ping-host');
        await expect(pingHostInput).toBeVisible();
        await expect(pingHostInput).toHaveAttribute('name', 'ping_host');
    });

    test('should have check interval input field', async ({ page }) => {
        const intervalInput = page.locator('#vpn-check-interval');
        await expect(intervalInput).toBeVisible();
        await expect(intervalInput).toHaveAttribute('type', 'number');
        await expect(intervalInput).toHaveAttribute('min', '30');
        await expect(intervalInput).toHaveAttribute('max', '300');
    });

    test('should have default ping host value', async ({ page }) => {
        const pingHostInput = page.locator('#vpn-ping-host');
        const value = await pingHostInput.inputValue();
        expect(value).toBeTruthy();
    });

    test('should have default check interval value', async ({ page }) => {
        const intervalInput = page.locator('#vpn-check-interval');
        const value = await intervalInput.inputValue();
        expect(parseInt(value)).toBeGreaterThanOrEqual(30);
    });

    test('should have save settings button', async ({ page }) => {
        const saveBtn = page.locator('#vpn-settings-submit-btn');
        await expect(saveBtn).toBeVisible();
    });

    test('should allow typing in ping host field', async ({ page }) => {
        const pingHostInput = page.locator('#vpn-ping-host');
        await pingHostInput.clear();
        await pingHostInput.fill('1.1.1.1');
        await expect(pingHostInput).toHaveValue('1.1.1.1');
    });

    test('should allow changing check interval', async ({ page }) => {
        const intervalInput = page.locator('#vpn-check-interval');
        await intervalInput.clear();
        await intervalInput.fill('120');
        await expect(intervalInput).toHaveValue('120');
    });

    test('should have message area for form feedback', async ({ page }) => {
        const messageArea = page.locator('#vpn-settings-message');
        await expect(messageArea).toBeVisible();
        await expect(messageArea).toHaveAttribute('role', 'alert');
    });
});

test.describe('System Actions', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-system');
    });

    test('should have Reboot Pi button', async ({ page }) => {
        const rebootBtn = page.locator('button:has-text("Reboot"), button:has-text("Redémarrer")');
        await expect(rebootBtn.first()).toBeVisible();
    });

    test('should have Restart VPN button', async ({ page }) => {
        const restartVpnBtn = page.locator('button:has-text("Restart VPN"), button:has-text("Redémarrer VPN")');
        await expect(restartVpnBtn.first()).toBeVisible();
    });

    test('should have Restart Hotspot button', async ({ page }) => {
        const restartHotspotBtn = page.locator('button:has-text("Restart Hotspot"), button:has-text("Redémarrer Hotspot")');
        await expect(restartHotspotBtn.first()).toBeVisible();
    });

    test('should have Run Setup Wizard button', async ({ page }) => {
        const wizardBtn = page.locator('#run-wizard-btn');
        await expect(wizardBtn).toBeVisible();
    });

    test('reboot button should have confirmation attribute', async ({ page }) => {
        const rebootBtn = page.locator('button[hx-post="/api/system/reboot"]');
        await expect(rebootBtn).toHaveAttribute('hx-confirm');
    });

    test('restart VPN button should target message area', async ({ page }) => {
        const restartVpnBtn = page.locator('button[hx-post="/api/vpn/restart"]');
        await expect(restartVpnBtn).toHaveAttribute('hx-target', '#system-action-message');
    });

    test('restart Hotspot button should target message area', async ({ page }) => {
        const restartHotspotBtn = page.locator('button[hx-post="/api/hotspot/restart"]');
        await expect(restartHotspotBtn).toHaveAttribute('hx-target', '#system-action-message');
    });

    test('should have system action message area', async ({ page }) => {
        const messageArea = page.locator('#system-action-message');
        await expect(messageArea).toBeVisible();
        await expect(messageArea).toHaveAttribute('role', 'alert');
    });
});

test.describe('Quick Guide', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-system');
    });

    test('should display guide steps', async ({ page }) => {
        const guideList = page.locator('#content-system ul.list-disc');
        await expect(guideList).toBeVisible();

        // Should have multiple guide items
        const items = guideList.locator('li');
        const count = await items.count();
        expect(count).toBeGreaterThanOrEqual(5);
    });

    test('should display version information', async ({ page }) => {
        const versionText = page.locator('text=Version');
        await expect(versionText.first()).toBeVisible();

        // Should show ROSE Link version
        const content = await page.locator('#content-system').textContent();
        expect(content).toMatch(/ROSE Link v\d+\.\d+\.\d+/);
    });

    test('should display compatibility information', async ({ page }) => {
        const compatText = page.locator('text=Pi 3, text=Pi 4, text=Pi 5');
        await expect(compatText.first()).toBeVisible();
    });
});

test.describe('System Tab Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-system');
    });

    test('should have proper labels for form inputs', async ({ page }) => {
        const pingHostLabel = page.locator('label[for="vpn-ping-host"]');
        const intervalLabel = page.locator('label[for="vpn-check-interval"]');

        await expect(pingHostLabel).toBeVisible();
        await expect(intervalLabel).toBeVisible();
    });

    test('should support keyboard navigation in form', async ({ page }) => {
        const pingHostInput = page.locator('#vpn-ping-host');
        await pingHostInput.focus();
        await expect(pingHostInput).toBeFocused();

        // Tab to next field
        await page.keyboard.press('Tab');
        const intervalInput = page.locator('#vpn-check-interval');
        await expect(intervalInput).toBeFocused();

        // Tab to submit button
        await page.keyboard.press('Tab');
        const submitBtn = page.locator('#vpn-settings-submit-btn');
        await expect(submitBtn).toBeFocused();
    });

    test('should have accessible buttons', async ({ page }) => {
        const buttons = page.locator('#content-system button');
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

    test('should have aria-live regions for messages', async ({ page }) => {
        const vpnMessage = page.locator('#vpn-settings-message');
        const actionMessage = page.locator('#system-action-message');

        await expect(vpnMessage).toHaveAttribute('role', 'alert');
        await expect(actionMessage).toHaveAttribute('role', 'alert');
    });

    test('should have proper heading hierarchy', async ({ page }) => {
        // System tab should have h2 headings for each section
        const h2Headings = page.locator('#content-system h2');
        const count = await h2Headings.count();
        expect(count).toBeGreaterThanOrEqual(3); // System Info, VPN Settings, Actions, Guide
    });
});

test.describe('System Status Integration', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should display system info in status cards', async ({ page }) => {
        const statusCards = page.locator('#status-cards');
        await expect(statusCards).toBeVisible();
    });

    test('should refresh system info periodically', async ({ page }) => {
        await page.click('#tab-system');

        // System info has hx-trigger="load, every 30s"
        const systemInfo = page.locator('#system-info[hx-trigger]');
        const trigger = await systemInfo.getAttribute('hx-trigger');
        expect(trigger).toContain('every');
    });
});

test.describe('Setup Wizard Integration', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
        await page.click('#tab-system');
    });

    test('should open wizard when Run Setup Wizard is clicked', async ({ page }) => {
        const wizardBtn = page.locator('#run-wizard-btn');
        await wizardBtn.click();

        // Wizard dialog should appear
        const wizardDialog = page.locator('#wizard-dialog, [role="dialog"]');
        await expect(wizardDialog.first()).toBeVisible({ timeout: 5000 });
    });

    test('wizard should have close/cancel option', async ({ page }) => {
        const wizardBtn = page.locator('#run-wizard-btn');
        await wizardBtn.click();

        // Wait for wizard to appear
        await page.waitForSelector('#wizard-dialog, [role="dialog"]', { timeout: 5000 });

        // Should have close button or cancel option
        const closeBtn = page.locator('[aria-label="Close"], button:has-text("Cancel"), button:has-text("Annuler"), button:has-text("Close")');
        const count = await closeBtn.count();
        expect(count).toBeGreaterThanOrEqual(1);
    });
});
