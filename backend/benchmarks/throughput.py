#!/usr/bin/env python3
"""
ROSE Link - Network Throughput Benchmark

Measures network throughput performance to validate VPN and hotspot
capabilities on various Raspberry Pi hardware configurations.

Usage:
    python -m benchmarks.throughput --interface wg0 --duration 10
    python -m benchmarks.throughput --all
"""

import argparse
import asyncio
import json
import os
import socket
import statistics
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ThroughputResult:
    """Result of a throughput benchmark run."""
    interface: str
    timestamp: str
    duration_seconds: float
    bytes_sent: int
    bytes_received: int
    throughput_mbps_tx: float
    throughput_mbps_rx: float
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    latency_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    hardware: Optional[str] = None


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results."""
    hardware_model: str
    kernel_version: str
    total_memory_mb: int
    test_date: str
    results: list[ThroughputResult]
    avg_throughput_mbps: float
    max_throughput_mbps: float
    min_throughput_mbps: float


def get_hardware_info() -> dict:
    """Get Raspberry Pi hardware information."""
    info = {
        "model": "Unknown",
        "kernel": "Unknown",
        "memory_mb": 0,
    }

    # Get Pi model
    try:
        with open("/proc/device-tree/model", "r") as f:
            info["model"] = f.read().strip().replace("\x00", "")
    except (FileNotFoundError, PermissionError):
        pass

    # Get kernel version
    try:
        info["kernel"] = subprocess.check_output(
            ["uname", "-r"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        pass

    # Get memory
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    info["memory_mb"] = kb // 1024
                    break
    except (FileNotFoundError, PermissionError):
        pass

    return info


def get_interface_stats(interface: str) -> dict:
    """Get network interface statistics."""
    stats_path = Path(f"/sys/class/net/{interface}/statistics")
    stats = {}

    for stat in ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets",
                 "rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]:
        try:
            with open(stats_path / stat, "r") as f:
                stats[stat] = int(f.read().strip())
        except (FileNotFoundError, PermissionError, ValueError):
            stats[stat] = 0

    return stats


def measure_latency(host: str = "8.8.8.8", count: int = 10) -> tuple[float, float]:
    """
    Measure network latency and jitter using ping.

    Returns:
        tuple: (average_latency_ms, jitter_ms)
    """
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-q", host],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # Parse ping output for rtt stats
            for line in result.stdout.split("\n"):
                if "rtt min/avg/max/mdev" in line:
                    # Format: rtt min/avg/max/mdev = 1.234/5.678/9.012/1.234 ms
                    parts = line.split("=")[1].strip().split("/")
                    avg_latency = float(parts[1])
                    jitter = float(parts[3].split()[0])  # mdev is jitter
                    return avg_latency, jitter
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        pass

    return 0.0, 0.0


async def run_iperf_benchmark(
    server: str,
    port: int = 5201,
    duration: int = 10,
    reverse: bool = False
) -> Optional[dict]:
    """
    Run iperf3 benchmark against a server.

    Args:
        server: iperf3 server address
        port: Server port
        duration: Test duration in seconds
        reverse: Test download instead of upload

    Returns:
        dict with iperf3 results or None if failed
    """
    cmd = [
        "iperf3",
        "-c", server,
        "-p", str(port),
        "-t", str(duration),
        "-J",  # JSON output
    ]
    if reverse:
        cmd.append("-R")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    return None


def measure_interface_throughput(
    interface: str,
    duration: float = 10.0
) -> ThroughputResult:
    """
    Measure throughput on a network interface by monitoring stats.

    Args:
        interface: Network interface name (e.g., wg0, wlan0)
        duration: Measurement duration in seconds

    Returns:
        ThroughputResult with measured statistics
    """
    # Get initial stats
    start_stats = get_interface_stats(interface)
    start_time = time.monotonic()

    # Wait for measurement period
    time.sleep(duration)

    # Get final stats
    end_stats = get_interface_stats(interface)
    end_time = time.monotonic()

    actual_duration = end_time - start_time

    # Calculate deltas
    bytes_sent = end_stats["tx_bytes"] - start_stats["tx_bytes"]
    bytes_received = end_stats["rx_bytes"] - start_stats["rx_bytes"]
    packets_sent = end_stats["tx_packets"] - start_stats["tx_packets"]
    packets_received = end_stats["rx_packets"] - start_stats["rx_packets"]
    packets_dropped = (
        (end_stats["rx_dropped"] - start_stats["rx_dropped"]) +
        (end_stats["tx_dropped"] - start_stats["tx_dropped"])
    )
    total_packets = packets_sent + packets_received

    # Calculate throughput in Mbps
    throughput_tx = (bytes_sent * 8) / (actual_duration * 1_000_000)
    throughput_rx = (bytes_received * 8) / (actual_duration * 1_000_000)

    # Calculate packet loss
    packet_loss = 0.0
    if total_packets > 0:
        packet_loss = (packets_dropped / total_packets) * 100

    # Get latency if this is a VPN interface
    latency, jitter = 0.0, 0.0
    if interface.startswith("wg") or interface.startswith("tun"):
        latency, jitter = measure_latency()

    hw_info = get_hardware_info()

    return ThroughputResult(
        interface=interface,
        timestamp=datetime.now().isoformat(),
        duration_seconds=actual_duration,
        bytes_sent=bytes_sent,
        bytes_received=bytes_received,
        throughput_mbps_tx=round(throughput_tx, 2),
        throughput_mbps_rx=round(throughput_rx, 2),
        packets_sent=packets_sent,
        packets_received=packets_received,
        packet_loss_percent=round(packet_loss, 4),
        latency_ms=latency if latency > 0 else None,
        jitter_ms=jitter if jitter > 0 else None,
        hardware=hw_info["model"],
    )


def get_active_interfaces() -> list[str]:
    """Get list of active network interfaces."""
    interfaces = []
    net_path = Path("/sys/class/net")

    for iface in net_path.iterdir():
        if iface.name == "lo":
            continue
        operstate_path = iface / "operstate"
        try:
            with open(operstate_path, "r") as f:
                if f.read().strip() == "up":
                    interfaces.append(iface.name)
        except (FileNotFoundError, PermissionError):
            pass

    return interfaces


def run_all_benchmarks(
    duration: float = 10.0,
    iterations: int = 3
) -> BenchmarkSummary:
    """
    Run benchmarks on all active interfaces.

    Args:
        duration: Duration per interface test in seconds
        iterations: Number of test iterations per interface

    Returns:
        BenchmarkSummary with all results
    """
    hw_info = get_hardware_info()
    results: list[ThroughputResult] = []

    interfaces = get_active_interfaces()
    print(f"Found active interfaces: {interfaces}")

    for interface in interfaces:
        print(f"\nBenchmarking {interface}...")
        for i in range(iterations):
            print(f"  Iteration {i + 1}/{iterations}...")
            result = measure_interface_throughput(interface, duration)
            results.append(result)

    # Calculate summary statistics
    all_throughputs = [
        max(r.throughput_mbps_tx, r.throughput_mbps_rx)
        for r in results
    ]

    return BenchmarkSummary(
        hardware_model=hw_info["model"],
        kernel_version=hw_info["kernel"],
        total_memory_mb=hw_info["memory_mb"],
        test_date=datetime.now().isoformat(),
        results=results,
        avg_throughput_mbps=round(statistics.mean(all_throughputs), 2) if all_throughputs else 0.0,
        max_throughput_mbps=round(max(all_throughputs), 2) if all_throughputs else 0.0,
        min_throughput_mbps=round(min(all_throughputs), 2) if all_throughputs else 0.0,
    )


def save_results(summary: BenchmarkSummary, output_path: Optional[str] = None) -> str:
    """Save benchmark results to JSON file."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"benchmark_results_{timestamp}.json"

    output = {
        "hardware": summary.hardware_model,
        "kernel": summary.kernel_version,
        "memory_mb": summary.total_memory_mb,
        "test_date": summary.test_date,
        "summary": {
            "avg_throughput_mbps": summary.avg_throughput_mbps,
            "max_throughput_mbps": summary.max_throughput_mbps,
            "min_throughput_mbps": summary.min_throughput_mbps,
        },
        "results": [asdict(r) for r in summary.results],
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    return output_path


def print_results(summary: BenchmarkSummary) -> None:
    """Print benchmark results to console."""
    print("\n" + "=" * 60)
    print("ROSE Link Performance Benchmark Results")
    print("=" * 60)
    print(f"Hardware: {summary.hardware_model}")
    print(f"Kernel: {summary.kernel_version}")
    print(f"Memory: {summary.total_memory_mb} MB")
    print(f"Test Date: {summary.test_date}")
    print("-" * 60)
    print("\nSummary:")
    print(f"  Average Throughput: {summary.avg_throughput_mbps} Mbps")
    print(f"  Maximum Throughput: {summary.max_throughput_mbps} Mbps")
    print(f"  Minimum Throughput: {summary.min_throughput_mbps} Mbps")
    print("\nDetailed Results:")

    for result in summary.results:
        print(f"\n  Interface: {result.interface}")
        print(f"    TX: {result.throughput_mbps_tx} Mbps")
        print(f"    RX: {result.throughput_mbps_rx} Mbps")
        print(f"    Packet Loss: {result.packet_loss_percent}%")
        if result.latency_ms:
            print(f"    Latency: {result.latency_ms} ms")
        if result.jitter_ms:
            print(f"    Jitter: {result.jitter_ms} ms")

    print("\n" + "=" * 60)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="ROSE Link Network Throughput Benchmark"
    )
    parser.add_argument(
        "--interface", "-i",
        help="Specific interface to benchmark"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Benchmark all active interfaces"
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=10.0,
        help="Test duration in seconds (default: 10)"
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=3,
        help="Number of test iterations (default: 3)"
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

    if args.interface:
        # Benchmark single interface
        results = []
        for i in range(args.iterations):
            result = measure_interface_throughput(args.interface, args.duration)
            results.append(result)

        hw_info = get_hardware_info()
        all_throughputs = [
            max(r.throughput_mbps_tx, r.throughput_mbps_rx)
            for r in results
        ]

        summary = BenchmarkSummary(
            hardware_model=hw_info["model"],
            kernel_version=hw_info["kernel"],
            total_memory_mb=hw_info["memory_mb"],
            test_date=datetime.now().isoformat(),
            results=results,
            avg_throughput_mbps=round(statistics.mean(all_throughputs), 2) if all_throughputs else 0.0,
            max_throughput_mbps=round(max(all_throughputs), 2) if all_throughputs else 0.0,
            min_throughput_mbps=round(min(all_throughputs), 2) if all_throughputs else 0.0,
        )
    else:
        # Benchmark all interfaces
        summary = run_all_benchmarks(args.duration, args.iterations)

    if args.json:
        output = {
            "hardware": summary.hardware_model,
            "summary": {
                "avg_throughput_mbps": summary.avg_throughput_mbps,
                "max_throughput_mbps": summary.max_throughput_mbps,
            },
            "results": [asdict(r) for r in summary.results],
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(summary)
        if args.output:
            path = save_results(summary, args.output)
            print(f"\nResults saved to: {path}")


if __name__ == "__main__":
    main()
