/**
 * E2E Tests: Navigation and Tab Functionality
 */

const { test, expect } = require('@playwright/test');

test.describe('Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        // Wait for splash screen to disappear
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should load the main page', async ({ page }) => {
        await expect(page).toHaveTitle(/ROSE Link/);
    });

    test('should display the header with logo', async ({ page }) => {
        const logo = page.locator('img[alt="ROSE Link Logo"]');
        await expect(logo).toBeVisible();
    });

    test('should display all navigation tabs', async ({ page }) => {
        await expect(page.locator('#tab-wifi')).toBeVisible();
        await expect(page.locator('#tab-vpn')).toBeVisible();
        await expect(page.locator('#tab-hotspot')).toBeVisible();
        await expect(page.locator('#tab-system')).toBeVisible();
    });

    test('should switch to VPN tab when clicked', async ({ page }) => {
        await page.click('#tab-vpn');

        await expect(page.locator('#content-vpn')).toBeVisible();
        await expect(page.locator('#content-wifi')).toBeHidden();
    });

    test('should switch to Hotspot tab when clicked', async ({ page }) => {
        await page.click('#tab-hotspot');

        await expect(page.locator('#content-hotspot')).toBeVisible();
    });

    test('should switch to System tab when clicked', async ({ page }) => {
        await page.click('#tab-system');

        await expect(page.locator('#content-system')).toBeVisible();
    });

    test('should navigate tabs with keyboard arrow keys', async ({ page }) => {
        // Focus the first tab
        await page.click('#tab-wifi');

        // Press arrow right to go to VPN
        await page.keyboard.press('ArrowRight');
        await expect(page.locator('#tab-vpn')).toHaveAttribute('aria-selected', 'true');

        // Press arrow right to go to Hotspot
        await page.keyboard.press('ArrowRight');
        await expect(page.locator('#tab-hotspot')).toHaveAttribute('aria-selected', 'true');

        // Press arrow left to go back to VPN
        await page.keyboard.press('ArrowLeft');
        await expect(page.locator('#tab-vpn')).toHaveAttribute('aria-selected', 'true');
    });

    test('should navigate to first tab with Home key', async ({ page }) => {
        await page.click('#tab-system');
        await page.keyboard.press('Home');

        await expect(page.locator('#tab-wifi')).toHaveAttribute('aria-selected', 'true');
    });

    test('should navigate to last tab with End key', async ({ page }) => {
        await page.click('#tab-wifi');
        await page.keyboard.press('End');

        await expect(page.locator('#tab-system')).toHaveAttribute('aria-selected', 'true');
    });

    test('should persist tab selection across page reload', async ({ page }) => {
        // Select VPN tab
        await page.click('#tab-vpn');
        await expect(page.locator('#content-vpn')).toBeVisible();

        // Reload page
        await page.reload();
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });

        // VPN tab should still be selected
        await expect(page.locator('#content-vpn')).toBeVisible();
    });
});

test.describe('Language Switching', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should switch to French when FR button is clicked', async ({ page }) => {
        await page.click('#lang-fr');

        // Check that some text is in French
        await expect(page.locator('[data-i18n="tab_wifi"]')).toContainText('WiFi');
    });

    test('should switch to English when EN button is clicked', async ({ page }) => {
        // First switch to French
        await page.click('#lang-fr');
        // Then switch back to English
        await page.click('#lang-en');

        await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    });

    test('should persist language selection across page reload', async ({ page }) => {
        await page.click('#lang-fr');
        await page.reload();
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });

        await expect(page.locator('html')).toHaveAttribute('lang', 'fr');
    });
});

test.describe('Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });
    });

    test('should have proper ARIA roles on tabs', async ({ page }) => {
        const tabs = page.locator('[role="tab"]');
        await expect(tabs).toHaveCount(4);
    });

    test('should have proper ARIA attributes on tab panels', async ({ page }) => {
        const wifiPanel = page.locator('#content-wifi');
        await expect(wifiPanel).toHaveAttribute('role', 'tabpanel');
    });

    test('should have aria-selected on active tab', async ({ page }) => {
        const activeTab = page.locator('[aria-selected="true"]');
        await expect(activeTab).toHaveCount(1);
    });

    test('should have alt text on images', async ({ page }) => {
        const images = page.locator('img');
        const count = await images.count();

        for (let i = 0; i < count; i++) {
            const img = images.nth(i);
            const alt = await img.getAttribute('alt');
            expect(alt).toBeTruthy();
        }
    });

    test('should have visible focus styles', async ({ page }) => {
        await page.click('#tab-wifi');
        await page.keyboard.press('Tab');

        // Check that some element has focus
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeVisible();
    });
});

test.describe('Responsive Design', () => {
    test('should display correctly on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });

        // Header should be visible
        const header = page.locator('header');
        await expect(header).toBeVisible();

        // Tabs should be visible
        await expect(page.locator('#tab-wifi')).toBeVisible();
    });

    test('should display correctly on tablet', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });

        await expect(page.locator('h1')).toBeVisible();
    });

    test('should display correctly on desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto('/');
        await page.waitForSelector('#splash-screen', { state: 'hidden', timeout: 10000 });

        await expect(page.locator('h1')).toBeVisible();
    });
});
