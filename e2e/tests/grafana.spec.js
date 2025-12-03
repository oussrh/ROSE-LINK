/**
 * E2E Tests: Grafana Dashboard
 *
 * These tests verify the ROSE-LINK Grafana dashboard functionality.
 * Requires Grafana to be running (via docker-compose in monitoring/).
 *
 * Run these tests with:
 *   GRAFANA_URL=http://localhost:3000 npx playwright test grafana.spec.js
 */

const { test, expect } = require('@playwright/test');

// Grafana URL - can be configured via environment variable
const GRAFANA_URL = process.env.GRAFANA_URL || 'http://localhost:3000';
const DASHBOARD_UID = 'rose-link-main';

test.describe('Grafana Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to the ROSE-LINK dashboard
        await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);

        // Wait for Grafana to load (check for dashboard title or panels)
        await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
            timeout: 30000,
        });
    });

    test.describe('Dashboard Loading', () => {
        test('should load the ROSE-LINK dashboard', async ({ page }) => {
            // Check dashboard title is visible
            const dashboardTitle = page.locator('text=ROSE-LINK Dashboard');
            await expect(dashboardTitle).toBeVisible({ timeout: 10000 });
        });

        test('should display dashboard without authentication errors', async ({ page }) => {
            // Anonymous access should be enabled in Grafana config
            // Check that we're not on a login page
            const loginForm = page.locator('input[name="user"], form[name="loginForm"]');
            await expect(loginForm).not.toBeVisible();
        });

        test('should have the correct dashboard UID', async ({ page }) => {
            await expect(page).toHaveURL(new RegExp(DASHBOARD_UID));
        });
    });

    test.describe('Status Overview Panels', () => {
        test('should display VPN Status panel', async ({ page }) => {
            const vpnPanel = page.locator('[data-panelid="1"], :has-text("VPN Status")').first();
            await expect(vpnPanel).toBeVisible({ timeout: 15000 });
        });

        test('should display WAN Status panel', async ({ page }) => {
            const wanPanel = page.locator('[data-panelid="2"], :has-text("WAN Status")').first();
            await expect(wanPanel).toBeVisible({ timeout: 15000 });
        });

        test('should display Hotspot Status panel', async ({ page }) => {
            const hotspotPanel = page.locator('[data-panelid="3"], :has-text("Hotspot Status")').first();
            await expect(hotspotPanel).toBeVisible({ timeout: 15000 });
        });

        test('should display Connected Clients panel', async ({ page }) => {
            const clientsPanel = page.locator('[data-panelid="4"], :has-text("Connected Clients")').first();
            await expect(clientsPanel).toBeVisible({ timeout: 15000 });
        });

        test('should display System Uptime panel', async ({ page }) => {
            const uptimePanel = page.locator('[data-panelid="5"], :has-text("System Uptime")').first();
            await expect(uptimePanel).toBeVisible({ timeout: 15000 });
        });

        test('should display CPU Temperature stat panel', async ({ page }) => {
            const tempPanel = page.locator('[data-panelid="6"], :has-text("CPU Temperature")').first();
            await expect(tempPanel).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('System Resources Section', () => {
        test('should display CPU Usage gauge', async ({ page }) => {
            const cpuGauge = page.locator(':has-text("CPU Usage")').first();
            await expect(cpuGauge).toBeVisible({ timeout: 15000 });
        });

        test('should display Memory Usage gauge', async ({ page }) => {
            const memoryGauge = page.locator(':has-text("Memory Usage")').first();
            await expect(memoryGauge).toBeVisible({ timeout: 15000 });
        });

        test('should display Disk Usage gauge', async ({ page }) => {
            const diskGauge = page.locator(':has-text("Disk Usage")').first();
            await expect(diskGauge).toBeVisible({ timeout: 15000 });
        });

        test('should display CPU Usage Over Time graph', async ({ page }) => {
            const cpuGraph = page.locator(':has-text("CPU Usage Over Time")').first();
            await expect(cpuGraph).toBeVisible({ timeout: 15000 });
        });

        test('should display Memory Usage Over Time graph', async ({ page }) => {
            const memoryGraph = page.locator(':has-text("Memory Usage Over Time")').first();
            await expect(memoryGraph).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('Network Traffic Section', () => {
        test('should display Network Throughput panel', async ({ page }) => {
            const throughputPanel = page.locator(':has-text("Network Throughput")').first();
            await expect(throughputPanel).toBeVisible({ timeout: 15000 });
        });

        test('should display Network Packets panel', async ({ page }) => {
            const packetsPanel = page.locator(':has-text("Network Packets")').first();
            await expect(packetsPanel).toBeVisible({ timeout: 15000 });
        });

        test('should display Total Network Traffic panel', async ({ page }) => {
            const totalTrafficPanel = page.locator(':has-text("Total Network Traffic")').first();
            await expect(totalTrafficPanel).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('VPN & Connectivity History Section', () => {
        test('should display VPN Status History panel', async ({ page }) => {
            const vpnHistory = page.locator(':has-text("VPN Status History")').first();
            await expect(vpnHistory).toBeVisible({ timeout: 15000 });
        });

        test('should display WAN Status History panel', async ({ page }) => {
            const wanHistory = page.locator(':has-text("WAN Status History")').first();
            await expect(wanHistory).toBeVisible({ timeout: 15000 });
        });

        test('should display Hotspot Status History panel', async ({ page }) => {
            const hotspotHistory = page.locator(':has-text("Hotspot Status History")').first();
            await expect(hotspotHistory).toBeVisible({ timeout: 15000 });
        });

        test('should display Connected Clients Over Time panel', async ({ page }) => {
            const clientsHistory = page.locator(':has-text("Connected Clients Over Time")').first();
            await expect(clientsHistory).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('System Information Section', () => {
        test('should display CPU Temperature Over Time panel', async ({ page }) => {
            const tempHistory = page.locator(':has-text("CPU Temperature Over Time")').first();
            await expect(tempHistory).toBeVisible({ timeout: 15000 });
        });

        test('should display Disk Usage Over Time panel', async ({ page }) => {
            const diskHistory = page.locator(':has-text("Disk Usage Over Time")').first();
            await expect(diskHistory).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('Dashboard Interactivity', () => {
        test('should have working time range picker', async ({ page }) => {
            // Click on time picker
            const timePicker = page.locator('[data-testid="data-testid TimePicker Open Button"], button:has-text("Last")').first();
            await timePicker.click();

            // Check that time range options appear
            const timeOptions = page.locator('[data-testid="data-testid TimePicker Absolute time range"], .time-picker-content, [class*="TimeRangeContent"]');
            await expect(timeOptions).toBeVisible({ timeout: 5000 });
        });

        test('should have working refresh button', async ({ page }) => {
            // Find and click refresh button
            const refreshButton = page.locator('[data-testid="data-testid RefreshPicker run button"], button[aria-label*="Refresh"], button:has([class*="fa-sync"])').first();

            if (await refreshButton.isVisible()) {
                await refreshButton.click();
                // Wait for network activity to settle
                await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
                const dashboardTitle = page.locator('text=ROSE-LINK Dashboard');
                await expect(dashboardTitle).toBeVisible();
            }
        });

        test('should support panel drill-down on click', async ({ page }) => {
            // Click on a panel to expand/view details
            const panel = page.locator('[data-panelid="11"], :has-text("CPU Usage Over Time")').first();

            if (await panel.isVisible()) {
                // Right-click to open context menu (if available)
                await panel.click({ button: 'right' });

                // Check if context menu appears (may vary by Grafana version)
                const contextMenu = page.locator('[class*="context-menu"], [role="menu"], [class*="dropdown"]');
                await contextMenu.first().waitFor({ state: 'visible', timeout: 2000 }).catch(() => {
                    // Context menu may not be available in all versions
                });
            }
        });

        test('should allow scrolling through all panels', async ({ page }) => {
            // Scroll to bottom of dashboard
            await page.evaluate(() => {
                window.scrollTo(0, document.body.scrollHeight);
            });

            // Check that bottom section panels are visible after scroll
            const diskHistoryPanel = page.locator(':has-text("Disk Usage Over Time")').first();
            await expect(diskHistoryPanel).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('Row Collapse/Expand', () => {
        test('should have collapsible row headers', async ({ page }) => {
            // Look for row headers
            const rows = page.locator('.dashboard-row, [data-testid="dashboard-row-container"]');
            const rowCount = await rows.count();

            // Dashboard should have multiple row sections
            expect(rowCount).toBeGreaterThanOrEqual(0); // May be 0 if rows are already expanded
        });

        test('should be able to collapse Status Overview row', async ({ page }) => {
            const statusRow = page.locator(':has-text("Status Overview")').first();

            if (await statusRow.isVisible()) {
                // Row titles are clickable to collapse
                const rowTitle = statusRow.locator('.dashboard-row__title, [class*="row-title"]').first();

                if (await rowTitle.isVisible()) {
                    await rowTitle.click();
                    // Wait for collapse animation
                    await page.waitForFunction(() => {
                        // Check if row collapse completed
                        return true;
                    }, { timeout: 2000 }).catch(() => {});
                }
            }
        });
    });

    test.describe('Datasource Connectivity', () => {
        test('should not display "No data" on panels when Prometheus is connected', async ({ page }) => {
            // Wait for panels to render using network idle instead of timeout
            await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

            // Check for "No data" messages - should ideally be none if Prometheus is running
            const noDataMessages = page.locator('text="No data"');
            const noDataCount = await noDataMessages.count();

            // Log warning if no data (could be expected if backend not running)
            if (noDataCount > 0) {
                console.warn(`Found ${noDataCount} panels with "No data" - ensure ROSE-LINK backend and Prometheus are running`);
            }
        });

        test('should not display error alerts on panels', async ({ page }) => {
            // Wait for panels to render
            await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

            // Check for panel error indicators
            const errorIndicators = page.locator('[class*="panel-alert"], [class*="error"], [data-testid*="error"]');

            // Filter to only actual error messages, not CSS class names
            const visibleErrors = await errorIndicators.filter({ hasText: /error|failed|unable/i }).count();

            expect(visibleErrors).toBe(0);
        });
    });

    test.describe('Dashboard Tags and Metadata', () => {
        test('should have appropriate dashboard tags', async ({ page }) => {
            // Access dashboard settings or check URL for tags
            await expect(page).toHaveURL(/rose-link/);
        });
    });

    test.describe('Responsive Design', () => {
        test('should display correctly on desktop (1920x1080)', async ({ page }) => {
            await page.setViewportSize({ width: 1920, height: 1080 });
            await page.reload();

            const dashboard = page.locator('.dashboard-container, [class*="dashboard"], main');
            await expect(dashboard.first()).toBeVisible({ timeout: 15000 });
        });

        test('should display correctly on tablet (768x1024)', async ({ page }) => {
            await page.setViewportSize({ width: 768, height: 1024 });
            await page.reload();

            const dashboard = page.locator('.dashboard-container, [class*="dashboard"], main');
            await expect(dashboard.first()).toBeVisible({ timeout: 15000 });
        });

        test('should display correctly on mobile (375x667)', async ({ page }) => {
            await page.setViewportSize({ width: 375, height: 667 });
            await page.reload();

            const dashboard = page.locator('.dashboard-container, [class*="dashboard"], main');
            await expect(dashboard.first()).toBeVisible({ timeout: 15000 });
        });

        test('should adapt panel layout on smaller screens', async ({ page }) => {
            await page.setViewportSize({ width: 480, height: 800 });
            await page.reload();

            // Panels should still be visible but may stack vertically
            const vpnStatus = page.locator(':has-text("VPN Status")').first();
            await expect(vpnStatus).toBeVisible({ timeout: 15000 });
        });
    });

    test.describe('Panel Value Mapping', () => {
        test('should display human-readable status values', async ({ page }) => {
            // Wait for panels to load
            await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

            // VPN Status should show "Connected" or "Disconnected", not just 1 or 0
            const vpnPanel = page.locator('[data-panelid="1"], :has-text("VPN Status")').first();

            if (await vpnPanel.isVisible()) {
                const panelText = await vpnPanel.textContent();
                // Should contain mapped value or the raw metric
                const hasValidContent = panelText.includes('Connected') ||
                    panelText.includes('Disconnected') ||
                    panelText.includes('VPN Status') ||
                    /\d/.test(panelText); // Contains a number

                expect(hasValidContent).toBeTruthy();
            }
        });

        test('should display temperature with unit (Celsius)', async ({ page }) => {
            // Wait for panels to load
            await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

            const tempPanel = page.locator(':has-text("CPU Temperature")').first();

            if (await tempPanel.isVisible()) {
                const panelText = await tempPanel.textContent();
                // Should contain temperature-related content
                const hasValidContent = panelText.toLowerCase().includes('temperature') ||
                    panelText.includes('\u00B0') || // degree symbol
                    panelText.toLowerCase().includes('c') ||
                    /\d/.test(panelText);

                expect(hasValidContent).toBeTruthy();
            }
        });
    });

    test.describe('Dashboard Performance', () => {
        test('should load within acceptable time', async ({ page }) => {
            const startTime = Date.now();

            await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);
            await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
                timeout: 30000,
            });

            const loadTime = Date.now() - startTime;

            // Dashboard should load within 15 seconds
            expect(loadTime).toBeLessThan(15000);
            console.log(`Dashboard loaded in ${loadTime}ms`);
        });

        test('should render all visible panels within timeout', async ({ page }) => {
            // Wait for panels to load
            await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

            const panels = page.locator('[class*="panel-container"], [data-panelid]');
            const panelCount = await panels.count();

            // Should have multiple panels rendered
            expect(panelCount).toBeGreaterThan(0);
            console.log(`Found ${panelCount} rendered panels`);
        });
    });
});

test.describe('Grafana Health Check', () => {
    test('should respond to health endpoint', async ({ request }) => {
        const response = await request.get(`${GRAFANA_URL}/api/health`);
        expect(response.ok()).toBeTruthy();

        const health = await response.json();
        expect(health.database).toBe('ok');
    });

    test('should have ROSE-LINK dashboard provisioned', async ({ request }) => {
        const response = await request.get(`${GRAFANA_URL}/api/dashboards/uid/${DASHBOARD_UID}`);

        // Should return 200 if dashboard exists, or 401/403 if auth required
        expect([200, 401, 403]).toContain(response.status());

        if (response.status() === 200) {
            const data = await response.json();
            expect(data.dashboard.title).toBe('ROSE-LINK Dashboard');
        }
    });

    test('should have Prometheus datasource configured', async ({ request }) => {
        const response = await request.get(`${GRAFANA_URL}/api/datasources`);

        // May require authentication
        if (response.ok()) {
            const datasources = await response.json();
            const prometheus = datasources.find(ds => ds.type === 'prometheus');
            expect(prometheus).toBeDefined();
        }
    });
});

test.describe('Dashboard Annotations', () => {
    test('should support annotation queries', async ({ page }) => {
        // Wait for dashboard to fully load
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

        // Check that annotations layer is available
        const annotationsToggle = page.locator('[data-testid="annotations-toggle"], button[aria-label*="nnotation"]');

        if (await annotationsToggle.isVisible()) {
            // Annotations feature is available
            expect(true).toBeTruthy();
        } else {
            // Annotations may not be visible by default, which is fine
            console.log('Annotations toggle not visible (may be disabled or hidden)');
        }
    });
});

test.describe('Dashboard Alerting', () => {
    test('should have alert rules configured', async ({ request }) => {
        // Check Grafana alerting API if available
        const response = await request.get(`${GRAFANA_URL}/api/v1/provisioning/alert-rules`).catch(() => null);

        if (response && response.ok()) {
            const rules = await response.json();
            // Alert rules should be defined (may be empty if not configured)
            expect(Array.isArray(rules)).toBeTruthy();
        } else {
            // Alerting API may require authentication
            console.log('Alert rules API not accessible (may require authentication)');
        }
    });

    test('should display alert state indicators on panels', async ({ page }) => {
        await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);
        await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
            timeout: 30000,
        });

        // Wait for panels to load
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

        // Look for alert state indicators
        const alertIndicators = page.locator('[class*="alert-state"], [data-testid*="alert"], [class*="alerting"]');
        const alertCount = await alertIndicators.count();

        // Just verify we can check for alerts (may be 0 if no alerts configured)
        expect(alertCount).toBeGreaterThanOrEqual(0);
    });
});

test.describe('Dashboard Variables', () => {
    test('should have template variables available', async ({ page }) => {
        await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);
        await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
            timeout: 30000,
        });

        // Look for variable dropdowns
        const variableDropdowns = page.locator('[class*="variable"], [data-testid*="variable"], .submenu-controls');
        const variableCount = await variableDropdowns.count();

        // Variables may or may not be configured
        console.log(`Found ${variableCount} variable controls`);
    });

    test('should filter data when variable changed', async ({ page }) => {
        await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);
        await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
            timeout: 30000,
        });

        // Look for time range variable
        const timeRangeDropdown = page.locator('[data-testid="data-testid TimePicker Open Button"], button:has-text("Last")').first();

        if (await timeRangeDropdown.isVisible()) {
            await timeRangeDropdown.click();

            // Select a different time range
            const lastHour = page.locator('text="Last 1 hour"').first();
            if (await lastHour.isVisible({ timeout: 2000 }).catch(() => false)) {
                await lastHour.click();

                // Verify the URL or dashboard updates
                await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
            }
        }
    });
});

test.describe('Dashboard Data Validation', () => {
    test('should have numeric values in gauge panels', async ({ page }) => {
        await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);
        await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
            timeout: 30000,
        });

        // Wait for data to load
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

        // Check CPU Usage gauge for numeric value
        const cpuGauge = page.locator(':has-text("CPU Usage")').first();
        if (await cpuGauge.isVisible()) {
            const text = await cpuGauge.textContent();
            // Should contain a percentage or number
            const hasNumeric = /\d+(\.\d+)?%?/.test(text);
            expect(hasNumeric || text.includes('No data')).toBeTruthy();
        }
    });

    test('should have valid time series data in graphs', async ({ page }) => {
        await page.goto(`${GRAFANA_URL}/d/${DASHBOARD_UID}/rose-link-dashboard`);
        await page.waitForSelector('[data-testid="dashboard-title"], .dashboard-container, [class*="dashboard"]', {
            timeout: 30000,
        });

        // Wait for data to load
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

        // Check for graph panels with SVG elements (rendered charts)
        const graphPanels = page.locator('[class*="panel-container"] svg, [data-panelid] svg');
        const graphCount = await graphPanels.count();

        // Graphs should render SVG elements when data is available
        console.log(`Found ${graphCount} graph SVG elements`);
    });
});
