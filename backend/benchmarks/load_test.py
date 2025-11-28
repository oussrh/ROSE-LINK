#!/usr/bin/env python3
"""
ROSE Link - API Load Testing

Tests the FastAPI backend under load to validate performance
on Raspberry Pi hardware.

Usage:
    python -m benchmarks.load_test --url http://localhost:8000 --duration 60
    python -m benchmarks.load_test --url http://localhost:8000 --concurrent 50

Requires: pip install httpx
"""

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class RequestResult:
    """Result of a single HTTP request."""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class LoadTestSummary:
    """Summary of load test results."""
    base_url: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate_percent: float


# API endpoints to test with their expected methods
ENDPOINTS = [
    ("GET", "/api/health"),
    ("GET", "/api/status"),
    ("GET", "/api/vpn/status"),
    ("GET", "/api/hotspot/clients"),
    ("GET", "/api/system/info"),
    ("GET", "/api/vpn/profiles"),
]


async def make_request(
    client,  # httpx.AsyncClient
    base_url: str,
    method: str,
    endpoint: str,
) -> RequestResult:
    """Make a single HTTP request and measure response time."""
    url = f"{base_url}{endpoint}"
    start_time = time.perf_counter()
    error = None
    status_code = 0
    success = False

    try:
        if method == "GET":
            response = await client.get(url, timeout=10.0)
        elif method == "POST":
            response = await client.post(url, timeout=10.0)
        else:
            raise ValueError(f"Unsupported method: {method}")

        status_code = response.status_code
        success = 200 <= status_code < 400
    except Exception as e:
        error = str(e)
        success = False

    end_time = time.perf_counter()
    response_time_ms = (end_time - start_time) * 1000

    return RequestResult(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=round(response_time_ms, 2),
        success=success,
        error=error,
    )


async def run_load_test(
    base_url: str,
    duration_seconds: float = 60.0,
    concurrent_requests: int = 10,
    endpoints: Optional[list[tuple[str, str]]] = None,
) -> LoadTestSummary:
    """
    Run load test against the API.

    Args:
        base_url: Base URL of the API (e.g., http://localhost:8000)
        duration_seconds: How long to run the test
        concurrent_requests: Number of concurrent requests
        endpoints: List of (method, endpoint) tuples to test

    Returns:
        LoadTestSummary with test results
    """
    # Import httpx here to make it optional
    try:
        import httpx
    except ImportError:
        raise ImportError(
            "httpx is required for load testing. "
            "Install with: pip install httpx"
        )

    if endpoints is None:
        endpoints = ENDPOINTS

    results: list[RequestResult] = []
    start_time = time.monotonic()
    end_time = start_time + duration_seconds

    print(f"Starting load test against {base_url}")
    print(f"Duration: {duration_seconds}s, Concurrent: {concurrent_requests}")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        request_count = 0
        while time.monotonic() < end_time:
            # Create batch of concurrent requests
            tasks = []
            for _ in range(concurrent_requests):
                # Round-robin through endpoints
                method, endpoint = endpoints[request_count % len(endpoints)]
                tasks.append(make_request(client, base_url, method, endpoint))
                request_count += 1

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, RequestResult):
                    results.append(result)
                else:
                    # Handle exceptions
                    results.append(RequestResult(
                        endpoint="unknown",
                        method="unknown",
                        status_code=0,
                        response_time_ms=0,
                        success=False,
                        error=str(result),
                    ))

            # Progress indicator
            elapsed = time.monotonic() - start_time
            print(f"\rProgress: {elapsed:.1f}s / {duration_seconds}s "
                  f"({len(results)} requests)", end="", flush=True)

    print("\n")

    # Calculate statistics
    actual_duration = time.monotonic() - start_time
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
    response_times.sort()

    def percentile(data: list[float], p: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f])

    return LoadTestSummary(
        base_url=base_url,
        duration_seconds=round(actual_duration, 2),
        total_requests=len(results),
        successful_requests=len(successful),
        failed_requests=len(failed),
        requests_per_second=round(len(results) / actual_duration, 2),
        avg_response_time_ms=round(statistics.mean(response_times), 2) if response_times else 0,
        min_response_time_ms=round(min(response_times), 2) if response_times else 0,
        max_response_time_ms=round(max(response_times), 2) if response_times else 0,
        p50_response_time_ms=round(percentile(response_times, 50), 2),
        p95_response_time_ms=round(percentile(response_times, 95), 2),
        p99_response_time_ms=round(percentile(response_times, 99), 2),
        error_rate_percent=round((len(failed) / len(results)) * 100, 2) if results else 0,
    )


def print_summary(summary: LoadTestSummary) -> None:
    """Print load test summary to console."""
    print("=" * 60)
    print("ROSE Link API Load Test Results")
    print("=" * 60)
    print(f"Target: {summary.base_url}")
    print(f"Duration: {summary.duration_seconds}s")
    print("-" * 60)
    print("\nRequest Statistics:")
    print(f"  Total Requests: {summary.total_requests}")
    print(f"  Successful: {summary.successful_requests}")
    print(f"  Failed: {summary.failed_requests}")
    print(f"  Error Rate: {summary.error_rate_percent}%")
    print(f"  Requests/Second: {summary.requests_per_second}")
    print("\nResponse Time Statistics:")
    print(f"  Average: {summary.avg_response_time_ms} ms")
    print(f"  Minimum: {summary.min_response_time_ms} ms")
    print(f"  Maximum: {summary.max_response_time_ms} ms")
    print(f"  P50 (Median): {summary.p50_response_time_ms} ms")
    print(f"  P95: {summary.p95_response_time_ms} ms")
    print(f"  P99: {summary.p99_response_time_ms} ms")
    print("=" * 60)

    # Performance assessment
    print("\nPerformance Assessment:")
    if summary.error_rate_percent < 1:
        print("  [PASS] Error rate below 1%")
    else:
        print(f"  [WARN] Error rate at {summary.error_rate_percent}%")

    if summary.p95_response_time_ms < 500:
        print("  [PASS] P95 response time under 500ms")
    elif summary.p95_response_time_ms < 1000:
        print(f"  [WARN] P95 response time at {summary.p95_response_time_ms}ms")
    else:
        print(f"  [FAIL] P95 response time too high: {summary.p95_response_time_ms}ms")

    if summary.requests_per_second > 50:
        print(f"  [PASS] Throughput at {summary.requests_per_second} req/s")
    else:
        print(f"  [WARN] Low throughput: {summary.requests_per_second} req/s")


async def run_stress_test(
    base_url: str,
    max_concurrent: int = 200,
    step: int = 20,
    step_duration: float = 10.0,
) -> list[LoadTestSummary]:
    """
    Run progressive stress test to find breaking point.

    Gradually increases concurrent requests until performance degrades.
    """
    results = []
    print("Starting stress test - finding performance limits")
    print("=" * 60)

    for concurrent in range(step, max_concurrent + 1, step):
        print(f"\nTesting with {concurrent} concurrent connections...")
        summary = await run_load_test(
            base_url=base_url,
            duration_seconds=step_duration,
            concurrent_requests=concurrent,
        )
        results.append(summary)
        print_summary(summary)

        # Stop if error rate exceeds 10% or p95 exceeds 2 seconds
        if summary.error_rate_percent > 10 or summary.p95_response_time_ms > 2000:
            print(f"\nBreaking point reached at {concurrent} concurrent connections")
            break

    return results


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="ROSE Link API Load Testing Tool"
    )
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=60.0,
        help="Test duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--concurrent", "-c",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)"
    )
    parser.add_argument(
        "--stress",
        action="store_true",
        help="Run stress test with progressive load"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path for JSON results"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout"
    )

    args = parser.parse_args()

    if args.stress:
        results = asyncio.run(run_stress_test(args.url))
        summaries = [asdict(r) for r in results]
    else:
        summary = asyncio.run(run_load_test(
            base_url=args.url,
            duration_seconds=args.duration,
            concurrent_requests=args.concurrent,
        ))
        summaries = [asdict(summary)]
        if not args.json:
            print_summary(summary)

    if args.json:
        print(json.dumps(summaries, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "results": summaries,
            }, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
