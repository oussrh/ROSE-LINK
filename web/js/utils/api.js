/**
 * ROSE Link - API Utilities
 * Centralized API fetch helpers with timeout, error handling, and retry support
 */

import { showToast } from './toast.js';
import { setButtonLoading } from './dom.js';
import { showConfirm } from './modal.js';

/**
 * Default request timeout in milliseconds
 * @type {number}
 */
const DEFAULT_TIMEOUT = 30000;

/**
 * API Error class for structured error handling
 */
export class ApiError extends Error {
    /**
     * @param {string} message - Error message
     * @param {number} status - HTTP status code
     * @param {string} [detail] - Detailed error message from server
     */
    constructor(message, status, detail = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.detail = detail;
    }
}

/**
 * Create an AbortController with timeout
 * @param {number} timeout - Timeout in milliseconds
 * @returns {{ controller: AbortController, timeoutId: number }}
 */
function createTimeoutController(timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        controller.abort();
    }, timeout);
    return { controller, timeoutId };
}

/**
 * Make an API request with error handling and timeout
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @param {number} [options.timeout] - Request timeout in ms (default: 30000)
 * @returns {Promise<any>} Response data
 * @throws {ApiError} On request failure
 */
export async function apiRequest(url, options = {}) {
    const { timeout = DEFAULT_TIMEOUT, headers: customHeaders, ...fetchOptions } = options;
    const { controller, timeoutId } = createTimeoutController(timeout);

    try {
        const response = await fetch(url, {
            ...fetchOptions,
            headers: {
                'Content-Type': 'application/json',
                ...customHeaders
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new ApiError(
                errorData.detail || `Request failed: ${response.status}`,
                response.status,
                errorData.detail
            );
        }

        return response.json();
    } catch (error) {
        clearTimeout(timeoutId);

        if (error.name === 'AbortError') {
            throw new ApiError('Request timeout - server did not respond', 408, 'timeout');
        }

        if (error instanceof ApiError) {
            throw error;
        }

        // Network error or other failure
        throw new ApiError(
            error.message || 'Network error',
            0,
            'network_error'
        );
    }
}

/**
 * POST request helper
 * @param {string} url - API endpoint
 * @param {Object} data - Request body
 * @param {Object} [options] - Additional options
 * @returns {Promise<any>} Response data
 */
export async function post(url, data, options = {}) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data),
        ...options
    });
}

/**
 * DELETE request helper
 * @param {string} url - API endpoint
 * @param {Object} [options] - Additional options
 * @returns {Promise<any>} Response data
 */
export async function del(url, options = {}) {
    return apiRequest(url, { method: 'DELETE', ...options });
}

/**
 * GET request helper
 * @param {string} url - API endpoint
 * @param {Object} [options] - Additional options
 * @returns {Promise<any>} Response data
 */
export async function get(url, options = {}) {
    return apiRequest(url, { method: 'GET', ...options });
}

/**
 * Execute an API action with standardized loading, success, and error handling
 *
 * This function extracts the common pattern of:
 * 1. Setting button loading state
 * 2. Making API request
 * 3. Showing success toast
 * 4. Triggering htmx refresh
 * 5. Handling errors with toast
 * 6. Restoring button state
 *
 * @param {Object} config - Action configuration
 * @param {string} config.url - API endpoint URL
 * @param {string} [config.method='POST'] - HTTP method
 * @param {Object} [config.data] - Request body data
 * @param {HTMLElement} [config.button] - Button element for loading state
 * @param {string} [config.successMessage] - Success toast message
 * @param {string} [config.errorMessage] - Fallback error message
 * @param {string|string[]} [config.refreshSelectors] - CSS selectors to trigger htmx refresh
 * @param {Function} [config.onSuccess] - Custom success handler
 * @param {Function} [config.onError] - Custom error handler
 * @param {number} [config.timeout] - Request timeout in ms
 * @returns {Promise<any>} Response data or undefined on error
 *
 * @example
 * // Basic usage
 * await apiAction({
 *     url: '/api/vpn/activate',
 *     data: { name: profileName },
 *     button: btn,
 *     successMessage: 'VPN activated',
 *     errorMessage: 'Activation failed',
 *     refreshSelectors: ['#vpn-profiles', '#vpn-status-detail']
 * });
 *
 * @example
 * // With custom handlers
 * await apiAction({
 *     url: '/api/wifi/connect',
 *     data: { ssid, password },
 *     button: btn,
 *     onSuccess: (data) => {
 *         showToast(`Connected to ${data.ssid}`, 'success');
 *         updateUI(data);
 *     },
 *     onError: (error) => {
 *         if (error.status === 401) {
 *             redirectToLogin();
 *         }
 *     }
 * });
 */
export async function apiAction(config) {
    const {
        url,
        method = 'POST',
        data,
        button,
        successMessage,
        errorMessage = 'An error occurred',
        refreshSelectors,
        onSuccess,
        onError,
        timeout = DEFAULT_TIMEOUT
    } = config;

    // Set loading state
    if (button) {
        setButtonLoading(button, true);
    }

    try {
        const options = { method, timeout };
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }

        const response = await apiRequest(url, options);

        // Handle success
        if (onSuccess) {
            onSuccess(response);
        } else if (successMessage) {
            showToast(successMessage, 'success');
        }

        // Trigger htmx refresh
        if (refreshSelectors && typeof htmx !== 'undefined') {
            const selectors = Array.isArray(refreshSelectors) ? refreshSelectors : [refreshSelectors];
            selectors.forEach(selector => {
                const element = document.querySelector(selector);
                if (element) {
                    htmx.trigger(element, 'htmx:load');
                }
            });
        }

        return response;
    } catch (error) {
        // Handle error
        if (onError) {
            onError(error);
        } else {
            const msg = error.detail || error.message || errorMessage;
            showToast(msg, 'error');
        }

        return undefined;
    } finally {
        // Reset loading state
        if (button) {
            setButtonLoading(button, false);
        }
    }
}

/**
 * Execute an API action with confirmation dialog
 *
 * @param {string} confirmMessage - Confirmation message to display
 * @param {Object} config - Same as apiAction config
 * @param {Object} [modalOptions] - Optional modal customization
 * @param {string} [modalOptions.title] - Modal title
 * @param {string} [modalOptions.confirmText] - Confirm button text
 * @param {string} [modalOptions.variant] - Button variant: 'default', 'danger'
 * @param {string} [modalOptions.icon] - Lucide icon name
 * @returns {Promise<any>} Response data, undefined on error, or false if cancelled
 */
export async function apiActionWithConfirm(confirmMessage, config, modalOptions = {}) {
    const confirmed = await showConfirm({
        title: modalOptions.title || 'Confirm Action',
        message: confirmMessage,
        confirmText: modalOptions.confirmText || 'Confirm',
        cancelText: modalOptions.cancelText || 'Cancel',
        variant: modalOptions.variant || 'default',
        icon: modalOptions.icon || 'alert-circle'
    });

    if (!confirmed) {
        return false;
    }
    return apiAction(config);
}
