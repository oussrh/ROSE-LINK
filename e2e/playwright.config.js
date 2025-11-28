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

    // Run tests in parallel - use more workers in CI for faster execution
    fullyParallel: true,

    // Fail the build on CI if you accidentally left test.only in the source code
    forbidOnly: !!process.env.CI,

    // Retry only once on CI to reduce time for consistently failing tests
    retries: process.env.CI ? 1 : 0,

    // Use more workers in CI (GitHub runners have 2-4 cores)
    workers: process.env.CI ? 4 : undefined,

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

        // Reduced timeouts - fail fast rather than wait
        actionTimeout: 10000,

        // Navigation timeout
        navigationTimeout: 15000,
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

    // Timeout for each test - reduced for faster feedback
    timeout: 30000,

    // Timeout for expect assertions
    expect: {
        timeout: 5000,
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
