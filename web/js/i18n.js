/**
 * ROSE Link - Internationalization (i18n) System
 * Handles translations for English and French
 */

// Translation storage
const translations = {
    en: {},
    fr: {}
};

// Current language
let currentLang = localStorage.getItem('rose-lang') ||
    (navigator.language.startsWith('fr') ? 'fr' : 'en');

/**
 * Load translations from JSON files
 */
export async function loadTranslations() {
    try {
        const [enResponse, frResponse] = await Promise.all([
            fetch('/locales/en.json'),
            fetch('/locales/fr.json')
        ]);

        if (enResponse.ok) {
            translations.en = await enResponse.json();
        }
        if (frResponse.ok) {
            translations.fr = await frResponse.json();
        }
    } catch {
        console.warn('Could not load translations, using defaults');
    }
}

/**
 * Get translated string for a key
 * @param {string} key - Translation key
 * @returns {string} Translated string or key if not found
 */
export function t(key) {
    return translations[currentLang]?.[key] || translations['en']?.[key] || key;
}

/**
 * Get current language
 * @returns {string} Current language code
 */
export function getCurrentLang() {
    return currentLang;
}

/**
 * Set the current language
 * @param {string} lang - Language code ('en' or 'fr')
 */
export function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('rose-lang', lang);
    document.documentElement.lang = lang;
    updateAllTranslations();
    updateLanguageButtons();
}

/**
 * Update all translated elements in the DOM
 */
export function updateAllTranslations() {
    // Text content
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.getAttribute('data-i18n'));
    });

    // Placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });

    // Titles
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.title = t(el.getAttribute('data-i18n-title'));
    });

    // Aria labels
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
        el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
    });

    // Page title
    document.title = `ROSE Link - ${t('subtitle')}`;
}

/**
 * Update language button styles
 */
export function updateLanguageButtons() {
    const enBtn = document.getElementById('lang-en');
    const frBtn = document.getElementById('lang-fr');
    if (!enBtn || !frBtn) return;

    [enBtn, frBtn].forEach(btn => {
        btn.classList.remove('bg-rose-600', 'text-white', 'text-gray-400');
    });

    if (currentLang === 'en') {
        enBtn.classList.add('bg-rose-600', 'text-white');
        frBtn.classList.add('text-gray-400');
    } else {
        frBtn.classList.add('bg-rose-600', 'text-white');
        enBtn.classList.add('text-gray-400');
    }
}

/**
 * Initialize i18n system
 */
export async function initI18n() {
    await loadTranslations();
    updateAllTranslations();
    updateLanguageButtons();
}

// Make setLanguage globally available for onclick handlers
window.setLanguage = setLanguage;
