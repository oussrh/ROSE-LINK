/**
 * ROSE Link - Debounce Utility
 * Provides debouncing and throttling for performance optimization
 */

/**
 * Creates a debounced version of a function that delays execution
 * until after wait milliseconds have elapsed since the last call.
 *
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait before executing
 * @param {boolean} immediate - Execute on leading edge instead of trailing
 * @returns {Function} Debounced function with cancel() method
 *
 * @example
 * const debouncedSearch = debounce((query) => {
 *     fetch(`/api/search?q=${query}`);
 * }, 300);
 *
 * input.addEventListener('input', (e) => debouncedSearch(e.target.value));
 */
export function debounce(func, wait, immediate = false) {
    let timeout = null;
    let lastArgs = null;
    let lastThis = null;

    function debounced(...args) {
        lastArgs = args;
        lastThis = this;

        const callNow = immediate && !timeout;

        if (timeout) {
            clearTimeout(timeout);
        }

        timeout = setTimeout(() => {
            timeout = null;
            if (!immediate && lastArgs) {
                func.apply(lastThis, lastArgs);
            }
        }, wait);

        if (callNow) {
            func.apply(this, args);
        }
    }

    // Allow cancelling pending execution
    debounced.cancel = function() {
        if (timeout) {
            clearTimeout(timeout);
            timeout = null;
        }
        lastArgs = null;
        lastThis = null;
    };

    // Check if there's a pending execution
    debounced.pending = function() {
        return timeout !== null;
    };

    // Force immediate execution
    debounced.flush = function() {
        if (timeout && lastArgs) {
            clearTimeout(timeout);
            timeout = null;
            func.apply(lastThis, lastArgs);
            lastArgs = null;
            lastThis = null;
        }
    };

    return debounced;
}

/**
 * Creates a throttled version of a function that only executes
 * at most once per wait milliseconds.
 *
 * @param {Function} func - Function to throttle
 * @param {number} wait - Minimum milliseconds between executions
 * @param {Object} options - Options for leading/trailing edge execution
 * @param {boolean} options.leading - Execute on leading edge (default: true)
 * @param {boolean} options.trailing - Execute on trailing edge (default: true)
 * @returns {Function} Throttled function with cancel() method
 *
 * @example
 * const throttledScroll = throttle(() => {
 *     updateScrollPosition();
 * }, 100);
 *
 * window.addEventListener('scroll', throttledScroll);
 */
export function throttle(func, wait, { leading = true, trailing = true } = {}) {
    let timeout = null;
    let lastArgs = null;
    let lastThis = null;
    let lastCallTime = 0;
    let hasLeadingCall = false;

    function throttled(...args) {
        const now = Date.now();

        // On first call, if leading is false, set lastCallTime to now to skip leading invocation
        if (!hasLeadingCall && !leading) {
            lastCallTime = now;
        }
        hasLeadingCall = true;

        const remaining = wait - (now - lastCallTime);

        lastArgs = args;
        lastThis = this;

        if (remaining <= 0 || remaining > wait) {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
            lastCallTime = now;
            func.apply(this, args);
        } else if (!timeout && trailing) {
            timeout = setTimeout(() => {
                lastCallTime = leading ? Date.now() : 0;
                hasLeadingCall = leading;
                timeout = null;
                func.apply(lastThis, lastArgs);
            }, remaining);
        }
    }

    throttled.cancel = function() {
        if (timeout) {
            clearTimeout(timeout);
            timeout = null;
        }
        lastCallTime = 0;
        hasLeadingCall = false;
        lastArgs = null;
        lastThis = null;
    };

    return throttled;
}

/**
 * Creates a debounced API request function that prevents duplicate requests.
 * Automatically cancels pending requests when a new one is made.
 *
 * @param {Function} requestFn - Async function that makes the API request
 * @param {number} wait - Milliseconds to wait before executing (default: 300)
 * @returns {Function} Debounced request function
 *
 * @example
 * const debouncedFetch = debouncedRequest(async (url) => {
 *     const response = await fetch(url);
 *     return response.json();
 * }, 300);
 *
 * // Only the last call within 300ms will execute
 * debouncedFetch('/api/data?page=1');
 * debouncedFetch('/api/data?page=2');
 * debouncedFetch('/api/data?page=3'); // Only this executes
 */
export function debouncedRequest(requestFn, wait = 300) {
    let abortController = null;

    const debouncedFn = debounce(async (...args) => {
        // Cancel any pending request
        if (abortController) {
            abortController.abort();
        }

        // Create new abort controller
        abortController = new AbortController();

        try {
            const result = await requestFn(...args, abortController.signal);
            return result;
        } catch (error) {
            if (error.name === 'AbortError') {
                // Request was cancelled, ignore
                return null;
            }
            throw error;
        } finally {
            abortController = null;
        }
    }, wait);

    // Add method to cancel pending request
    debouncedFn.abort = function() {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
        debouncedFn.cancel();
    };

    return debouncedFn;
}

/**
 * Debounce for form submissions - prevents double submissions
 *
 * @param {Function} submitFn - Form submission handler
 * @param {number} wait - Cooldown period in milliseconds (default: 1000)
 * @returns {Function} Protected submit handler
 *
 * @example
 * form.addEventListener('submit', debouncedSubmit(async (e) => {
 *     e.preventDefault();
 *     await submitForm();
 * }));
 */
export function debouncedSubmit(submitFn, wait = 1000) {
    let isSubmitting = false;

    return async function(...args) {
        if (isSubmitting) {
            return;
        }

        isSubmitting = true;

        try {
            await submitFn.apply(this, args);
        } finally {
            setTimeout(() => {
                isSubmitting = false;
            }, wait);
        }
    };
}
