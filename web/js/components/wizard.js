/**
 * ROSE Link - Setup Wizard Component
 * First-run wizard for initial configuration
 */

import { escapeHtml, icon, refreshIcons, setButtonLoading } from '../utils/dom.js';
import { t } from '../i18n.js';
import { showToast } from '../utils/toast.js';
import { showConfirm, showPrompt } from '../utils/modal.js';

const WIZARD_STORAGE_KEY = 'rose-link-wizard-completed';
const WIZARD_STEPS = ['welcome', 'wifi', 'vpn', 'hotspot', 'complete'];

let currentStep = 0;
let wizardData = {
    wifi: null,
    vpn: null,
    hotspot: {
        ssid: 'ROSE-Link',
        password: '',
        country: 'US',
        band: '2.4GHz',
        channel: 6,
        wpa3: false
    }
};

// Device capabilities - populated from system info
let deviceCapabilities = {
    singleWifi: false,  // True if device has only one WiFi (used for hotspot)
    loaded: false
};

/**
 * Check if wizard should be shown
 * @returns {boolean}
 */
export function shouldShowWizard() {
    return localStorage.getItem(WIZARD_STORAGE_KEY) !== 'true';
}

/**
 * Mark wizard as completed
 */
export function markWizardCompleted() {
    localStorage.setItem(WIZARD_STORAGE_KEY, 'true');
}

/**
 * Reset wizard state (for re-running setup)
 */
export function resetWizard() {
    localStorage.removeItem(WIZARD_STORAGE_KEY);
    currentStep = 0;
    wizardData = {
        wifi: null,
        vpn: null,
        hotspot: {
            ssid: 'ROSE-Link',
            password: '',
            country: 'US',
            band: '2.4GHz',
            channel: 6,
            wpa3: false
        }
    };
}

/**
 * Show the wizard overlay
 */
export function showWizard() {
    const wizard = document.getElementById('setup-wizard');
    if (wizard) {
        wizard.classList.remove('hidden');
        renderCurrentStep();
    }
}

/**
 * Hide the wizard overlay
 */
export function hideWizard() {
    const wizard = document.getElementById('setup-wizard');
    if (wizard) {
        wizard.classList.add('hidden');
    }
}

/**
 * Go to next step
 */
export function nextStep() {
    if (currentStep < WIZARD_STEPS.length - 1) {
        currentStep++;
        renderCurrentStep();
    }
}

/**
 * Go to previous step
 */
export function prevStep() {
    if (currentStep > 0) {
        currentStep--;
        renderCurrentStep();
    }
}

/**
 * Skip to a specific step
 * @param {number} step
 */
export function goToStep(step) {
    if (step >= 0 && step < WIZARD_STEPS.length) {
        currentStep = step;
        renderCurrentStep();
    }
}

/**
 * Complete the wizard
 */
export function completeWizard() {
    markWizardCompleted();
    hideWizard();
    showToast(t('wizard_complete_message'), 'success');
    // Trigger refresh of main UI
    if (typeof htmx !== 'undefined') {
        htmx.trigger('#status-cards', 'htmx:load');
    }
}

/**
 * Skip the wizard (closes without confirmation)
 */
export function skipWizard() {
    markWizardCompleted();
    hideWizard();
}

/**
 * Close wizard with confirmation
 */
export async function closeWizardWithConfirm() {
    const confirmed = await showConfirm({
        title: t('skip_wizard') || 'Skip Setup',
        message: t('wizard_skip_confirm') || 'Are you sure you want to skip the setup wizard? You can run it later from the menu.',
        confirmText: t('skip') || 'Skip',
        cancelText: t('cancel') || 'Cancel',
        variant: 'default',
        icon: 'skip-forward'
    });

    if (confirmed) {
        markWizardCompleted();
        hideWizard();
    }
}

/**
 * Render the current step
 */
function renderCurrentStep() {
    const container = document.getElementById('wizard-content');
    if (!container) return;

    const stepName = WIZARD_STEPS[currentStep];

    // Update progress indicators
    updateProgressIndicators();

    switch (stepName) {
        case 'welcome':
            renderWelcomeStep(container);
            break;
        case 'wifi':
            renderWifiStep(container);
            break;
        case 'vpn':
            renderVpnStep(container);
            break;
        case 'hotspot':
            renderHotspotStep(container);
            break;
        case 'complete':
            renderCompleteStep(container);
            break;
    }

    refreshIcons();
}

/**
 * Update progress indicator dots
 */
function updateProgressIndicators() {
    const indicators = document.querySelectorAll('.wizard-step-indicator');
    indicators.forEach((indicator, index) => {
        indicator.classList.remove('bg-rose-500', 'bg-gray-600');
        if (index <= currentStep) {
            indicator.classList.add('bg-rose-500');
        } else {
            indicator.classList.add('bg-gray-600');
        }
    });

    // Update step counter
    const stepCounter = document.getElementById('wizard-step-counter');
    if (stepCounter) {
        stepCounter.textContent = `${currentStep + 1} / ${WIZARD_STEPS.length}`;
    }
}

/**
 * Render welcome step
 */
function renderWelcomeStep(container) {
    container.innerHTML = `
        <div class="text-center py-6">
            <div class="w-20 h-20 mx-auto mb-6 bg-rose-500/20 rounded-full flex items-center justify-center">
                ${icon('wifi', 'w-10 h-10 text-rose-400')}
            </div>
            <h2 class="text-2xl font-bold mb-4">${t('wizard_welcome_title')}</h2>
            <p class="text-gray-400 mb-6 max-w-md mx-auto">${t('wizard_welcome_desc')}</p>

            <div class="bg-gray-700/50 rounded-lg p-4 mb-6 text-left max-w-md mx-auto">
                <h3 class="font-semibold mb-3 flex items-center gap-2">
                    ${icon('list-checks', 'icon-sm')} ${t('wizard_steps_overview')}
                </h3>
                <ul class="space-y-2 text-sm text-gray-300">
                    <li class="flex items-center gap-2">
                        ${icon('wifi', 'icon-sm text-blue-400')} ${t('wizard_step_wifi')}
                    </li>
                    <li class="flex items-center gap-2">
                        ${icon('shield', 'icon-sm text-green-400')} ${t('wizard_step_vpn')}
                    </li>
                    <li class="flex items-center gap-2">
                        ${icon('radio', 'icon-sm text-yellow-400')} ${t('wizard_step_hotspot')}
                    </li>
                </ul>
            </div>

            <div class="flex justify-center gap-3">
                <button onclick="window.skipWizard()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-smooth">
                    ${t('wizard_skip')}
                </button>
                <button onclick="window.nextStep()" class="px-6 py-2 bg-rose-600 hover:bg-rose-700 rounded-lg font-medium transition-smooth flex items-center gap-2">
                    ${t('wizard_get_started')} ${icon('arrow-right', 'icon-sm')}
                </button>
            </div>
        </div>
    `;
}

/**
 * Render WiFi setup step
 */
function renderWifiStep(container) {
    // Check if device has only one WiFi (single WiFi = no WiFi WAN available)
    if (deviceCapabilities.singleWifi) {
        // Single WiFi device - show message that Ethernet is required
        container.innerHTML = `
            <div class="py-4">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 mx-auto mb-4 bg-orange-500/20 rounded-full flex items-center justify-center">
                        ${icon('ethernet-port', 'w-8 h-8 text-orange-400')}
                    </div>
                    <h2 class="text-xl font-bold mb-2">${t('wizard_wifi_title')}</h2>
                    <p class="text-gray-400 text-sm">${t('single_wifi_device_desc')}</p>
                </div>

                <div class="bg-orange-900/30 border border-orange-700 rounded-lg p-4 mb-4">
                    <div class="flex items-start gap-3">
                        ${icon('alert-triangle', 'w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5')}
                        <div>
                            <p class="font-medium text-orange-300 mb-1">${t('single_wifi_title')}</p>
                            <p class="text-sm text-orange-200/80">${t('single_wifi_message')}</p>
                        </div>
                    </div>
                </div>

                <div class="bg-gray-700/50 rounded-lg p-4 mb-4">
                    <div class="flex items-center justify-between mb-3">
                        <span class="font-medium text-gray-400">${t('scan_networks')}</span>
                        <button disabled class="px-3 py-1 bg-gray-600 rounded text-sm text-gray-400 cursor-not-allowed flex items-center gap-1 opacity-50">
                            ${icon('search', 'icon-sm')} ${t('scan_networks')}
                        </button>
                    </div>
                    <div class="text-gray-500 text-sm text-center py-4">
                        ${icon('wifi-off', 'icon-sm inline-block mr-1')} ${t('wifi_wan_disabled')}
                    </div>
                </div>

                <div class="flex justify-between">
                    <button onclick="window.prevStep()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-smooth flex items-center gap-2">
                        ${icon('arrow-left', 'icon-sm')} ${t('wizard_back')}
                    </button>
                    <button onclick="window.nextStep()" class="px-6 py-2 bg-rose-600 hover:bg-rose-700 rounded-lg font-medium transition-smooth flex items-center gap-2">
                        ${t('wizard_next')} ${icon('arrow-right', 'icon-sm')}
                    </button>
                </div>
            </div>
        `;
        refreshIcons();
        return;
    }

    // Normal dual-WiFi device - show regular WiFi setup
    container.innerHTML = `
        <div class="py-4">
            <div class="text-center mb-6">
                <div class="w-16 h-16 mx-auto mb-4 bg-blue-500/20 rounded-full flex items-center justify-center">
                    ${icon('wifi', 'w-8 h-8 text-blue-400')}
                </div>
                <h2 class="text-xl font-bold mb-2">${t('wizard_wifi_title')}</h2>
                <p class="text-gray-400 text-sm">${t('wizard_wifi_desc')}</p>
            </div>

            <div class="bg-gray-700/50 rounded-lg p-4 mb-4">
                <div class="flex items-center justify-between mb-3">
                    <span class="font-medium">${t('scan_networks')}</span>
                    <button id="wizard-wifi-scan" class="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-smooth flex items-center gap-1">
                        ${icon('search', 'icon-sm')} ${t('scan_networks')}
                    </button>
                </div>
                <div id="wizard-wifi-networks" class="space-y-2 max-h-48 overflow-y-auto">
                    <p class="text-gray-400 text-sm text-center py-4">${t('click_scan')}</p>
                </div>
            </div>

            <div class="bg-gray-700/30 rounded-lg p-3 mb-6">
                <p class="text-xs text-gray-400 flex items-center gap-2">
                    ${icon('info', 'icon-sm')} ${t('wizard_wifi_optional')}
                </p>
            </div>

            <div class="flex justify-between">
                <button onclick="window.prevStep()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-smooth flex items-center gap-2">
                    ${icon('arrow-left', 'icon-sm')} ${t('wizard_back')}
                </button>
                <button onclick="window.nextStep()" class="px-6 py-2 bg-rose-600 hover:bg-rose-700 rounded-lg font-medium transition-smooth flex items-center gap-2">
                    ${wizardData.wifi ? t('wizard_next') : t('wizard_skip_step')} ${icon('arrow-right', 'icon-sm')}
                </button>
            </div>
        </div>
    `;

    // Set up WiFi scan handler
    const scanBtn = document.getElementById('wizard-wifi-scan');
    if (scanBtn) {
        scanBtn.addEventListener('click', () => scanWifiNetworks());
    }
}

/**
 * Scan for WiFi networks in wizard
 */
async function scanWifiNetworks() {
    const container = document.getElementById('wizard-wifi-networks');
    const scanBtn = document.getElementById('wizard-wifi-scan');
    if (!container || !scanBtn) return;

    setButtonLoading(scanBtn, true);

    try {
        const response = await fetch('/api/wifi/scan', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            renderWifiNetworksList(container, data.networks || []);
        } else {
            container.innerHTML = `<p class="text-red-400 text-sm text-center py-4">${t('error')}</p>`;
        }
    } catch {
        container.innerHTML = `<p class="text-red-400 text-sm text-center py-4">${t('error')}</p>`;
    } finally {
        setButtonLoading(scanBtn, false);
    }
}

/**
 * Render WiFi networks list in wizard
 */
function renderWifiNetworksList(container, networks) {
    if (networks.length === 0) {
        container.innerHTML = `<p class="text-gray-400 text-sm text-center py-4">${t('no_networks')}</p>`;
        return;
    }

    container.innerHTML = networks.map(net => `
        <div class="bg-gray-600/50 rounded p-2 flex items-center justify-between cursor-pointer hover:bg-gray-600 transition-smooth"
             data-ssid="${escapeHtml(net.ssid)}">
            <div class="flex items-center gap-2">
                ${icon('wifi', 'icon-sm')}
                <span class="text-sm">${escapeHtml(net.ssid)}</span>
            </div>
            <span class="text-xs text-gray-400">${net.signal}%</span>
        </div>
    `).join('');

    // Add click handlers
    container.querySelectorAll('[data-ssid]').forEach(el => {
        el.addEventListener('click', () => {
            const ssid = el.dataset.ssid;
            connectToWifiInWizard(ssid);
        });
    });

    refreshIcons();
}

/**
 * Connect to WiFi in wizard
 */
async function connectToWifiInWizard(ssid) {
    const password = await showPrompt({
        title: t('connect_to_wifi') || 'Connect to WiFi',
        message: `${t('password_for') || 'Enter password for'} ${ssid}`,
        placeholder: t('wifi_password') || 'WiFi password',
        inputType: 'password',
        confirmText: t('connect') || 'Connect',
        cancelText: t('cancel') || 'Cancel',
        icon: 'wifi'
    });

    if (!password) return;

    try {
        const response = await fetch('/api/wifi/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ssid, password })
        });

        if (response.ok) {
            wizardData.wifi = { ssid, connected: true };
            showToast(`${t('wifi_connected_to')} ${ssid}`, 'success');
            renderCurrentStep(); // Re-render to update button text
        } else {
            const data = await response.json();
            showToast(data.detail || t('connection_failed'), 'error');
        }
    } catch {
        showToast(t('error'), 'error');
    }
}

/**
 * Render VPN setup step
 */
function renderVpnStep(container) {
    container.innerHTML = `
        <div class="py-4">
            <div class="text-center mb-6">
                <div class="w-16 h-16 mx-auto mb-4 bg-green-500/20 rounded-full flex items-center justify-center">
                    ${icon('shield', 'w-8 h-8 text-green-400')}
                </div>
                <h2 class="text-xl font-bold mb-2">${t('wizard_vpn_title')}</h2>
                <p class="text-gray-400 text-sm">${t('wizard_vpn_desc')}</p>
            </div>

            <div class="bg-gray-700/50 rounded-lg p-4 mb-4">
                <label class="block mb-3 font-medium">${t('import_profile')}</label>
                <div class="space-y-3">
                    <input type="file" id="wizard-vpn-file" accept=".conf,.ovpn,.wg,.ini,.txt,.conf.txt,application/octet-stream"
                           class="block w-full bg-gray-600 rounded px-3 py-2 text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:bg-rose-600 file:text-white file:cursor-pointer truncate">
                    <button id="wizard-vpn-import" class="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm transition-smooth flex items-center justify-center gap-2">
                        ${icon('upload', 'icon-sm')} ${t('import_activate')}
                    </button>
                </div>
                <p id="wizard-vpn-status" class="mt-3 text-sm text-gray-400"></p>
            </div>

            <div class="bg-gray-700/30 rounded-lg p-3 mb-6">
                <p class="text-xs text-gray-400 flex items-center gap-2">
                    ${icon('info', 'icon-sm')} ${t('wizard_vpn_hint')}
                </p>
            </div>

            <div class="flex justify-between">
                <button onclick="window.prevStep()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-smooth flex items-center gap-2">
                    ${icon('arrow-left', 'icon-sm')} ${t('wizard_back')}
                </button>
                <button onclick="window.nextStep()" class="px-6 py-2 bg-rose-600 hover:bg-rose-700 rounded-lg font-medium transition-smooth flex items-center gap-2">
                    ${wizardData.vpn ? t('wizard_next') : t('wizard_skip_step')} ${icon('arrow-right', 'icon-sm')}
                </button>
            </div>
        </div>
    `;

    // Set up VPN import handler
    const importBtn = document.getElementById('wizard-vpn-import');
    if (importBtn) {
        importBtn.addEventListener('click', () => importVpnProfile());
    }
}

/**
 * Import VPN profile in wizard
 */
async function importVpnProfile() {
    const fileInput = document.getElementById('wizard-vpn-file');
    const statusEl = document.getElementById('wizard-vpn-status');
    const importBtn = document.getElementById('wizard-vpn-import');

    if (!fileInput?.files?.length) {
        showToast(t('wizard_select_file'), 'error');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    setButtonLoading(importBtn, true);

    try {
        const response = await fetch('/api/vpn/import', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            wizardData.vpn = { name: data.name || file.name.replace('.conf', ''), imported: true };
            statusEl.innerHTML = `<span class="text-green-400 flex items-center gap-1">${icon('check-circle', 'icon-sm')} ${t('upload_success')}: ${escapeHtml(wizardData.vpn.name)}</span>`;
            showToast(t('upload_success'), 'success');
            refreshIcons();
            renderCurrentStep(); // Re-render to update button text
        } else {
            // Try to parse as JSON, fall back to text if it fails
            const text = await response.text();
            let errorMsg = t('upload_failed');
            try {
                const data = JSON.parse(text);
                errorMsg = data.detail || errorMsg;
            } catch {
                errorMsg = text || `Error ${response.status}`;
            }
            statusEl.innerHTML = `<span class="text-red-400">${escapeHtml(errorMsg)}</span>`;
        }
    } catch {
        statusEl.innerHTML = `<span class="text-red-400">${t('error')}</span>`;
    } finally {
        setButtonLoading(importBtn, false);
    }
}

/**
 * Render Hotspot setup step
 */
function renderHotspotStep(container) {
    const countries = [
        { code: 'AT', name: 'Austria' },
        { code: 'AU', name: 'Australia' },
        { code: 'BE', name: 'Belgium' },
        { code: 'BR', name: 'Brazil' },
        { code: 'CA', name: 'Canada' },
        { code: 'CH', name: 'Switzerland' },
        { code: 'DE', name: 'Germany' },
        { code: 'DK', name: 'Denmark' },
        { code: 'ES', name: 'Spain' },
        { code: 'FI', name: 'Finland' },
        { code: 'FR', name: 'France' },
        { code: 'GB', name: 'United Kingdom' },
        { code: 'GR', name: 'Greece' },
        { code: 'IE', name: 'Ireland' },
        { code: 'IT', name: 'Italy' },
        { code: 'JP', name: 'Japan' },
        { code: 'LU', name: 'Luxembourg' },
        { code: 'MA', name: 'Morocco' },
        { code: 'MX', name: 'Mexico' },
        { code: 'NL', name: 'Netherlands' },
        { code: 'NO', name: 'Norway' },
        { code: 'NZ', name: 'New Zealand' },
        { code: 'PL', name: 'Poland' },
        { code: 'PT', name: 'Portugal' },
        { code: 'SE', name: 'Sweden' },
        { code: 'TN', name: 'Tunisia' },
        { code: 'TR', name: 'Turkey' },
        { code: 'US', name: 'United States' },
        { code: 'ZA', name: 'South Africa' }
    ];

    container.innerHTML = `
        <div class="py-4">
            <div class="text-center mb-6">
                <div class="w-16 h-16 mx-auto mb-4 bg-yellow-500/20 rounded-full flex items-center justify-center">
                    ${icon('radio', 'w-8 h-8 text-yellow-400')}
                </div>
                <h2 class="text-xl font-bold mb-2">${t('wizard_hotspot_title')}</h2>
                <p class="text-gray-400 text-sm">${t('wizard_hotspot_desc')}</p>
            </div>

            <div class="bg-gray-700/50 rounded-lg p-4 mb-4 space-y-4">
                <div>
                    <label class="block text-sm mb-1">${t('ssid_label')}</label>
                    <input type="text" id="wizard-hotspot-ssid" value="${escapeHtml(wizardData.hotspot.ssid)}"
                           class="w-full bg-gray-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-rose-500 outline-none"
                           placeholder="ROSE-Link" maxlength="32">
                </div>

                <div>
                    <label class="block text-sm mb-1">${t('password_label')}</label>
                    <input type="password" id="wizard-hotspot-password" value="${escapeHtml(wizardData.hotspot.password)}"
                           class="w-full bg-gray-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-rose-500 outline-none"
                           placeholder="********" minlength="8" maxlength="63">
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">${t('country_label')}</label>
                        <select id="wizard-hotspot-country" class="w-full bg-gray-600 rounded px-3 py-2 text-sm">
                            ${countries.map(c => `<option value="${c.code}" ${wizardData.hotspot.country === c.code ? 'selected' : ''}>${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">${t('band_label')}</label>
                        <select id="wizard-hotspot-band" class="w-full bg-gray-600 rounded px-3 py-2 text-sm">
                            <option value="2.4GHz" ${wizardData.hotspot.band === '2.4GHz' ? 'selected' : ''}>2.4 GHz</option>
                            <option value="5GHz" ${wizardData.hotspot.band === '5GHz' ? 'selected' : ''}>5 GHz</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="flex justify-between">
                <button onclick="window.prevStep()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-smooth flex items-center gap-2">
                    ${icon('arrow-left', 'icon-sm')} ${t('wizard_back')}
                </button>
                <button id="wizard-hotspot-save" class="px-6 py-2 bg-rose-600 hover:bg-rose-700 rounded-lg font-medium transition-smooth flex items-center gap-2">
                    ${t('wizard_next')} ${icon('arrow-right', 'icon-sm')}
                </button>
            </div>
        </div>
    `;

    // Set up save handler
    const saveBtn = document.getElementById('wizard-hotspot-save');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => saveHotspotConfig());
    }
}

/**
 * Save hotspot configuration in wizard
 */
async function saveHotspotConfig() {
    const ssid = document.getElementById('wizard-hotspot-ssid')?.value?.trim();
    const password = document.getElementById('wizard-hotspot-password')?.value;
    const country = document.getElementById('wizard-hotspot-country')?.value;
    const band = document.getElementById('wizard-hotspot-band')?.value;

    if (!ssid) {
        showToast(t('wizard_ssid_required'), 'error');
        return;
    }

    if (password && password.length < 8) {
        showToast(t('wizard_password_min'), 'error');
        return;
    }

    wizardData.hotspot = {
        ssid,
        password: password || '',
        country: country || 'US',
        band: band || '2.4GHz',
        channel: band === '5GHz' ? 36 : 6,
        wpa3: false
    };

    // Try to apply config
    const saveBtn = document.getElementById('wizard-hotspot-save');
    setButtonLoading(saveBtn, true);

    try {
        const response = await fetch('/api/hotspot/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(wizardData.hotspot)
        });

        if (response.ok) {
            showToast(t('config_applied'), 'success');
        }
        // Continue to next step even if it fails (backend might not be running)
        nextStep();
    } catch {
        // Continue anyway - backend might not be available
        nextStep();
    } finally {
        setButtonLoading(saveBtn, false);
    }
}

/**
 * Render completion step
 */
function renderCompleteStep(container) {
    const checkIcon = icon('check', 'icon-sm text-green-400');
    const skipIcon = icon('minus', 'icon-sm text-gray-500');

    container.innerHTML = `
        <div class="text-center py-6">
            <div class="w-20 h-20 mx-auto mb-6 bg-green-500/20 rounded-full flex items-center justify-center">
                ${icon('check-circle', 'w-10 h-10 text-green-400')}
            </div>
            <h2 class="text-2xl font-bold mb-4">${t('wizard_complete_title')}</h2>
            <p class="text-gray-400 mb-6">${t('wizard_complete_desc')}</p>

            <div class="bg-gray-700/50 rounded-lg p-4 mb-6 text-left max-w-sm mx-auto">
                <h3 class="font-semibold mb-3">${t('wizard_summary')}</h3>
                <ul class="space-y-2 text-sm">
                    <li class="flex items-center gap-2">
                        ${wizardData.wifi ? checkIcon : skipIcon}
                        <span class="${wizardData.wifi ? 'text-white' : 'text-gray-500'}">
                            WiFi: ${wizardData.wifi ? escapeHtml(wizardData.wifi.ssid) : t('wizard_not_configured')}
                        </span>
                    </li>
                    <li class="flex items-center gap-2">
                        ${wizardData.vpn ? checkIcon : skipIcon}
                        <span class="${wizardData.vpn ? 'text-white' : 'text-gray-500'}">
                            VPN: ${wizardData.vpn ? escapeHtml(wizardData.vpn.name) : t('wizard_not_configured')}
                        </span>
                    </li>
                    <li class="flex items-center gap-2">
                        ${wizardData.hotspot.ssid ? checkIcon : skipIcon}
                        <span class="text-white">
                            Hotspot: ${escapeHtml(wizardData.hotspot.ssid)}
                        </span>
                    </li>
                </ul>
            </div>

            <div class="flex justify-center gap-3">
                <button onclick="window.prevStep()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-smooth flex items-center gap-2">
                    ${icon('arrow-left', 'icon-sm')} ${t('wizard_back')}
                </button>
                <button onclick="window.completeWizard()" class="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-smooth flex items-center gap-2">
                    ${icon('check', 'icon-sm')} ${t('wizard_finish')}
                </button>
            </div>
        </div>
    `;
}

/**
 * Load device capabilities from system info API
 */
async function loadDeviceCapabilities() {
    if (deviceCapabilities.loaded) return;

    try {
        const response = await fetch('/api/system/info');
        if (response.ok) {
            const data = await response.json();
            deviceCapabilities.singleWifi = data.interfaces?.single_wifi || false;
            deviceCapabilities.loaded = true;
        }
    } catch {
        // Silently fail - assume dual WiFi if we can't fetch
        deviceCapabilities.loaded = true;
    }
}

/**
 * Check if device has single WiFi (no WiFi WAN available)
 * @returns {boolean}
 */
export function isSingleWifiDevice() {
    return deviceCapabilities.singleWifi;
}

/**
 * Initialize wizard - check if should show and set up event handlers
 */
export async function initWizard() {
    // Expose functions globally for onclick handlers
    window.nextStep = nextStep;
    window.prevStep = prevStep;
    window.skipWizard = skipWizard;
    window.completeWizard = completeWizard;
    window.resetWizard = resetWizard;
    window.showWizard = showWizard;

    // Set up close button handler
    const closeBtn = document.getElementById('wizard-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeWizardWithConfirm();
        });
    }

    // Load device capabilities
    await loadDeviceCapabilities();

    // Check if wizard should be shown
    if (shouldShowWizard()) {
        showWizard();
    }
}
