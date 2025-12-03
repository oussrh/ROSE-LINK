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

        it('should not add duplicate aria-describedby hints', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <input id="username" type="text" aria-describedby="username-hint">
                    <span id="username-hint">Enter your username</span>
                </form>
            `;

            const form = document.getElementById('test-form');
            enhanceFormAccessibility(form);

            const input = document.getElementById('username');
            // Should not duplicate the hint id
            expect(input.getAttribute('aria-describedby')).toBe('username-hint');
        });

        it('should not override existing aria-required', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <input id="email" type="email" required aria-required="true">
                </form>
            `;

            const form = document.getElementById('test-form');
            enhanceFormAccessibility(form);

            const input = document.getElementById('email');
            expect(input.getAttribute('aria-required')).toBe('true');
        });

        it('should handle select and textarea elements', () => {
            document.body.innerHTML = `
                <form id="test-form">
                    <select id="country" required>
                        <option>US</option>
                    </select>
                    <span id="country-hint">Select your country</span>
                    <textarea id="message" required></textarea>
                    <span id="message-hint">Enter your message</span>
                </form>
            `;

            const form = document.getElementById('test-form');
            enhanceFormAccessibility(form);

            const select = document.getElementById('country');
            const textarea = document.getElementById('message');
            expect(select.getAttribute('aria-describedby')).toBe('country-hint');
            expect(select.getAttribute('aria-required')).toBe('true');
            expect(textarea.getAttribute('aria-describedby')).toBe('message-hint');
            expect(textarea.getAttribute('aria-required')).toBe('true');
        });
    });

    describe('announce without initialization', () => {
        it('should auto-initialize when announcing without prior init', async () => {
            // Reset modules to clear any cached liveRegion
            jest.resetModules();

            // Re-import to get fresh module state
            const { announce: freshAnnounce } = await import('../../js/utils/a11y.js');

            // Announce without calling initA11y first
            freshAnnounce('Auto init message');
            jest.advanceTimersByTime(100);

            const liveRegion = document.getElementById('a11y-live-region');
            expect(liveRegion).not.toBeNull();
            expect(liveRegion.textContent).toBe('Auto init message');
        });
    });

    describe('setupKeyboardShortcuts', () => {
        let setupKeyboardShortcuts;

        beforeEach(async () => {
            const module = await import('../../js/utils/a11y.js');
            setupKeyboardShortcuts = module.setupKeyboardShortcuts;
        });

        it('should register keyboard shortcuts', () => {
            const handler = jest.fn();
            const shortcuts = {
                's': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 's',
                bubbles: true
            });
            document.dispatchEvent(event);

            expect(handler).toHaveBeenCalled();
        });

        it('should handle ctrl+key combinations', () => {
            const handler = jest.fn();
            const shortcuts = {
                'ctrl+s': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 's',
                ctrlKey: true,
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            document.dispatchEvent(event);

            expect(handler).toHaveBeenCalled();
        });

        it('should handle alt+key combinations', () => {
            const handler = jest.fn();
            const shortcuts = {
                'alt+a': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 'a',
                altKey: true,
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            document.dispatchEvent(event);

            expect(handler).toHaveBeenCalled();
        });

        it('should handle shift+key combinations', () => {
            const handler = jest.fn();
            const shortcuts = {
                'shift+x': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 'x',
                shiftKey: true,
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            document.dispatchEvent(event);

            expect(handler).toHaveBeenCalled();
        });

        it('should handle complex key combinations', () => {
            const handler = jest.fn();
            const shortcuts = {
                'ctrl+alt+shift+d': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 'd',
                ctrlKey: true,
                altKey: true,
                shiftKey: true,
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            document.dispatchEvent(event);

            expect(handler).toHaveBeenCalled();
        });

        it('should not trigger handler for unregistered shortcuts', () => {
            const handler = jest.fn();
            const shortcuts = {
                'ctrl+s': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 'z',
                ctrlKey: true,
                bubbles: true
            });
            document.dispatchEvent(event);

            expect(handler).not.toHaveBeenCalled();
        });

        it('should return cleanup function', () => {
            const handler = jest.fn();
            const shortcuts = { 'a': handler };

            const cleanup = setupKeyboardShortcuts(shortcuts);
            expect(typeof cleanup).toBe('function');

            // Cleanup and verify handler no longer called
            cleanup();

            const event = new KeyboardEvent('keydown', {
                key: 'a',
                bubbles: true
            });
            document.dispatchEvent(event);

            expect(handler).not.toHaveBeenCalled();
        });

        it('should call preventDefault when shortcut matches', () => {
            const handler = jest.fn();
            const shortcuts = {
                'ctrl+s': handler
            };

            setupKeyboardShortcuts(shortcuts);

            const event = new KeyboardEvent('keydown', {
                key: 's',
                ctrlKey: true,
                bubbles: true
            });
            const preventDefault = jest.fn();
            Object.defineProperty(event, 'preventDefault', { value: preventDefault });
            document.dispatchEvent(event);

            expect(preventDefault).toHaveBeenCalled();
        });
    });

    describe('makeKeyboardDraggable', () => {
        let makeKeyboardDraggable;

        beforeEach(async () => {
            const module = await import('../../js/utils/a11y.js');
            makeKeyboardDraggable = module.makeKeyboardDraggable;
        });

        it('should set ARIA attributes on element', () => {
            const element = document.createElement('div');
            document.body.appendChild(element);

            makeKeyboardDraggable(element);

            expect(element.getAttribute('role')).toBe('button');
            expect(element.getAttribute('tabindex')).toBe('0');
            expect(element.getAttribute('aria-grabbed')).toBe('false');
        });

        it('should handle ArrowUp key', () => {
            const element = document.createElement('div');
            element.style.position = 'absolute';
            element.style.top = '100px';
            element.style.left = '100px';
            document.body.appendChild(element);

            makeKeyboardDraggable(element);

            const event = new KeyboardEvent('keydown', {
                key: 'ArrowUp',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            element.dispatchEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should handle ArrowDown key', () => {
            const element = document.createElement('div');
            element.style.position = 'absolute';
            element.style.top = '100px';
            document.body.appendChild(element);

            makeKeyboardDraggable(element);

            const event = new KeyboardEvent('keydown', {
                key: 'ArrowDown',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            element.dispatchEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should handle ArrowLeft key', () => {
            const element = document.createElement('div');
            element.style.position = 'absolute';
            element.style.left = '100px';
            document.body.appendChild(element);

            makeKeyboardDraggable(element);

            const event = new KeyboardEvent('keydown', {
                key: 'ArrowLeft',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            element.dispatchEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should handle ArrowRight key', () => {
            const element = document.createElement('div');
            element.style.position = 'absolute';
            element.style.left = '100px';
            document.body.appendChild(element);

            makeKeyboardDraggable(element);

            const event = new KeyboardEvent('keydown', {
                key: 'ArrowRight',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            element.dispatchEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should use custom step size', () => {
            const element = document.createElement('div');
            element.style.position = 'absolute';
            document.body.appendChild(element);

            makeKeyboardDraggable(element, { step: 20 });

            // The step is stored internally, just verify no errors
            const event = new KeyboardEvent('keydown', {
                key: 'ArrowUp',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            element.dispatchEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should ignore non-arrow keys', () => {
            const element = document.createElement('div');
            document.body.appendChild(element);

            makeKeyboardDraggable(element);

            const event = new KeyboardEvent('keydown', {
                key: 'Enter',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            element.dispatchEvent(event);

            // preventDefault should NOT be called for non-arrow keys
            expect(event.preventDefault).not.toHaveBeenCalled();
        });
    });

    describe('releaseFocus', () => {
        let releaseFocus;

        beforeEach(async () => {
            const module = await import('../../js/utils/a11y.js');
            releaseFocus = module.releaseFocus;
        });

        it('should focus returnFocus element when provided', () => {
            const returnElement = document.createElement('button');
            returnElement.focus = jest.fn();
            document.body.appendChild(returnElement);

            const element = document.createElement('div');
            document.body.appendChild(element);

            releaseFocus(element, returnElement);

            expect(returnElement.focus).toHaveBeenCalled();
        });

        it('should not throw when returnFocus is null', () => {
            const element = document.createElement('div');
            document.body.appendChild(element);

            expect(() => releaseFocus(element, null)).not.toThrow();
        });

        it('should not throw when returnFocus lacks focus method', () => {
            const element = document.createElement('div');
            document.body.appendChild(element);

            const badElement = {};
            expect(() => releaseFocus(element, badElement)).not.toThrow();
        });
    });

    describe('trapFocus cleanup', () => {
        it('should restore focus on cleanup', () => {
            const previousButton = document.createElement('button');
            previousButton.id = 'previous';
            document.body.appendChild(previousButton);
            previousButton.focus();

            const modal = document.createElement('div');
            modal.innerHTML = `
                <button id="modal-btn">Modal Button</button>
            `;
            document.body.appendChild(modal);

            const cleanup = trapFocus(modal);

            // Cleanup should restore focus to previously focused element
            cleanup();

            // The cleanup attempts to restore focus
            expect(document.activeElement).toBe(previousButton);
        });

        it('should handle cleanup when previouslyFocused has no focus method', () => {
            // Simulate document.activeElement being a non-focusable element
            const modal = document.createElement('div');
            modal.innerHTML = `
                <button id="modal-btn">Modal Button</button>
            `;
            document.body.appendChild(modal);

            const cleanup = trapFocus(modal);

            // Should not throw even if original element can't be focused
            expect(() => cleanup()).not.toThrow();
        });

        it('should ignore non-Tab keys in trap', () => {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <button id="first">First</button>
                <button id="last">Last</button>
            `;
            document.body.appendChild(modal);

            trapFocus(modal);

            const event = new KeyboardEvent('keydown', {
                key: 'Enter',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            modal.dispatchEvent(event);

            // preventDefault should not be called for non-Tab keys
            expect(event.preventDefault).not.toHaveBeenCalled();
        });

        it('should handle Tab when not at boundaries', () => {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <button id="first">First</button>
                <input id="middle" type="text">
                <button id="last">Last</button>
            `;
            document.body.appendChild(modal);

            trapFocus(modal);

            // Focus middle element
            const middle = document.getElementById('middle');
            middle.focus();

            const event = new KeyboardEvent('keydown', {
                key: 'Tab',
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            modal.dispatchEvent(event);

            // Should not prevent default when in the middle
            expect(event.preventDefault).not.toHaveBeenCalled();
        });

        it('should handle Shift+Tab when not at first element', () => {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <button id="first">First</button>
                <input id="middle" type="text">
                <button id="last">Last</button>
            `;
            document.body.appendChild(modal);

            trapFocus(modal);

            // Focus middle element
            const middle = document.getElementById('middle');
            middle.focus();

            const event = new KeyboardEvent('keydown', {
                key: 'Tab',
                shiftKey: true,
                bubbles: true
            });
            Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
            modal.dispatchEvent(event);

            // Should not prevent default when in the middle
            expect(event.preventDefault).not.toHaveBeenCalled();
        });

        it('should handle modal with no focusable elements', () => {
            const modal = document.createElement('div');
            modal.innerHTML = `<p>No focusable content</p>`;
            document.body.appendChild(modal);

            // Should not throw when no focusable elements
            expect(() => trapFocus(modal)).not.toThrow();
        });
    });

    describe('initA11y skip link and modal setup', () => {
        it('should setup skip link when present', () => {
            document.body.innerHTML = `
                <a href="#main-content" id="skip-link">Skip to content</a>
                <main id="main-content">Main content</main>
            `;

            initA11y();

            const skipLink = document.getElementById('skip-link');
            const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
            Object.defineProperty(clickEvent, 'preventDefault', { value: jest.fn() });
            skipLink.dispatchEvent(clickEvent);

            expect(clickEvent.preventDefault).toHaveBeenCalled();
            const mainContent = document.getElementById('main-content');
            expect(mainContent.getAttribute('tabindex')).toBe('-1');
        });

        it('should handle skip link when main content is missing', () => {
            document.body.innerHTML = `
                <a href="#main-content" id="skip-link">Skip to content</a>
            `;

            initA11y();

            const skipLink = document.getElementById('skip-link');
            const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
            Object.defineProperty(clickEvent, 'preventDefault', { value: jest.fn() });

            // Should not throw
            expect(() => skipLink.dispatchEvent(clickEvent)).not.toThrow();
        });

        it('should remove tabindex from main content on blur', () => {
            document.body.innerHTML = `
                <a href="#main-content" id="skip-link">Skip to content</a>
                <main id="main-content">Main content</main>
            `;

            initA11y();

            const skipLink = document.getElementById('skip-link');
            const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
            Object.defineProperty(clickEvent, 'preventDefault', { value: jest.fn() });
            skipLink.dispatchEvent(clickEvent);

            const mainContent = document.getElementById('main-content');
            expect(mainContent.getAttribute('tabindex')).toBe('-1');

            // Trigger blur
            const blurEvent = new FocusEvent('blur', { bubbles: true });
            mainContent.dispatchEvent(blurEvent);

            expect(mainContent.getAttribute('tabindex')).toBeNull();
        });

        it('should setup modal focus management when wizard exists', () => {
            document.body.innerHTML = `
                <div id="setup-wizard" class="hidden">
                    <button>Wizard button</button>
                </div>
            `;

            // Mock MutationObserver
            const mockObserve = jest.fn();
            global.MutationObserver = jest.fn().mockImplementation((callback) => ({
                observe: mockObserve,
                disconnect: jest.fn()
            }));

            initA11y();

            expect(mockObserve).toHaveBeenCalled();
        });

        it('should trap focus when wizard modal becomes visible', () => {
            document.body.innerHTML = `
                <div id="setup-wizard" class="hidden">
                    <button id="wizard-btn">Wizard button</button>
                </div>
            `;

            let observerCallback;
            global.MutationObserver = jest.fn().mockImplementation((callback) => {
                observerCallback = callback;
                return {
                    observe: jest.fn(),
                    disconnect: jest.fn()
                };
            });

            initA11y();

            // Simulate class change removing hidden
            const wizard = document.getElementById('setup-wizard');
            wizard.classList.remove('hidden');

            // Trigger the observer callback
            observerCallback([{ attributeName: 'class' }]);

            // The first focusable element should be focused
            expect(document.activeElement.id).toBe('wizard-btn');
        });

        it('should not trap focus when wizard remains hidden', () => {
            document.body.innerHTML = `
                <button id="outside-btn">Outside</button>
                <div id="setup-wizard" class="hidden">
                    <button id="wizard-btn">Wizard button</button>
                </div>
            `;

            const outsideBtn = document.getElementById('outside-btn');
            outsideBtn.focus();

            let observerCallback;
            global.MutationObserver = jest.fn().mockImplementation((callback) => {
                observerCallback = callback;
                return {
                    observe: jest.fn(),
                    disconnect: jest.fn()
                };
            });

            initA11y();

            // Trigger the observer callback but wizard is still hidden
            observerCallback([{ attributeName: 'class' }]);

            // Focus should remain on outside button
            expect(document.activeElement.id).toBe('outside-btn');
        });

        it('should ignore non-class attribute mutations', () => {
            document.body.innerHTML = `
                <button id="outside-btn">Outside</button>
                <div id="setup-wizard" class="hidden">
                    <button id="wizard-btn">Wizard button</button>
                </div>
            `;

            const outsideBtn = document.getElementById('outside-btn');
            outsideBtn.focus();

            let observerCallback;
            global.MutationObserver = jest.fn().mockImplementation((callback) => {
                observerCallback = callback;
                return {
                    observe: jest.fn(),
                    disconnect: jest.fn()
                };
            });

            initA11y();

            // Trigger the observer callback with a different attribute
            observerCallback([{ attributeName: 'data-test' }]);

            // Focus should remain on outside button
            expect(document.activeElement.id).toBe('outside-btn');
        });
    });
});
