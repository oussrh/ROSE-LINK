/**
 * Tests for Internationalization (i18n) System
 */

import {
    loadTranslations,
    t,
    getCurrentLang,
    setLanguage,
    updateAllTranslations,
    updateLanguageButtons,
    initI18n
} from '../js/i18n.js';

describe('i18n System', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        localStorage.clear();
        fetch.mockClear();
    });

    describe('loadTranslations', () => {
        it('should load both English and French translations', async () => {
            const enTranslations = { hello: 'Hello', world: 'World' };
            const frTranslations = { hello: 'Bonjour', world: 'Monde' };

            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve(enTranslations)
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve(frTranslations)
                });

            await loadTranslations();

            expect(fetch).toHaveBeenCalledTimes(2);
            expect(fetch).toHaveBeenCalledWith('/locales/en.json');
            expect(fetch).toHaveBeenCalledWith('/locales/fr.json');
        });

        it('should handle fetch failures gracefully', async () => {
            fetch.mockRejectedValue(new Error('Network error'));

            // Should not throw
            await expect(loadTranslations()).resolves.not.toThrow();
        });

        it('should handle non-ok responses', async () => {
            fetch
                .mockResolvedValueOnce({ ok: false })
                .mockResolvedValueOnce({ ok: false });

            // Should not throw
            await expect(loadTranslations()).resolves.not.toThrow();
        });
    });

    describe('t (translate)', () => {
        beforeEach(async () => {
            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ hello: 'Hello', only_en: 'English only' })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ hello: 'Bonjour', only_fr: 'Francais seulement' })
                });

            await loadTranslations();
        });

        it('should return the key if translation not found', () => {
            const result = t('nonexistent_key');
            expect(result).toBe('nonexistent_key');
        });
    });

    describe('getCurrentLang', () => {
        it('should return current language', () => {
            const lang = getCurrentLang();
            expect(['en', 'fr']).toContain(lang);
        });
    });

    describe('setLanguage', () => {
        it('should save language to localStorage', () => {
            setLanguage('fr');

            expect(localStorage.setItem).toHaveBeenCalledWith('rose-lang', 'fr');
        });

        it('should update document lang attribute', () => {
            setLanguage('fr');

            expect(document.documentElement.lang).toBe('fr');
        });
    });

    describe('updateAllTranslations', () => {
        beforeEach(async () => {
            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({
                        test: 'Test English',
                        subtitle: 'VPN Router',
                        placeholder_text: 'Enter value',
                        tooltip_text: 'Help tooltip',
                        aria_text: 'Screen reader text'
                    })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({
                        test: 'Test Francais',
                        subtitle: 'Routeur VPN'
                    })
                });

            await loadTranslations();
        });

        it('should update elements with data-i18n attribute', () => {
            document.body.innerHTML = '<span data-i18n="test"></span>';

            updateAllTranslations();

            const element = document.querySelector('[data-i18n]');
            expect(element.textContent).toBeTruthy();
        });

        it('should update placeholders with data-i18n-placeholder', () => {
            document.body.innerHTML = '<input data-i18n-placeholder="placeholder_text" />';

            updateAllTranslations();

            const input = document.querySelector('input');
            expect(input.placeholder).toBeTruthy();
        });

        it('should update titles with data-i18n-title', () => {
            document.body.innerHTML = '<button data-i18n-title="tooltip_text"></button>';

            updateAllTranslations();

            const button = document.querySelector('button');
            expect(button.title).toBeTruthy();
        });

        it('should update aria labels with data-i18n-aria', () => {
            document.body.innerHTML = '<button data-i18n-aria="aria_text"></button>';

            updateAllTranslations();

            const button = document.querySelector('button');
            expect(button.getAttribute('aria-label')).toBeTruthy();
        });

        it('should update page title', () => {
            updateAllTranslations();

            expect(document.title).toContain('ROSE Link');
        });
    });

    describe('updateLanguageButtons', () => {
        it('should highlight English button when lang is en', () => {
            document.body.innerHTML = `
                <button id="lang-en"></button>
                <button id="lang-fr"></button>
            `;

            setLanguage('en');
            updateLanguageButtons();

            const enBtn = document.getElementById('lang-en');
            const frBtn = document.getElementById('lang-fr');

            expect(enBtn.classList.contains('bg-rose-600')).toBe(true);
            expect(frBtn.classList.contains('text-gray-400')).toBe(true);
        });

        it('should highlight French button when lang is fr', () => {
            document.body.innerHTML = `
                <button id="lang-en"></button>
                <button id="lang-fr"></button>
            `;

            setLanguage('fr');
            updateLanguageButtons();

            const enBtn = document.getElementById('lang-en');
            const frBtn = document.getElementById('lang-fr');

            expect(frBtn.classList.contains('bg-rose-600')).toBe(true);
            expect(enBtn.classList.contains('text-gray-400')).toBe(true);
        });

        it('should handle missing buttons gracefully', () => {
            document.body.innerHTML = '';

            // Should not throw
            expect(() => updateLanguageButtons()).not.toThrow();
        });
    });

    describe('initI18n', () => {
        it('should load translations and update UI', async () => {
            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ subtitle: 'VPN Router' })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ subtitle: 'Routeur VPN' })
                });

            await initI18n();

            expect(fetch).toHaveBeenCalledTimes(2);
        });
    });

    describe('global availability', () => {
        it('should expose setLanguage on window', () => {
            expect(window.setLanguage).toBeDefined();
            expect(typeof window.setLanguage).toBe('function');
        });
    });
});
