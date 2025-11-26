/**
 * Tests for Toast Notifications
 */

import { showToast } from '../../js/utils/toast.js';

describe('Toast Notifications', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('should create a toast element in the DOM', () => {
        showToast('Test message', 'info');

        const toast = document.querySelector('[role="alert"]');
        expect(toast).toBeInTheDocument();
        expect(toast.textContent).toBe('Test message');
    });

    it('should apply correct color class for success', () => {
        showToast('Success!', 'success');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.classList.contains('bg-green-600')).toBe(true);
    });

    it('should apply correct color class for error', () => {
        showToast('Error!', 'error');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.classList.contains('bg-red-600')).toBe(true);
    });

    it('should apply correct color class for warning', () => {
        showToast('Warning!', 'warning');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.classList.contains('bg-yellow-600')).toBe(true);
    });

    it('should apply info color class by default', () => {
        showToast('Info message');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.classList.contains('bg-blue-600')).toBe(true);
    });

    it('should set assertive aria-live for errors', () => {
        showToast('Error!', 'error');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.getAttribute('aria-live')).toBe('assertive');
    });

    it('should set polite aria-live for non-errors', () => {
        showToast('Info message', 'info');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.getAttribute('aria-live')).toBe('polite');
    });

    it('should have aria-atomic attribute', () => {
        showToast('Test message');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.getAttribute('aria-atomic')).toBe('true');
    });

    it('should remove toast after timeout', () => {
        showToast('Test message');

        expect(document.querySelector('[role="alert"]')).toBeInTheDocument();

        // Fast-forward past the dismiss timeout (3000ms)
        jest.advanceTimersByTime(3000);

        // Toast should start fade animation
        const toast = document.querySelector('[role="alert"]');
        expect(toast.classList.contains('opacity-0')).toBe(true);

        // Fast-forward past the animation (300ms)
        jest.advanceTimersByTime(300);

        // Toast should be removed
        expect(document.querySelector('[role="alert"]')).not.toBeInTheDocument();
    });

    it('should use textContent to prevent XSS', () => {
        showToast('<script>alert("xss")</script>');

        const toast = document.querySelector('[role="alert"]');
        expect(toast.innerHTML).not.toContain('<script>');
        expect(toast.textContent).toBe('<script>alert("xss")</script>');
    });

    it('should be available globally on window', () => {
        expect(window.showToast).toBeDefined();
        expect(typeof window.showToast).toBe('function');
    });

    it('should handle unknown toast type gracefully', () => {
        showToast('Unknown type', 'unknown');

        const toast = document.querySelector('[role="alert"]');
        // Should fall back to info color
        expect(toast.classList.contains('bg-blue-600')).toBe(true);
    });
});
