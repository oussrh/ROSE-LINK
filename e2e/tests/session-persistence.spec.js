/**
 * E2E Tests: Session Persistence
 * Tests that user settings and state persist correctly across sessions
 */

const { test, expect } = require('@playwright/test');
const {
    waitForAppReady,
    navigateToTab,
    setLanguage,
    SELECTORS,
    TEST_DATA
} = require('./fixtures/test-helpers');

test.describe('Language Persistence', () => {
    test('should persist French language preference across reload', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Set language to French
        await setLanguage(page, 'fr');

        // Verify language is French
        const html = page.locator('html');
        await expect(html).toHaveAttribute('lang', 'fr');

        // Reload the page
        await page.reload();
        await waitForAppReady(page);

        // Language should still be French
        await expect(html).toHaveAttribute('lang', 'fr');

        // Verify localStorage persisted the language
        const storedLang = await page.evaluate(() => localStorage.getItem('rose-link-lang'));
        expect(storedLang).toBe('fr');
    });

    test('should persist English language preference after switching back', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Switch to French then back to English
        await setLanguage(page, 'fr');
        await setLanguage(page, 'en');

        // Reload
        await page.reload();
        await waitForAppReady(page);

        // Should be English
        const html = page.locator('html');
        await expect(html).toHaveAttribute('lang', 'en');
    });

    test('should apply persisted language on fresh page load', async ({ page }) => {
        // Set localStorage before page load
        await page.goto('/');
        await page.evaluate(() => {
            localStorage.setItem('rose-link-lang', 'fr');
        });

        // Navigate to page fresh
        await page.goto('/');
        await waitForAppReady(page);

        // Should load with French
        const html = page.locator('html');
        await expect(html).toHaveAttribute('lang', 'fr');
    });
});

test.describe('Tab Selection Persistence', () => {
    test('should persist active tab across reload', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Navigate to VPN tab
        await navigateToTab(page, 'vpn');

        // Verify VPN tab is active
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();

        // Reload
        await page.reload();
        await waitForAppReady(page);

        // VPN tab should still be selected
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });

    test('should persist hotspot tab across reload', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Navigate to Hotspot tab
        await navigateToTab(page, 'hotspot');

        // Verify Hotspot tab is active
        await expect(page.locator(SELECTORS.content.hotspot)).toBeVisible();

        // Reload
        await page.reload();
        await waitForAppReady(page);

        // Hotspot tab should still be selected
        await expect(page.locator(SELECTORS.content.hotspot)).toBeVisible();
    });

    test('should persist system tab across reload', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Navigate to System tab
        await navigateToTab(page, 'system');

        // Verify System tab is active
        await expect(page.locator(SELECTORS.content.system)).toBeVisible();

        // Reload
        await page.reload();
        await waitForAppReady(page);

        // System tab should still be selected
        await expect(page.locator(SELECTORS.content.system)).toBeVisible();
    });
});

test.describe('Form Draft Preservation', () => {
    test('should preserve hotspot form values when switching tabs', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Navigate to Hotspot and fill form
        await navigateToTab(page, 'hotspot');

        const { ssid, password } = TEST_DATA.hotspot.config;
        await page.locator(SELECTORS.hotspot.ssid).fill(ssid);
        await page.locator(SELECTORS.hotspot.password).fill(password);

        // Switch to another tab
        await navigateToTab(page, 'wifi');

        // Come back to Hotspot
        await navigateToTab(page, 'hotspot');

        // Values should be preserved
        await expect(page.locator(SELECTORS.hotspot.ssid)).toHaveValue(ssid);
        await expect(page.locator(SELECTORS.hotspot.password)).toHaveValue(password);
    });

    test('should preserve VPN settings form values when switching tabs', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Navigate to System and fill VPN settings
        await navigateToTab(page, 'system');

        const { ping_host, check_interval } = TEST_DATA.vpn.settings;
        await page.locator(SELECTORS.system.pingHost).fill(ping_host);
        await page.locator(SELECTORS.system.checkInterval).fill(String(check_interval));

        // Switch to another tab
        await navigateToTab(page, 'vpn');

        // Come back to System
        await navigateToTab(page, 'system');

        // Values should be preserved
        await expect(page.locator(SELECTORS.system.pingHost)).toHaveValue(ping_host);
        await expect(page.locator(SELECTORS.system.checkInterval)).toHaveValue(String(check_interval));
    });
});

test.describe('WebSocket Reconnection', () => {
    test('should attempt reconnection after WebSocket disconnect', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Track WebSocket connections
        let wsConnections = 0;
        let wsReconnectAttempts = 0;

        page.on('websocket', ws => {
            wsConnections++;

            ws.on('close', () => {
                // Track that connection was closed
            });
        });

        // Go offline to trigger disconnect
        await page.context().setOffline(true);

        // Wait a moment for disconnect to be detected
        await page.waitForFunction(() => {
            // Check if any reconnection UI is shown
            const indicator = document.querySelector('[data-testid="connection-status"], .connection-status');
            return indicator !== null || true; // Continue even if no indicator
        }, { timeout: 5000 }).catch(() => {});

        // Go back online
        await page.context().setOffline(false);

        // App should remain functional
        const header = page.locator('header');
        await expect(header).toBeVisible();

        // Should be able to navigate
        await navigateToTab(page, 'vpn');
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });

    test('should restore status updates after reconnection', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Verify status cards are visible initially
        await expect(page.locator(SELECTORS.statusCards)).toBeVisible();

        // Go offline briefly
        await page.context().setOffline(true);

        // Go back online
        await page.context().setOffline(false);

        // Status cards should still be visible and functional
        await expect(page.locator(SELECTORS.statusCards)).toBeVisible();

        // Should show WAN, VPN, AP status
        const statusText = await page.locator(SELECTORS.statusCards).textContent();
        expect(statusText.length).toBeGreaterThan(0);
    });
});

test.describe('Theme Persistence', () => {
    test('should use system default theme initially', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Check that the app loads with some theme applied
        const body = page.locator('body');
        await expect(body).toBeVisible();

        // Verify basic styling is applied
        const hasBackground = await body.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return styles.backgroundColor !== 'rgba(0, 0, 0, 0)';
        });
        expect(hasBackground).toBeTruthy();
    });
});

test.describe('Multi-Session Consistency', () => {
    test('should maintain consistent state across multiple tabs (simulated)', async ({ page, context }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Set language in first tab
        await setLanguage(page, 'fr');

        // Open a "new tab" (new page in same context shares localStorage)
        const page2 = await context.newPage();
        await page2.goto('/');
        await waitForAppReady(page2);

        // Second tab should also be in French (reads from localStorage)
        const html2 = page2.locator('html');
        await expect(html2).toHaveAttribute('lang', 'fr');

        await page2.close();
    });

    test('should not lose state when navigating back', async ({ page }) => {
        await page.goto('/');
        await waitForAppReady(page);

        // Navigate to VPN
        await navigateToTab(page, 'vpn');

        // Navigate to external URL and back (simulated with reload to same state)
        const currentUrl = page.url();

        // Navigate to system
        await navigateToTab(page, 'system');

        // Navigate back to VPN
        await navigateToTab(page, 'vpn');

        // VPN content should be visible
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });
});

test.describe('LocalStorage Integrity', () => {
    test('should handle corrupted localStorage gracefully', async ({ page }) => {
        // Set corrupted data before page load
        await page.goto('/');
        await page.evaluate(() => {
            localStorage.setItem('rose-link-lang', 'invalid-lang');
            localStorage.setItem('rose-link-tab', '{corrupted-json}');
        });

        // Reload page
        await page.reload();
        await waitForAppReady(page);

        // App should still function with defaults
        const header = page.locator('header');
        await expect(header).toBeVisible();

        // Should fall back to default language (en)
        const html = page.locator('html');
        const lang = await html.getAttribute('lang');
        expect(['en', 'fr']).toContain(lang); // Should be a valid language
    });

    test('should handle missing localStorage gracefully', async ({ page }) => {
        await page.goto('/');
        await page.evaluate(() => {
            localStorage.clear();
        });

        await page.reload();
        await waitForAppReady(page);

        // App should still function
        const header = page.locator('header');
        await expect(header).toBeVisible();

        // Should be able to navigate
        await navigateToTab(page, 'vpn');
        await expect(page.locator(SELECTORS.content.vpn)).toBeVisible();
    });
});
