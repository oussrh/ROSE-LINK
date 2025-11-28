/**
 * Tests for WebSocket Utilities
 */

// Mock toast before importing
jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

import wsManager, { initWebSocket, getWebSocket, isConnected, sendMessage } from '../../js/utils/websocket.js';
import { showToast } from '../../js/utils/toast.js';

// Mock WebSocket
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = WebSocket.CONNECTING;
        this.onopen = null;
        this.onclose = null;
        this.onerror = null;
        this.onmessage = null;
        this.sentMessages = [];
        MockWebSocket.instances.push(this);
    }

    send(data) {
        this.sentMessages.push(data);
    }

    close(code, reason) {
        this.readyState = WebSocket.CLOSED;
        if (this.onclose) {
            this.onclose({ code, reason, wasClean: true });
        }
    }

    // Helper to simulate connection
    simulateOpen() {
        this.readyState = WebSocket.OPEN;
        if (this.onopen) {
            this.onopen({});
        }
    }

    // Helper to simulate message
    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }

    // Helper to simulate error
    simulateError(error) {
        if (this.onerror) {
            this.onerror({ error });
        }
    }

    // Helper to simulate close
    simulateClose(code = 1000, reason = '', wasClean = true) {
        this.readyState = WebSocket.CLOSED;
        if (this.onclose) {
            this.onclose({ code, reason, wasClean });
        }
    }
}

MockWebSocket.CONNECTING = 0;
MockWebSocket.OPEN = 1;
MockWebSocket.CLOSING = 2;
MockWebSocket.CLOSED = 3;
MockWebSocket.instances = [];

// Set up global WebSocket mock
global.WebSocket = MockWebSocket;

describe('WebSocket Utilities', () => {
    beforeEach(() => {
        MockWebSocket.instances = [];
        jest.clearAllMocks();
        jest.useFakeTimers();

        // Reset wsManager state
        wsManager.socket = null;
        wsManager.isConnected = false;
        wsManager.wasConnected = false;
        wsManager.reconnectAttempts = 0;
        wsManager.listeners.clear();
    });

    afterEach(() => {
        jest.useRealTimers();
        if (wsManager.socket) {
            wsManager.disconnect();
        }
    });

    describe('WebSocketManager.getWebSocketUrl', () => {
        it('should return ws:// URL for http:// page', () => {
            Object.defineProperty(window, 'location', {
                value: { protocol: 'http:', host: 'localhost:8000' },
                writable: true
            });

            const url = wsManager.getWebSocketUrl();

            expect(url).toBe('ws://localhost:8000/api/ws');
        });

        it('should return wss:// URL for https:// page', () => {
            Object.defineProperty(window, 'location', {
                value: { protocol: 'https:', host: 'example.com' },
                writable: true
            });

            const url = wsManager.getWebSocketUrl();

            expect(url).toBe('wss://example.com/api/ws');
        });
    });

    describe('WebSocketManager.connect', () => {
        it('should create WebSocket connection', () => {
            wsManager.connect();

            expect(MockWebSocket.instances.length).toBe(1);
            expect(wsManager.socket).toBe(MockWebSocket.instances[0]);
        });

        it('should not create new connection if already connected', () => {
            wsManager.connect();
            MockWebSocket.instances[0].readyState = WebSocket.OPEN;

            wsManager.connect();

            expect(MockWebSocket.instances.length).toBe(1);
        });

        it('should set up event handlers', () => {
            wsManager.connect();

            const socket = MockWebSocket.instances[0];
            expect(socket.onopen).toBeTruthy();
            expect(socket.onclose).toBeTruthy();
            expect(socket.onerror).toBeTruthy();
            expect(socket.onmessage).toBeTruthy();
        });
    });

    describe('WebSocketManager event handlers', () => {
        it('should set isConnected to true on open', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];

            socket.simulateOpen();

            expect(wsManager.isConnected).toBe(true);
        });

        it('should reset reconnect attempts on successful connection', () => {
            wsManager.reconnectAttempts = 3;
            wsManager.connect();
            const socket = MockWebSocket.instances[0];

            socket.simulateOpen();

            expect(wsManager.reconnectAttempts).toBe(0);
        });

        it('should show toast on reconnection', () => {
            wsManager.wasConnected = true;
            wsManager.connect();
            const socket = MockWebSocket.instances[0];

            socket.simulateOpen();

            expect(showToast).toHaveBeenCalledWith('Connection restored', 'success');
        });

        it('should not show toast on first connection', () => {
            wsManager.wasConnected = false;
            wsManager.connect();
            const socket = MockWebSocket.instances[0];

            socket.simulateOpen();

            expect(showToast).not.toHaveBeenCalled();
        });

        it('should emit connected event on open', () => {
            const callback = jest.fn();
            wsManager.on('connected', callback);
            wsManager.connect();
            const socket = MockWebSocket.instances[0];

            socket.simulateOpen();

            expect(callback).toHaveBeenCalled();
        });

        it('should set isConnected to false on close', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateClose();

            expect(wsManager.isConnected).toBe(false);
        });

        it('should emit disconnected event on close', () => {
            const callback = jest.fn();
            wsManager.on('disconnected', callback);
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateClose(1000, 'Normal');

            expect(callback).toHaveBeenCalledWith({ code: 1000, reason: 'Normal' }, null);
        });

        it('should emit error event on error', () => {
            const callback = jest.fn();
            wsManager.on('error', callback);
            wsManager.connect();
            const socket = MockWebSocket.instances[0];

            socket.simulateError(new Error('Test error'));

            expect(callback).toHaveBeenCalled();
        });

        it('should parse and handle incoming messages', () => {
            const callback = jest.fn();
            wsManager.on('status', callback);
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateMessage({ type: 'status', data: { wan: true }, timestamp: '2024-01-01' });

            expect(callback).toHaveBeenCalledWith({ wan: true }, '2024-01-01');
        });

        it('should emit message event for all messages', () => {
            const callback = jest.fn();
            wsManager.on('message', callback);
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateMessage({ type: 'status', data: {} });

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('WebSocketManager.scheduleReconnect', () => {
        it('should schedule reconnection with exponential backoff', () => {
            wsManager.wasConnected = true;
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateClose(1006, 'Abnormal', false);

            // First reconnect should be scheduled
            expect(wsManager.reconnectAttempts).toBe(1);

            // Fast-forward timer
            jest.advanceTimersByTime(1000);

            // Should have created another socket
            expect(MockWebSocket.instances.length).toBe(2);
        });

        it('should stop reconnecting after max attempts', () => {
            wsManager.maxReconnectAttempts = 2;
            wsManager.reconnectAttempts = 2;

            wsManager.scheduleReconnect();

            expect(showToast).toHaveBeenCalledWith(
                'Connection lost. Please refresh the page.',
                'error'
            );
        });

        it('should increase delay with each attempt', () => {
            wsManager.reconnectDelay = 1000;

            // First attempt: 1000ms
            wsManager.scheduleReconnect();
            expect(wsManager.reconnectAttempts).toBe(1);

            // Second attempt would be 2000ms
            wsManager.scheduleReconnect();
            expect(wsManager.reconnectAttempts).toBe(2);
        });
    });

    describe('WebSocketManager.send', () => {
        it('should return false when not connected', () => {
            const result = wsManager.send({ test: 'data' });

            expect(result).toBe(false);
        });

        it('should send JSON stringified data when connected', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            const result = wsManager.send({ action: 'test' });

            expect(result).toBe(true);
            expect(socket.sentMessages[0]).toBe('{"action":"test"}');
        });
    });

    describe('WebSocketManager.ping', () => {
        it('should send ping action', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            wsManager.ping();

            expect(socket.sentMessages[0]).toBe('{"action":"ping"}');
        });
    });

    describe('WebSocketManager.requestStatus', () => {
        it('should send get_status action', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            wsManager.requestStatus();

            expect(socket.sentMessages[0]).toBe('{"action":"get_status"}');
        });
    });

    describe('WebSocketManager.requestBandwidth', () => {
        it('should send get_bandwidth action', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            wsManager.requestBandwidth();

            expect(socket.sentMessages[0]).toBe('{"action":"get_bandwidth"}');
        });
    });

    describe('WebSocketManager.on/off/emit', () => {
        it('should add event listeners', () => {
            const callback = jest.fn();

            wsManager.on('test', callback);
            wsManager.emit('test', { data: 'value' });

            expect(callback).toHaveBeenCalledWith({ data: 'value' }, null);
        });

        it('should remove event listeners', () => {
            const callback = jest.fn();
            wsManager.on('test', callback);

            wsManager.off('test', callback);
            wsManager.emit('test', {});

            expect(callback).not.toHaveBeenCalled();
        });

        it('should support multiple listeners for same event', () => {
            const callback1 = jest.fn();
            const callback2 = jest.fn();

            wsManager.on('test', callback1);
            wsManager.on('test', callback2);
            wsManager.emit('test', {});

            expect(callback1).toHaveBeenCalled();
            expect(callback2).toHaveBeenCalled();
        });

        it('should handle errors in listeners gracefully', () => {
            const errorCallback = jest.fn(() => { throw new Error('Test'); });
            const normalCallback = jest.fn();

            // Mock console.error to prevent test output noise
            const originalError = console.error;
            console.error = jest.fn();

            wsManager.on('test', errorCallback);
            wsManager.on('test', normalCallback);

            expect(() => wsManager.emit('test', {})).not.toThrow();
            expect(normalCallback).toHaveBeenCalled();
            expect(console.error).toHaveBeenCalledWith(
                expect.stringContaining('Error in test listener:'),
                expect.any(Error)
            );

            // Restore console.error
            console.error = originalError;
        });
    });

    describe('WebSocketManager.disconnect', () => {
        it('should close socket and reset state', () => {
            wsManager.connect();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            wsManager.disconnect();

            expect(wsManager.socket).toBeNull();
            expect(wsManager.isConnected).toBe(false);
        });
    });

    describe('initWebSocket', () => {
        it('should connect and return manager', () => {
            const result = initWebSocket();

            expect(MockWebSocket.instances.length).toBe(1);
            expect(result).toBe(wsManager);
        });

        it('should set up status event handler', () => {
            const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateMessage({ type: 'status', data: { wan: true } });

            expect(dispatchEventSpy).toHaveBeenCalledWith(
                expect.objectContaining({ type: 'rose:status' })
            );
        });

        it('should set up bandwidth event handler', () => {
            const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            socket.simulateMessage({ type: 'bandwidth', data: { rx: 100 } });

            expect(dispatchEventSpy).toHaveBeenCalledWith(
                expect.objectContaining({ type: 'rose:bandwidth' })
            );
        });

        it('should request status on connection', () => {
            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            // Fast-forward the setTimeout
            jest.advanceTimersByTime(100);

            expect(socket.sentMessages).toContainEqual('{"action":"get_status"}');
            expect(socket.sentMessages).toContainEqual('{"action":"get_bandwidth"}');
        });
    });

    describe('getWebSocket', () => {
        it('should return the websocket manager', () => {
            expect(getWebSocket()).toBe(wsManager);
        });
    });

    describe('isConnected', () => {
        it('should return connection status', () => {
            expect(isConnected()).toBe(false);

            wsManager.connect();
            MockWebSocket.instances[0].simulateOpen();

            expect(isConnected()).toBe(true);
        });
    });

    describe('sendMessage', () => {
        it('should send message via manager', () => {
            wsManager.connect();
            MockWebSocket.instances[0].simulateOpen();

            const result = sendMessage({ test: true });

            expect(result).toBe(true);
        });

        it('should return false when not connected', () => {
            const result = sendMessage({ test: true });

            expect(result).toBe(false);
        });
    });

    describe('status badge updates', () => {
        beforeEach(() => {
            // Set up status badge DOM
            document.body.innerHTML = `
                <div id="status-badge">
                    <div class="indicator"></div>
                    <span>Online</span>
                </div>
            `;
        });

        it('should update status badge to online when connected', () => {
            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            const badge = document.getElementById('status-badge');
            const indicator = badge.querySelector('div');
            const text = badge.querySelector('span');

            expect(indicator.className).toContain('bg-green-500');
            expect(text.getAttribute('data-i18n')).toBe('online');
        });

        it('should update status badge to offline when disconnected', () => {
            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();
            socket.simulateClose(1006, 'Connection lost', false);

            const badge = document.getElementById('status-badge');
            const indicator = badge.querySelector('div');
            const text = badge.querySelector('span');

            expect(indicator.className).toContain('bg-red-500');
            expect(text.getAttribute('data-i18n')).toBe('offline');
        });

        it('should handle missing status badge gracefully', () => {
            document.body.innerHTML = '';

            expect(() => {
                initWebSocket();
                MockWebSocket.instances[0].simulateOpen();
            }).not.toThrow();
        });

        it('should use window.t if available for translations', () => {
            window.t = jest.fn(key => key === 'online' ? 'En ligne' : 'Hors ligne');

            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            const text = document.querySelector('#status-badge span');
            expect(text.textContent).toBe('En ligne');

            delete window.t;
        });

        it('should use fallback text if window.t is not available', () => {
            delete window.t;

            initWebSocket();
            const socket = MockWebSocket.instances[0];
            socket.simulateOpen();

            const text = document.querySelector('#status-badge span');
            expect(text.textContent).toBe('Online');
        });

        it('should handle missing indicator element', () => {
            document.body.innerHTML = `
                <div id="status-badge">
                    <span>Online</span>
                </div>
            `;

            expect(() => {
                initWebSocket();
                MockWebSocket.instances[0].simulateOpen();
            }).not.toThrow();
        });

        it('should handle missing text element', () => {
            document.body.innerHTML = `
                <div id="status-badge">
                    <div class="indicator"></div>
                </div>
            `;

            expect(() => {
                initWebSocket();
                MockWebSocket.instances[0].simulateOpen();
            }).not.toThrow();
        });
    });
});
