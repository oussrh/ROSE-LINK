/**
 * Tests for API Utilities
 */

// Mock the toast module before importing api
jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

// Mock the dom module
jest.mock('../../js/utils/dom.js', () => ({
    setButtonLoading: jest.fn()
}));

import { apiRequest, post, del, get, apiAction, apiActionWithConfirm, ApiError } from '../../js/utils/api.js';
import { showToast } from '../../js/utils/toast.js';
import { setButtonLoading } from '../../js/utils/dom.js';

describe('API Utilities', () => {
    beforeEach(() => {
        fetch.mockClear();
        jest.clearAllMocks();
        global.confirm = jest.fn();
    });

    describe('apiRequest', () => {
        it('should make a successful request', async () => {
            const mockData = { status: 'ok' };
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockData)
            });

            const result = await apiRequest('/api/health');

            expect(fetch).toHaveBeenCalledWith('/api/health', expect.objectContaining({
                headers: { 'Content-Type': 'application/json' }
            }));
            expect(result).toEqual(mockData);
        });

        it('should include custom headers', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await apiRequest('/api/test', {
                headers: { 'Authorization': 'Bearer token' }
            });

            expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer token'
                }
            }));
        });

        it('should throw error on failed request with detail', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: () => Promise.resolve({ detail: 'Invalid request' })
            });

            await expect(apiRequest('/api/fail')).rejects.toThrow('Invalid request');
        });

        it('should throw generic error on failed request without detail', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: () => Promise.reject()
            });

            await expect(apiRequest('/api/fail')).rejects.toThrow('Request failed: 500');
        });
    });

    describe('post', () => {
        it('should make a POST request with JSON body', async () => {
            const mockData = { success: true };
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockData)
            });

            const result = await post('/api/action', { key: 'value' });

            expect(fetch).toHaveBeenCalledWith('/api/action', expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'value' })
            }));
            expect(result).toEqual(mockData);
        });
    });

    describe('del', () => {
        it('should make a DELETE request', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ deleted: true })
            });

            const result = await del('/api/resource/123');

            expect(fetch).toHaveBeenCalledWith('/api/resource/123', expect.objectContaining({
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            }));
            expect(result).toEqual({ deleted: true });
        });
    });

    describe('get', () => {
        it('should make a GET request', async () => {
            const mockData = { items: [] };
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockData)
            });

            const result = await get('/api/items');

            expect(fetch).toHaveBeenCalledWith('/api/items', expect.objectContaining({
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }));
            expect(result).toEqual(mockData);
        });
    });

    describe('ApiError', () => {
        it('should create error with message, status, and detail', () => {
            const error = new ApiError('Test error', 400, 'Detailed info');

            expect(error.message).toBe('Test error');
            expect(error.status).toBe(400);
            expect(error.detail).toBe('Detailed info');
            expect(error.name).toBe('ApiError');
        });

        it('should create error without detail', () => {
            const error = new ApiError('Test error', 500);

            expect(error.message).toBe('Test error');
            expect(error.status).toBe(500);
            expect(error.detail).toBeNull();
        });
    });

    describe('apiRequest error handling', () => {
        it('should handle network errors', async () => {
            fetch.mockRejectedValueOnce(new Error('Network failure'));

            await expect(apiRequest('/api/fail')).rejects.toThrow('Network failure');
        });

        it('should rethrow ApiError as-is', async () => {
            const apiError = new ApiError('Custom API error', 422, 'validation_error');
            fetch.mockRejectedValueOnce(apiError);

            await expect(apiRequest('/api/fail')).rejects.toThrow('Custom API error');
        });

        it('should handle error without message', async () => {
            const error = new Error();
            fetch.mockRejectedValueOnce(error);

            await expect(apiRequest('/api/fail')).rejects.toThrow('Network error');
        });
    });

    describe('apiAction', () => {
        it('should set button loading state', async () => {
            const button = document.createElement('button');
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });

            await apiAction({
                url: '/api/test',
                button
            });

            expect(setButtonLoading).toHaveBeenCalledWith(button, true);
            expect(setButtonLoading).toHaveBeenCalledWith(button, false);
        });

        it('should show success toast on successful request', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });

            await apiAction({
                url: '/api/test',
                successMessage: 'Operation completed'
            });

            expect(showToast).toHaveBeenCalledWith('Operation completed', 'success');
        });

        it('should call onSuccess handler when provided', async () => {
            const onSuccess = jest.fn();
            const responseData = { id: 123 };
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(responseData)
            });

            await apiAction({
                url: '/api/test',
                onSuccess
            });

            expect(onSuccess).toHaveBeenCalledWith(responseData);
            expect(showToast).not.toHaveBeenCalled();
        });

        it('should show error toast on failed request', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: () => Promise.resolve({ detail: 'Validation error' })
            });

            await apiAction({
                url: '/api/test',
                errorMessage: 'Default error'
            });

            expect(showToast).toHaveBeenCalledWith('Validation error', 'error');
        });

        it('should use fallback error message when no detail', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: () => Promise.reject()
            });

            await apiAction({
                url: '/api/test',
                errorMessage: 'Something went wrong'
            });

            expect(showToast).toHaveBeenCalledWith(expect.stringContaining('500'), 'error');
        });

        it('should call onError handler when provided', async () => {
            const onError = jest.fn();
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                json: () => Promise.resolve({ detail: 'Not found' })
            });

            await apiAction({
                url: '/api/test',
                onError
            });

            expect(onError).toHaveBeenCalled();
            expect(showToast).not.toHaveBeenCalled();
        });

        it('should trigger htmx refresh on success', async () => {
            document.body.innerHTML = '<div id="test-container"></div>';
            global.htmx = { trigger: jest.fn() };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await apiAction({
                url: '/api/test',
                refreshSelectors: '#test-container'
            });

            expect(global.htmx.trigger).toHaveBeenCalled();
            delete global.htmx;
        });

        it('should handle array of refresh selectors', async () => {
            document.body.innerHTML = '<div id="container1"></div><div id="container2"></div>';
            global.htmx = { trigger: jest.fn() };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await apiAction({
                url: '/api/test',
                refreshSelectors: ['#container1', '#container2']
            });

            expect(global.htmx.trigger).toHaveBeenCalledTimes(2);
            delete global.htmx;
        });

        it('should include body for POST requests with data', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await apiAction({
                url: '/api/test',
                method: 'POST',
                data: { key: 'value' }
            });

            expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ key: 'value' })
            }));
        });

        it('should not include body for GET requests', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await apiAction({
                url: '/api/test',
                method: 'GET',
                data: { key: 'value' }
            });

            expect(fetch).toHaveBeenCalledWith('/api/test', expect.not.objectContaining({
                body: expect.anything()
            }));
        });

        it('should return response on success', async () => {
            const responseData = { id: 1, name: 'Test' };
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(responseData)
            });

            const result = await apiAction({ url: '/api/test' });

            expect(result).toEqual(responseData);
        });

        it('should return undefined on error', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: () => Promise.resolve({ detail: 'Error' })
            });

            const result = await apiAction({ url: '/api/test' });

            expect(result).toBeUndefined();
        });

        it('should work without button', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await expect(apiAction({ url: '/api/test' })).resolves.not.toThrow();
            expect(setButtonLoading).not.toHaveBeenCalled();
        });

        it('should reset button loading even on error', async () => {
            const button = document.createElement('button');
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: () => Promise.resolve({ detail: 'Error' })
            });

            await apiAction({
                url: '/api/test',
                button
            });

            expect(setButtonLoading).toHaveBeenLastCalledWith(button, false);
        });
    });

    describe('apiActionWithConfirm', () => {
        it('should show confirmation dialog', async () => {
            global.confirm.mockReturnValue(true);
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            await apiActionWithConfirm('Are you sure?', { url: '/api/test' });

            expect(global.confirm).toHaveBeenCalledWith('Are you sure?');
        });

        it('should proceed with action when confirmed', async () => {
            global.confirm.mockReturnValue(true);
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });

            const result = await apiActionWithConfirm('Confirm?', {
                url: '/api/delete',
                method: 'DELETE'
            });

            expect(fetch).toHaveBeenCalled();
            expect(result).toEqual({ success: true });
        });

        it('should return false when cancelled', async () => {
            global.confirm.mockReturnValue(false);

            const result = await apiActionWithConfirm('Confirm?', { url: '/api/test' });

            expect(fetch).not.toHaveBeenCalled();
            expect(result).toBe(false);
        });

        it('should not show toast when cancelled', async () => {
            global.confirm.mockReturnValue(false);

            await apiActionWithConfirm('Confirm?', {
                url: '/api/test',
                successMessage: 'Done'
            });

            expect(showToast).not.toHaveBeenCalled();
        });
    });
});
