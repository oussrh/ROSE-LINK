/**
 * ROSE Link - WebSocket Utilities
 * Real-time communication with the backend via WebSocket
 */

import { showToast } from './toast.js';

/**
 * WebSocket connection manager
 * Handles connection, reconnection, and message handling
 */
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = new Map();
        this.isConnected = false;
        this.wasConnected = false;
    }

    /**
     * Get WebSocket URL based on current location
     * @returns {string} WebSocket URL
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/api/ws`;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;
        }

        const url = this.getWebSocketUrl();

        try {
            this.socket = new WebSocket(url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;

            if (this.wasConnected) {
                showToast('Connection restored', 'success');
            }
            this.wasConnected = true;

            this.emit('connected', {});
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.emit('disconnected', { code: event.code, reason: event.reason });

            if (!event.wasClean && this.wasConnected) {
                this.scheduleReconnect();
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', { error });
        };

        this.socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
    }

    /**
     * Handle incoming WebSocket messages
     * @param {Object} message - Parsed message object
     */
    handleMessage(message) {
        const { type, data, timestamp } = message;

        // Emit to type-specific listeners
        this.emit(type, data, timestamp);

        // Emit to 'message' listeners for all messages
        this.emit('message', message);
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            showToast('Connection lost. Please refresh the page.', 'error');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Send a message to the server
     * @param {Object} data - Data to send
     * @returns {boolean} True if sent successfully
     */
    send(data) {
        if (!this.isConnected || !this.socket) {
            console.warn('Cannot send: WebSocket not connected');
            return false;
        }

        try {
            this.socket.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
            return false;
        }
    }

    /**
     * Send a ping to check connection
     */
    ping() {
        return this.send({ action: 'ping' });
    }

    /**
     * Request current status from server
     */
    requestStatus() {
        return this.send({ action: 'get_status' });
    }

    /**
     * Request bandwidth statistics from server
     */
    requestBandwidth() {
        return this.send({ action: 'get_bandwidth' });
    }

    /**
     * Add event listener
     * @param {string} event - Event type
     * @param {Function} callback - Callback function
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event).add(callback);
    }

    /**
     * Remove event listener
     * @param {string} event - Event type
     * @param {Function} callback - Callback function
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).delete(callback);
        }
    }

    /**
     * Emit event to all listeners
     * @param {string} event - Event type
     * @param {*} data - Event data
     * @param {string} timestamp - Optional timestamp
     */
    emit(event, data, timestamp = null) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data, timestamp);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Client disconnect');
            this.socket = null;
        }
        this.isConnected = false;
    }
}

// Create singleton instance
const wsManager = new WebSocketManager();

/**
 * Update the status badge in the header
 * @param {boolean} online - Whether the connection is online
 */
function updateStatusBadge(online) {
    const badge = document.getElementById('status-badge');
    if (!badge) return;

    const indicator = badge.querySelector('div');
    const text = badge.querySelector('span');

    if (online) {
        if (indicator) {
            indicator.className = 'w-2 h-2 sm:w-3 sm:h-3 bg-green-500 rounded-full pulse-slow';
        }
        if (text) {
            text.setAttribute('data-i18n', 'online');
            text.textContent = window.t ? window.t('online') : 'Online';
        }
    } else {
        if (indicator) {
            indicator.className = 'w-2 h-2 sm:w-3 sm:h-3 bg-red-500 rounded-full';
        }
        if (text) {
            text.setAttribute('data-i18n', 'offline');
            text.textContent = window.t ? window.t('offline') : 'Offline';
        }
    }
}

/**
 * Initialize WebSocket connection
 * Call this from main.js during app initialization
 */
export function initWebSocket() {
    // Connect to WebSocket server
    wsManager.connect();

    // Set up status update handler
    wsManager.on('status', (data) => {
        // Dispatch custom event for components to listen to
        window.dispatchEvent(new CustomEvent('rose:status', { detail: data }));
    });

    // Set up bandwidth update handler
    wsManager.on('bandwidth', (data) => {
        window.dispatchEvent(new CustomEvent('rose:bandwidth', { detail: data }));
    });

    // Set up pong handler
    wsManager.on('pong', () => {
        console.log('Pong received');
    });

    // Handle connection events
    wsManager.on('connected', () => {
        updateStatusBadge(true);
        // Request initial status
        setTimeout(() => {
            wsManager.requestStatus();
            wsManager.requestBandwidth();
        }, 100);
    });

    // Handle disconnection events
    wsManager.on('disconnected', () => {
        updateStatusBadge(false);
    });

    return wsManager;
}

/**
 * Get the WebSocket manager instance
 * @returns {WebSocketManager} WebSocket manager
 */
export function getWebSocket() {
    return wsManager;
}

/**
 * Check if WebSocket is connected
 * @returns {boolean} Connection status
 */
export function isConnected() {
    return wsManager.isConnected;
}

/**
 * Send message via WebSocket
 * @param {Object} data - Data to send
 * @returns {boolean} Success status
 */
export function sendMessage(data) {
    return wsManager.send(data);
}

export default wsManager;
