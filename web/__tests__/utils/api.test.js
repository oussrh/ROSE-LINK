/**
 * Tests for API Utilities
 */

// Mock the toast module before importing api
jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

import { apiRequest, post, del, get } from '../../js/utils/api.js';

describe('API Utilities', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    describe('apiRequest', () => {
        it('should make a successful request', async () => {
            const mockData = { status: 'ok' };
            fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockData)
            });

            const result = await apiRequest('/api/health');

            expect(fetch).toHaveBeenCalledWith('/api/health', {
                headers: { 'Content-Type': 'application/json' }
            });
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

            expect(fetch).toHaveBeenCalledWith('/api/test', {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer token'
                }
            });
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

            expect(fetch).toHaveBeenCalledWith('/api/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'value' })
            });
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

            expect(fetch).toHaveBeenCalledWith('/api/resource/123', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
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

            expect(fetch).toHaveBeenCalledWith('/api/items', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            expect(result).toEqual(mockData);
        });
    });
});
