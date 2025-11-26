/**
 * ROSE Link - API Utilities
 * Centralized API fetch helpers
 */

import { showToast } from './toast.js';

/**
 * Make an API request with error handling
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
export async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
    }

    return response.json();
}

/**
 * POST request helper
 * @param {string} url - API endpoint
 * @param {Object} data - Request body
 * @returns {Promise<any>} Response data
 */
export async function post(url, data) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE request helper
 * @param {string} url - API endpoint
 * @returns {Promise<any>} Response data
 */
export async function del(url) {
    return apiRequest(url, { method: 'DELETE' });
}

/**
 * GET request helper
 * @param {string} url - API endpoint
 * @returns {Promise<any>} Response data
 */
export async function get(url) {
    return apiRequest(url, { method: 'GET' });
}
