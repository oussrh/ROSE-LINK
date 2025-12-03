/**
 * Tests for Debounce Utility
 */

import { debounce, throttle, debouncedRequest, debouncedSubmit } from '../../js/utils/debounce.js';

describe('Debounce Utility', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    describe('debounce', () => {
        it('should delay function execution', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            debouncedFn();
            expect(func).not.toHaveBeenCalled();

            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should only call function once for rapid calls', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            debouncedFn();
            debouncedFn();
            debouncedFn();

            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should pass the latest arguments', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            debouncedFn('first');
            debouncedFn('second');
            debouncedFn('third');

            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledWith('third');
        });

        it('should call immediately when immediate is true', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100, true);

            debouncedFn();
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should not call again during wait period when immediate', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100, true);

            debouncedFn();
            debouncedFn();
            debouncedFn();

            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should have cancel method', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            debouncedFn();
            debouncedFn.cancel();

            jest.advanceTimersByTime(100);
            expect(func).not.toHaveBeenCalled();
        });

        it('should have pending method', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            expect(debouncedFn.pending()).toBe(false);

            debouncedFn();
            expect(debouncedFn.pending()).toBe(true);

            jest.advanceTimersByTime(100);
            expect(debouncedFn.pending()).toBe(false);
        });

        it('should have flush method', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            debouncedFn('test');
            debouncedFn.flush();

            expect(func).toHaveBeenCalledWith('test');
        });

        it('should preserve this context', () => {
            const obj = {
                value: 42,
                getValue: jest.fn(function() {
                    return this.value;
                })
            };
            obj.debouncedGetValue = debounce(obj.getValue, 100);

            obj.debouncedGetValue();
            jest.advanceTimersByTime(100);

            expect(obj.getValue).toHaveBeenCalled();
        });
    });

    describe('throttle', () => {
        it('should call function immediately by default', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            throttledFn();
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should not call again within wait period', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            throttledFn();
            throttledFn();
            throttledFn();

            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should call again after wait period', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            throttledFn();
            jest.advanceTimersByTime(100);
            throttledFn();

            expect(func).toHaveBeenCalledTimes(2);
        });

        it('should call trailing by default', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            throttledFn('first');
            throttledFn('second');

            expect(func).toHaveBeenCalledTimes(1);

            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('second');
        });

        it('should not call trailing when trailing is false', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { trailing: false });

            throttledFn('first');
            throttledFn('second');

            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledTimes(1);
            expect(func).toHaveBeenCalledWith('first');
        });

        it('should not call leading when leading is false', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { leading: false });

            throttledFn();
            expect(func).not.toHaveBeenCalled();

            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should have cancel method', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            throttledFn();
            throttledFn.cancel();

            jest.advanceTimersByTime(100);
            // Only initial call should have happened
            expect(func).toHaveBeenCalledTimes(1);
        });
    });

    describe('debouncedSubmit', () => {
        it('should call function immediately', async () => {
            const func = jest.fn().mockResolvedValue('done');
            const protectedFn = debouncedSubmit(func, 1000);

            await protectedFn();
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should prevent double submissions', async () => {
            const func = jest.fn().mockResolvedValue('done');
            const protectedFn = debouncedSubmit(func, 1000);

            const promise1 = protectedFn();
            protectedFn(); // Should be ignored

            await promise1;
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should allow submission after cooldown', async () => {
            const func = jest.fn().mockResolvedValue('done');
            const protectedFn = debouncedSubmit(func, 100);

            await protectedFn();
            jest.advanceTimersByTime(100);
            await protectedFn();

            expect(func).toHaveBeenCalledTimes(2);
        });

        it('should handle async functions', async () => {
            const func = jest.fn().mockImplementation(() => {
                return new Promise(resolve => {
                    setTimeout(() => resolve('done'), 50);
                });
            });
            const protectedFn = debouncedSubmit(func, 100);

            const promise = protectedFn();
            jest.advanceTimersByTime(50);
            await promise;

            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should pass arguments to function', async () => {
            const func = jest.fn().mockResolvedValue('done');
            const protectedFn = debouncedSubmit(func, 100);

            await protectedFn('arg1', 'arg2');
            expect(func).toHaveBeenCalledWith('arg1', 'arg2');
        });

        it('should handle errors and still reset isSubmitting', async () => {
            const func = jest.fn().mockRejectedValue(new Error('Submit failed'));
            const protectedFn = debouncedSubmit(func, 100);

            await expect(protectedFn()).rejects.toThrow('Submit failed');

            // After cooldown, should be able to submit again
            jest.advanceTimersByTime(100);
            func.mockResolvedValue('done');
            await protectedFn();
            expect(func).toHaveBeenCalledTimes(2);
        });
    });

    describe('debouncedRequest', () => {
        it('should debounce API requests', async () => {
            const requestFn = jest.fn().mockResolvedValue({ data: 'test' });
            const debouncedFn = debouncedRequest(requestFn, 100);

            debouncedFn('arg1');
            debouncedFn('arg2');
            debouncedFn('arg3');

            expect(requestFn).not.toHaveBeenCalled();

            jest.advanceTimersByTime(100);
            await Promise.resolve(); // Allow async to complete

            expect(requestFn).toHaveBeenCalledTimes(1);
        });

        it('should pass arguments to request function', async () => {
            const requestFn = jest.fn().mockResolvedValue({ data: 'result' });
            const debouncedFn = debouncedRequest(requestFn, 100);

            debouncedFn('url', { headers: {} });
            jest.advanceTimersByTime(100);
            await Promise.resolve();

            expect(requestFn).toHaveBeenCalledWith('url', { headers: {} }, expect.any(AbortSignal));
        });

        it('should have abort method', () => {
            const requestFn = jest.fn().mockResolvedValue({});
            const debouncedFn = debouncedRequest(requestFn, 100);

            expect(typeof debouncedFn.abort).toBe('function');
        });

        it('should cancel pending requests when abort is called', () => {
            const requestFn = jest.fn().mockResolvedValue({});
            const debouncedFn = debouncedRequest(requestFn, 100);

            debouncedFn('test');
            debouncedFn.abort();

            jest.advanceTimersByTime(100);
            expect(requestFn).not.toHaveBeenCalled();
        });

        it('should use default wait time of 300ms', () => {
            const requestFn = jest.fn().mockResolvedValue({});
            const debouncedFn = debouncedRequest(requestFn);

            debouncedFn();
            jest.advanceTimersByTime(299);
            expect(requestFn).not.toHaveBeenCalled();

            jest.advanceTimersByTime(1);
            expect(requestFn).toHaveBeenCalled();
        });
    });

    describe('throttle additional edge cases', () => {
        it('should handle both leading and trailing false', () => {
            const func = jest.fn();
            // Both false would mean nothing executes - this is an edge case
            const throttledFn = throttle(func, 100, { leading: false, trailing: false });

            throttledFn();
            expect(func).not.toHaveBeenCalled();

            jest.advanceTimersByTime(100);
            expect(func).not.toHaveBeenCalled();
        });

        it('should cancel pending trailing call', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            throttledFn('first');
            throttledFn('second'); // This schedules trailing

            throttledFn.cancel();
            jest.advanceTimersByTime(100);

            expect(func).toHaveBeenCalledTimes(1);
            expect(func).toHaveBeenCalledWith('first');
        });
    });

    describe('debounce edge cases', () => {
        it('should not flush when no pending call', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            // Call flush without any pending debounce
            debouncedFn.flush();

            expect(func).not.toHaveBeenCalled();
        });

        it('should handle cancel when no pending call', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            // Should not throw
            expect(() => debouncedFn.cancel()).not.toThrow();
        });

        it('should reset after flush', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100);

            debouncedFn('first');
            debouncedFn.flush();

            expect(debouncedFn.pending()).toBe(false);
        });
    });

    describe('throttle remaining time edge cases', () => {
        it('should clear existing timeout when remaining time becomes non-positive', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { leading: true, trailing: true });

            // First call - leads
            throttledFn('first');
            expect(func).toHaveBeenCalledTimes(1);

            // Advance time past the wait period
            jest.advanceTimersByTime(101);

            // Call again - should trigger immediately because remaining is negative
            throttledFn('second');
            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('second');
        });

        it('should handle rapid calls within wait period with trailing', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { leading: true, trailing: true });

            throttledFn('first');
            throttledFn('second');
            throttledFn('third');

            expect(func).toHaveBeenCalledTimes(1);

            jest.advanceTimersByTime(100);

            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('third');
        });

        it('should execute immediately when time has passed beyond wait', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { leading: true, trailing: true });

            // First call - immediate execution
            throttledFn('first');
            expect(func).toHaveBeenCalledTimes(1);

            // Wait well past the throttle period
            jest.advanceTimersByTime(200);

            // Call again - should execute immediately since enough time passed
            throttledFn('second');
            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('second');
        });
    });

    describe('debouncedRequest abort and error handling', () => {
        it('should handle abort() when no controller exists', () => {
            const requestFn = jest.fn().mockResolvedValue({});
            const debouncedFn = debouncedRequest(requestFn, 100);

            // Calling abort without any pending request should not throw
            expect(() => debouncedFn.abort()).not.toThrow();
        });

        it('should call abort on controller when abort() is called during request', () => {
            const requestFn = jest.fn().mockImplementation((arg, signal) => {
                // Simulate a long-running request
                return new Promise(resolve => {
                    const timer = setTimeout(() => resolve({ data: arg }), 1000);
                    signal.addEventListener('abort', () => {
                        clearTimeout(timer);
                    });
                });
            });

            const debouncedFn = debouncedRequest(requestFn, 50);

            debouncedFn('test');
            jest.advanceTimersByTime(50);

            // Now abort
            debouncedFn.abort();

            // Request was initiated
            expect(requestFn).toHaveBeenCalled();
        });

        it('should handle AbortError by returning null', async () => {
            const abortError = new Error('Aborted');
            abortError.name = 'AbortError';

            const requestFn = jest.fn().mockRejectedValue(abortError);
            const debouncedFn = debouncedRequest(requestFn, 50);

            debouncedFn('test');
            jest.advanceTimersByTime(50);

            // Wait for async to complete
            await Promise.resolve();
            await Promise.resolve();

            // Should not throw, request function was called but abortError handled
            expect(requestFn).toHaveBeenCalled();
        });

        it('should cancel previous abort controller when making new request', async () => {
            let abortCount = 0;
            const requestFn = jest.fn().mockImplementation((arg, signal) => {
                return new Promise((resolve, reject) => {
                    const timer = setTimeout(() => resolve({ data: arg }), 500);
                    signal.addEventListener('abort', () => {
                        clearTimeout(timer);
                        abortCount++;
                        const err = new Error('Aborted');
                        err.name = 'AbortError';
                        reject(err);
                    });
                });
            });

            const debouncedFn = debouncedRequest(requestFn, 50);

            // First request
            debouncedFn('first');
            jest.advanceTimersByTime(50);
            await Promise.resolve();

            // Second request should cancel the first
            debouncedFn('second');
            jest.advanceTimersByTime(50);
            await Promise.resolve();

            expect(abortCount).toBe(1);
        });
    });

    describe('throttle edge cases for timeout handling', () => {
        it('should clear existing timeout when calling at exactly remaining time', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { leading: true, trailing: true });

            // First call
            throttledFn('first');
            expect(func).toHaveBeenCalledTimes(1);

            // Second call schedules trailing
            throttledFn('second');
            expect(func).toHaveBeenCalledTimes(1);

            // Third call while trailing is still pending - existing timeout should be cleared
            throttledFn('third');
            expect(func).toHaveBeenCalledTimes(1);

            // Advance to trigger trailing
            jest.advanceTimersByTime(100);
            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('third');
        });

        it('should handle remaining > wait edge case (time travel)', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100);

            // Mock Date.now to simulate time going backwards
            const originalNow = Date.now;
            let mockTime = 1000;
            Date.now = jest.fn(() => mockTime);

            throttledFn('first');
            expect(func).toHaveBeenCalledTimes(1);

            // Simulate time going way forward
            mockTime = 2000; // remaining = 100 - (2000 - 1000) = -900 (negative, so immediate)

            throttledFn('second');
            expect(func).toHaveBeenCalledTimes(2);

            Date.now = originalNow;
        });

        it('should clear pending timeout when remaining becomes non-positive', () => {
            const func = jest.fn();
            const throttledFn = throttle(func, 100, { leading: true, trailing: true });

            const originalNow = Date.now;
            let mockTime = 1000;
            Date.now = jest.fn(() => mockTime);

            // First call with leading
            throttledFn('first');
            expect(func).toHaveBeenCalledTimes(1);

            // Second call schedules trailing
            mockTime = 1050;
            throttledFn('second');
            expect(func).toHaveBeenCalledTimes(1);

            // Jump time past the wait period - should clear existing timeout and execute immediately
            mockTime = 1200;
            throttledFn('third');
            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('third');

            Date.now = originalNow;
        });
    });

    describe('debounce immediate mode edge cases', () => {
        it('should not call on trailing edge when immediate is true', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100, true);

            debouncedFn('first');
            expect(func).toHaveBeenCalledTimes(1);
            expect(func).toHaveBeenCalledWith('first');

            // Advance time
            jest.advanceTimersByTime(100);

            // Should not have called again
            expect(func).toHaveBeenCalledTimes(1);
        });

        it('should allow re-call after timeout expires in immediate mode', () => {
            const func = jest.fn();
            const debouncedFn = debounce(func, 100, true);

            debouncedFn('first');
            expect(func).toHaveBeenCalledTimes(1);

            // Advance past timeout
            jest.advanceTimersByTime(100);

            // New call should execute immediately
            debouncedFn('second');
            expect(func).toHaveBeenCalledTimes(2);
            expect(func).toHaveBeenLastCalledWith('second');
        });
    });

    describe('debouncedSubmit edge cases', () => {
        it('should preserve this context', async () => {
            const obj = {
                value: 42,
                submit: jest.fn(async function() {
                    return this.value;
                })
            };

            obj.protectedSubmit = debouncedSubmit(obj.submit, 100);

            await obj.protectedSubmit.call(obj);

            expect(obj.submit).toHaveBeenCalled();
        });
    });
});
