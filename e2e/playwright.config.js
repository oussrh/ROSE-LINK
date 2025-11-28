/**
 * Playwright E2E Test Configuration
 * @see https://playwright.dev/docs/test-configuration
 */

const { defineConfig, devices } = require('@playwright/test');

// Environment variables for different services
const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const GRAFANA_URL = process.env.GRAFANA_URL || 'http://localhost:3000';

module.exports = defineConfig({
    // Test directory
    testDir: './tests',

    // Run tests in parallel (but not in CI to avoid flakiness)
    fullyParallel: !process.env.CI,

    // Fail the build on CI if you accidentally left test.only in the source code
    forbidOnly: !!process.env.CI,

    // Retry on CI only
    retries: process.env.CI ? 2 : 0,

    // Number of workers
    workers: process.env.CI ? 1 : undefined,

    // Reporter configuration
    reporter: process.env.CI
        ? [['list'], ['json', { outputFile: 'test-results.json' }]]
        : [
            ['html', { outputFolder: 'playwright-report' }],
            ['json', { outputFile: 'test-results.json' }],
            ['list']
        ],

    // Shared settings for all projects
    use: {
        // Base URL for relative navigation
        baseURL: BASE_URL,

        // Collect trace when retrying the failed test
        trace: 'on-first-retry',

        // Screenshot on failure
        screenshot: 'only-on-failure',

        // Video on failure (disabled in CI to save resources)
        video: process.env.CI ? 'off' : 'on-first-retry',

        // Viewport
        viewport: { width: 1280, height: 720 },

        // Slower actions in CI for stability
        actionTimeout: process.env.CI ? 15000 : 10000,

        // Navigation timeout
        navigationTimeout: process.env.CI ? 30000 : 20000,
    },

    // Configure projects for major browsers
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
            testIgnore: /grafana\.spec\.js/, // Exclude Grafana tests from main run
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
            testIgnore: /grafana\.spec\.js/,
        },
        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
            testIgnore: /grafana\.spec\.js/,
        },
        // Mobile viewports
        {
            name: 'Mobile Chrome',
            use: { ...devices['Pixel 5'] },
            testIgnore: /grafana\.spec\.js/,
        },
        {
            name: 'Mobile Safari',
            use: { ...devices['iPhone 12'] },
            testIgnore: /grafana\.spec\.js/,
        },
        // Grafana-specific project
        {
            name: 'grafana',
            use: {
                ...devices['Desktop Chrome'],
                baseURL: GRAFANA_URL,
            },
            testMatch: /grafana\.spec\.js/,
        },
        {
            name: 'grafana-firefox',
            use: {
                ...devices['Desktop Firefox'],
                baseURL: GRAFANA_URL,
            },
            testMatch: /grafana\.spec\.js/,
        },
    ],

    // Timeout for each test (longer in CI)
    timeout: process.env.CI ? 60000 : 30000,

    // Timeout for expect assertions
    expect: {
        timeout: process.env.CI ? 10000 : 5000,
    },

    // Global setup/teardown
    globalSetup: undefined,
    globalTeardown: undefined,

    // Run local dev server before starting the tests
    // Uncomment if you want Playwright to start the server
    // webServer: {
    //     command: 'cd ../backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000',
    //     url: 'http://localhost:8000',
    //     reuseExistingServer: !process.env.CI,
    //     timeout: 120000,
    // },
});
