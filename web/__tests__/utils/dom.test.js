/**
 * Tests for DOM Utilities
 */

import {
    escapeHtml,
    escapeJs,
    icon,
    refreshIcons,
    spinnerSvg,
    setButtonLoading,
    formatBytes
} from '../../js/utils/dom.js';

describe('DOM Utilities', () => {
    describe('escapeHtml', () => {
        it('should escape HTML special characters', () => {
            expect(escapeHtml('<script>alert("xss")</script>'))
                .toBe('&lt;script&gt;alert("xss")&lt;/script&gt;');
        });

        it('should escape ampersands', () => {
            expect(escapeHtml('foo & bar')).toBe('foo &amp; bar');
        });

        it('should escape quotes', () => {
            expect(escapeHtml('"hello"')).toBe('"hello"');
            expect(escapeHtml("'world'")).toBe("'world'");
        });

        it('should handle null input', () => {
            expect(escapeHtml(null)).toBe('');
        });

        it('should handle undefined input', () => {
            expect(escapeHtml(undefined)).toBe('');
        });

        it('should convert numbers to strings', () => {
            expect(escapeHtml(123)).toBe('123');
        });

        it('should handle empty string', () => {
            expect(escapeHtml('')).toBe('');
        });

        it('should handle normal text without escaping', () => {
            expect(escapeHtml('Hello World')).toBe('Hello World');
        });
    });

    describe('escapeJs', () => {
        it('should escape single quotes', () => {
            expect(escapeJs("it's")).toBe("it\\'s");
        });

        it('should escape backslashes', () => {
            expect(escapeJs('path\\to\\file')).toBe('path\\\\to\\\\file');
        });

        it('should handle null input', () => {
            expect(escapeJs(null)).toBe('');
        });

        it('should handle undefined input', () => {
            expect(escapeJs(undefined)).toBe('');
        });

        it('should handle combined escapes', () => {
            expect(escapeJs("it's a \\path")).toBe("it\\'s a \\\\path");
        });
    });

    describe('icon', () => {
        it('should create icon HTML with default class', () => {
            const result = icon('wifi');
            expect(result).toBe('<i data-lucide="wifi" class="icon-sm"></i>');
        });

        it('should create icon HTML with custom class', () => {
            const result = icon('shield', 'icon-lg');
            expect(result).toBe('<i data-lucide="shield" class="icon-lg"></i>');
        });

        it('should escape icon name to prevent XSS', () => {
            const result = icon('<script>');
            expect(result).toContain('&lt;script&gt;');
        });

        it('should escape class name to prevent XSS', () => {
            const result = icon('wifi', '"><script>');
            expect(result).toContain('"&gt;&lt;script&gt;');
        });
    });

    describe('refreshIcons', () => {
        it('should call lucide.createIcons when lucide is defined', () => {
            refreshIcons();
            expect(lucide.createIcons).toHaveBeenCalled();
        });

        it('should not throw when lucide is undefined', () => {
            const originalLucide = global.lucide;
            global.lucide = undefined;

            expect(() => refreshIcons()).not.toThrow();

            global.lucide = originalLucide;
        });
    });

    describe('spinnerSvg', () => {
        it('should be a valid SVG string', () => {
            expect(spinnerSvg).toContain('<svg');
            expect(spinnerSvg).toContain('</svg>');
        });

        it('should include spin-slow animation class', () => {
            expect(spinnerSvg).toContain('spin-slow');
        });
    });

    describe('setButtonLoading', () => {
        let button;

        beforeEach(() => {
            button = document.createElement('button');
            button.innerHTML = 'Submit';
            document.body.appendChild(button);
        });

        it('should disable button when loading', () => {
            setButtonLoading(button, true);
            expect(button.disabled).toBe(true);
        });

        it('should add opacity class when loading', () => {
            setButtonLoading(button, true);
            expect(button.classList.contains('opacity-75')).toBe(true);
            expect(button.classList.contains('cursor-not-allowed')).toBe(true);
        });

        it('should store original content in dataset', () => {
            setButtonLoading(button, true);
            expect(button.dataset.originalContent).toBe('Submit');
        });

        it('should show spinner when loading', () => {
            setButtonLoading(button, true);
            expect(button.innerHTML).toContain('svg');
        });

        it('should enable button when not loading', () => {
            setButtonLoading(button, true);
            setButtonLoading(button, false);
            expect(button.disabled).toBe(false);
        });

        it('should restore original content when not loading', () => {
            setButtonLoading(button, true);
            setButtonLoading(button, false);
            expect(button.innerHTML).toBe('Submit');
        });

        it('should remove loading classes when not loading', () => {
            setButtonLoading(button, true);
            setButtonLoading(button, false);
            expect(button.classList.contains('opacity-75')).toBe(false);
            expect(button.classList.contains('cursor-not-allowed')).toBe(false);
        });

        it('should handle null button gracefully', () => {
            expect(() => setButtonLoading(null, true)).not.toThrow();
        });

        it('should delete originalContent from dataset after restore', () => {
            setButtonLoading(button, true);
            setButtonLoading(button, false);
            expect(button.dataset.originalContent).toBeUndefined();
        });
    });

    describe('formatBytes', () => {
        it('should return "0 B" for 0 bytes', () => {
            expect(formatBytes(0)).toBe('0 B');
        });

        it('should format bytes correctly', () => {
            expect(formatBytes(500)).toBe('500 B');
        });

        it('should format kilobytes correctly', () => {
            expect(formatBytes(1024)).toBe('1 KB');
            expect(formatBytes(1536)).toBe('1.5 KB');
        });

        it('should format megabytes correctly', () => {
            expect(formatBytes(1048576)).toBe('1 MB');
            expect(formatBytes(1572864)).toBe('1.5 MB');
        });

        it('should format gigabytes correctly', () => {
            expect(formatBytes(1073741824)).toBe('1 GB');
        });

        it('should round to one decimal place', () => {
            expect(formatBytes(1234567)).toBe('1.2 MB');
        });
    });
});
