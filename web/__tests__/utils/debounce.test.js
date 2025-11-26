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
});
