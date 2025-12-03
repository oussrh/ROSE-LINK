/**
 * Jest Test Setup for ROSE Link Web Interface
 *
 * This file runs before each test file to set up the testing environment.
 */

import '@testing-library/jest-dom';

// Mock localStorage
const localStorageMock = (() => {
    let store = {};
    return {
        getItem: jest.fn((key) => store[key] ?? null),
        setItem: jest.fn((key, value) => { store[key] = String(value); }),
        removeItem: jest.fn((key) => { delete store[key]; }),
        clear: jest.fn(() => { store = {}; }),
        get length() { return Object.keys(store).length; },
        key: jest.fn((i) => Object.keys(store)[i] ?? null),
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true
});

global.localStorage = localStorageMock;

// Mock fetch API
global.fetch = jest.fn(() =>
    Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
    })
);

// Mock htmx (loaded globally in the browser)
global.htmx = {
    process: jest.fn(),
    trigger: jest.fn(),
    ajax: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
};

// Mock lucide icons
global.lucide = {
    createIcons: jest.fn(),
};

// Mock console methods for cleaner test output
global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    // Keep warn and error for test debugging
};

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    fetch.mockClear();
});

// Clean up DOM after each test
afterEach(() => {
    document.body.innerHTML = '';
});
