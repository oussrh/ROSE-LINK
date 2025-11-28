/**
 * ROSE Link - Accessibility Utilities Tests
 */

import {
    initA11y,
    announce,
    announceUrgent,
    announceLoading,
    announceComplete,
    trapFocus,
    prefersReducedMotion,
    prefersHighContrast,
    enhanceFormAccessibility,
} from '../../js/utils/a11y.js';

describe('Accessibility Utilities', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    describe('initA11y', () => {
        it('should create live region element', () => {
            initA11y();

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion).not.toBeNull();
            expect(liveRegion.getAttribute('role')).toBe('status');
            expect(liveRegion.getAttribute('aria-live')).toBe('polite');
            expect(liveRegion.getAttribute('aria-atomic')).toBe('true');
        });

        it('should not create duplicate live regions', () => {
            initA11y();
            initA11y();

            const liveRegions = document.querySelectorAll('#a11y-live-region');
            expect(liveRegions.length).toBe(1);
        });

        it('should have visually hidden styles', () => {
            initA11y();

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.className).toContain('sr-only');
        });
    });

    describe('announce', () => {
        beforeEach(() => {
            initA11y();
        });

        it('should set message in live region', () => {
            announce('Test message');
            jest.advanceTimersByTime(100);

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.textContent).toBe('Test message');
        });

        it('should use polite priority by default', () => {
            announce('Test message');

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.getAttribute('aria-live')).toBe('polite');
        });

        it('should support assertive priority', () => {
            announce('Urgent message', 'assertive');

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.getAttribute('aria-live')).toBe('assertive');
        });

        it('should clear previous message before setting new one', () => {
            announce('First message');
            jest.advanceTimersByTime(100);

            announce('Second message');
            const liveRegion = document.getElementById('a11y-live-region');
            // Message should be cleared initially
            expect(liveRegion.textContent).toBe('');

            jest.advanceTimersByTime(100);
            expect(liveRegion.textContent).toBe('Second message');
        });
    });

    describe('announceUrgent', () => {
        beforeEach(() => {
            initA11y();
        });

        it('should use assertive priority', () => {
            announceUrgent('Critical error');

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.getAttribute('aria-live')).toBe('assertive');
        });
    });

    describe('announceLoading', () => {
        beforeEach(() => {
            initA11y();
        });

        it('should announce loading without context', () => {
            announceLoading();
            jest.advanceTimersByTime(100);

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.textContent).toBe('Loading, please wait.');
        });

        it('should announce loading with context', () => {
            announceLoading('WiFi networks');
            jest.advanceTimersByTime(100);

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.textContent).toBe('Loading WiFi networks, please wait.');
        });
    });

    describe('announceComplete', () => {
        beforeEach(() => {
            initA11y();
        });

        it('should announce successful completion', () => {
            announceComplete('WiFi scan');
            jest.advanceTimersByTime(100);

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.textContent).toBe('WiFi scan completed successfully.');
        });

        it('should announce failed completion', () => {
            announceComplete('VPN connection', false);
            jest.advanceTimersByTime(100);

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion.textContent).toBe('VPN connection failed.');
        });
    });

    describe('trapFocus', () => {
        let modal;

        beforeEach(() => {
            modal = document.createElement('div');
            modal.innerHTML = `
                <button id="first">First</button>
                <input id="middle" type="text">
                <button id="last">Last</button>
            `;
            document.body.appendChild(modal);
        });

        it('should focus first focusable element', () => {
            trapFocus(modal);

            expect(document.activeElement.id).toBe('first');
        });

        it('should return cleanup function', () => {
            const cleanup = trapFocus(modal);

            expect(typeof cleanup).toBe('function');
        });

        it('should trap Tab at end of modal', () => {
            trapFocus(modal);

            const lastButton = document.getElementById('last');
            lastButton.focus();

            // Simulate Tab key
            const event = new KeyboardEvent('keydown', {
                key: 'Tab',
                bubbles: true,
            });
            Object.defineProperty(event, 'preventDefault', {
                value: jest.fn(),
            });

            modal.dispatchEvent(event);

            // Should prevent default and focus first element
            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should trap Shift+Tab at start of modal', () => {
            trapFocus(modal);

            const firstButton = document.getElementById('first');
            firstButton.focus();

            // Simulate Shift+Tab key
            const event = new KeyboardEvent('keydown', {
                key: 'Tab',
                shiftKey: true,
                bubbles: true,
            });
            Object.defineProperty(event, 'preventDefault', {
                value: jest.fn(),
            });

            modal.dispatchEvent(event);

            // Should prevent default
            expect(event.preventDefault).toHaveBeenCalled();
        });
    });

    describe('prefersReducedMotion', () => {
        beforeEach(() => {
            // Mock matchMedia for jsdom
            window.matchMedia = jest.fn().mockReturnValue({ matches: false });
        });

        it('should return boolean', () => {
            const result = prefersReducedMotion();
            expect(typeof result).toBe('boolean');
        });

        it('should check media query', () => {
            // Mock matchMedia
            const mockMatchMedia = jest.fn().mockReturnValue({ matches: true });
            window.matchMedia = mockMatchMedia;

            const result = prefersReducedMotion();

            expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)');
            expect(result).toBe(true);
        });
    });

    describe('prefersHighContrast', () => {
        beforeEach(() => {
            // Mock matchMedia for jsdom
            window.matchMedia = jest.fn().mockReturnValue({ matches: false });
        });

        it('should return boolean', () => {
            const result = prefersHighContrast();
            expect(typeof result).toBe('boolean');
        });

        it('should check media query', () => {
            const mockMatchMedia = jest.fn().mockReturnValue({ matches: false });
            window.matchMedia = mockMatchMedia;

            const result = prefersHighContrast();

            expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-contrast: more)');
            expect(result).toBe(false);
        });
    });

    describe('enhanceFormAccessibility', () => {
        it('should add aria-describedby for hints', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <input id="username" type="text">
                    <span id="username-hint">Enter your username</span>
                </form>
            `;

            const form = document.getElementById('test-form');
            enhanceFormAccessibility(form);

            const input = document.getElementById('username');
            expect(input.getAttribute('aria-describedby')).toBe('username-hint');
        });

        it('should add aria-required for required fields', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <input id="email" type="email" required>
                </form>
            `;

            const form = document.getElementById('test-form');
            enhanceFormAccessibility(form);

            const input = document.getElementById('email');
            expect(input.getAttribute('aria-required')).toBe('true');
        });

        it('should preserve existing aria-describedby', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <input id="password" type="password" aria-describedby="existing-desc">
                    <span id="password-hint">Password requirements</span>
                    <span id="existing-desc">Required field</span>
                </form>
            `;

            const form = document.getElementById('test-form');
            enhanceFormAccessibility(form);

            const input = document.getElementById('password');
            expect(input.getAttribute('aria-describedby')).toBe('existing-desc password-hint');
        });

        it('should handle forms without hints', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <input id="simple" type="text">
                </form>
            `;

            const form = document.getElementById('test-form');
            // Should not throw
            expect(() => enhanceFormAccessibility(form)).not.toThrow();
        });
    });
});
