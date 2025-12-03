# ROSE Link Performance Benchmarking

This document describes the performance benchmarking tools available for ROSE Link, enabling validation of VPN throughput and API performance on various Raspberry Pi hardware.

## Overview

ROSE Link includes two benchmarking tools:

1. **Network Throughput Benchmark**: Measures VPN and hotspot network performance
2. **API Load Test**: Tests FastAPI backend under concurrent load

## Requirements

Install benchmark dependencies:

```bash
cd backend
pip install -r requirements-dev.txt
pip install httpx  # For load testing
```

For iperf3 throughput tests (optional):
```bash
sudo apt install iperf3
```

## Network Throughput Benchmark

Measures actual network throughput on VPN (WireGuard), WiFi, and Ethernet interfaces.

### Usage

```bash
# Benchmark all active interfaces
python -m benchmarks.throughput --all

# Benchmark specific interface
python -m benchmarks.throughput --interface wg0

# Custom duration and iterations
python -m benchmarks.throughput --interface wg0 --duration 30 --iterations 5

# Output to JSON file
python -m benchmarks.throughput --all --output results.json

# JSON output to stdout
python -m benchmarks.throughput --all --json
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--interface, -i` | Specific interface to benchmark | All active |
| `--all, -a` | Benchmark all active interfaces | - |
| `--duration, -d` | Test duration in seconds | 10 |
| `--iterations, -n` | Number of test iterations | 3 |
| `--output, -o` | Save results to JSON file | - |
| `--json` | Output JSON to stdout | - |

### Metrics Collected

- **Throughput (TX/RX)**: Megabits per second
- **Packet Loss**: Percentage of dropped packets
- **Latency**: Round-trip time in milliseconds (VPN interfaces)
- **Jitter**: Latency variation (VPN interfaces)
- **Hardware Info**: Pi model, kernel version, memory

### Sample Output

```
============================================================
ROSE Link Performance Benchmark Results
============================================================
Hardware: Raspberry Pi 4 Model B Rev 1.4
Kernel: 6.1.0-rpi7-rpi-v8
Memory: 3884 MB
Test Date: 2024-01-15T10:30:45
------------------------------------------------------------

Summary:
  Average Throughput: 85.5 Mbps
  Maximum Throughput: 92.3 Mbps
  Minimum Throughput: 78.2 Mbps

Detailed Results:

  Interface: wg0
    TX: 45.2 Mbps
    RX: 42.8 Mbps
    Packet Loss: 0.0%
    Latency: 25.3 ms
    Jitter: 2.1 ms
============================================================
```

## API Load Test

Tests the FastAPI backend under concurrent load to validate performance on Pi hardware.

### Usage

```bash
# Basic load test (60 seconds, 10 concurrent)
python -m benchmarks.load_test --url http://localhost:8000

# Custom duration and concurrency
python -m benchmarks.load_test --url http://localhost:8000 --duration 120 --concurrent 50

# Stress test (find breaking point)
python -m benchmarks.load_test --url http://localhost:8000 --stress

# Output to JSON
python -m benchmarks.load_test --url http://localhost:8000 --output results.json
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url, -u` | Base URL of the API | http://localhost:8000 |
| `--duration, -d` | Test duration in seconds | 60 |
| `--concurrent, -c` | Concurrent requests | 10 |
| `--stress` | Run progressive stress test | - |
| `--output, -o` | Save results to JSON file | - |
| `--json` | Output JSON to stdout | - |

### Endpoints Tested

The load test cycles through these API endpoints:

- `GET /api/health` - Health check
- `GET /api/status` - System status
- `GET /api/vpn/status` - VPN status
- `GET /api/hotspot/clients` - Connected clients
- `GET /api/system/info` - System information
- `GET /api/vpn/profiles` - VPN profiles

### Metrics Collected

- **Requests per Second**: Throughput
- **Response Times**: Average, min, max, P50, P95, P99
- **Error Rate**: Percentage of failed requests

### Performance Targets

| Metric | Target | Warning |
|--------|--------|---------|
| Error Rate | < 1% | < 5% |
| P95 Response Time | < 500ms | < 1000ms |
| Requests/Second | > 50 | > 25 |

### Sample Output

```
============================================================
ROSE Link API Load Test Results
============================================================
Target: http://localhost:8000
Duration: 60.0s
------------------------------------------------------------

Request Statistics:
  Total Requests: 3420
  Successful: 3415
  Failed: 5
  Error Rate: 0.15%
  Requests/Second: 57.0

Response Time Statistics:
  Average: 175.3 ms
  Minimum: 12.5 ms
  Maximum: 892.1 ms
  P50 (Median): 145.2 ms
  P95: 425.8 ms
  P99: 678.3 ms
============================================================

Performance Assessment:
  [PASS] Error rate below 1%
  [PASS] P95 response time under 500ms
  [PASS] Throughput at 57.0 req/s
```

## Hardware Performance Reference

Expected performance on different Raspberry Pi models:

| Model | VPN Throughput | API Requests/s | Notes |
|-------|---------------|----------------|-------|
| Pi 5 | ~300 Mbps | 100+ | Best performance |
| Pi 4 (4GB) | ~100 Mbps | 50-80 | Recommended |
| Pi 4 (2GB) | ~100 Mbps | 40-60 | Good |
| Pi 3B+ | ~30 Mbps | 20-30 | Limited by CPU |
| Zero 2W | ~25 Mbps | 15-25 | Portable use |

*VPN throughput depends on encryption overhead and network conditions*

## CI Integration

Add benchmarks to your CI pipeline (non-blocking):

```yaml
- name: Run performance benchmarks
  continue-on-error: true
  working-directory: backend
  run: |
    python -m benchmarks.throughput --interface lo --duration 5 --json > throughput.json
    python -m benchmarks.load_test --url http://localhost:8000 --duration 30 --json > load_test.json
```

## Interpreting Results

### Throughput Analysis

1. **TX vs RX asymmetry**: Common on residential connections
2. **Packet loss > 0.1%**: Indicates congestion or hardware issues
3. **High jitter**: May cause VoIP/video issues

### API Performance

1. **High P99 vs P50**: Indicates occasional slow requests
2. **Increasing response times under load**: May need optimization
3. **Errors at high concurrency**: Find the sustainable limit

## Troubleshooting

### Low VPN Throughput

1. Check CPU usage during test (`htop`)
2. Verify WireGuard kernel module is loaded
3. Test without VPN to establish baseline
4. Check MTU settings

### High API Latency

1. Check disk I/O (may be SD card bottleneck)
2. Monitor memory usage
3. Review slow database queries
4. Consider using Redis for caching

## Contributing

When adding new features, include benchmark results showing:

1. Performance impact on Pi 4
2. Memory usage changes
3. Any new bottlenecks introduced
