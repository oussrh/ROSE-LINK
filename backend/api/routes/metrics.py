"""
Prometheus Metrics Endpoint
===========================

Exposes system metrics in Prometheus format for monitoring.

Metrics exposed:
- rose_link_info: Application version info
- rose_link_vpn_status: VPN connection status (1=connected, 0=disconnected)
- rose_link_wan_status: WAN connection status (1=connected, 0=disconnected)
- rose_link_hotspot_status: Hotspot status (1=active, 0=inactive)
- rose_link_hotspot_clients: Number of connected hotspot clients
- rose_link_cpu_temperature_celsius: CPU temperature
- rose_link_cpu_usage_percent: CPU usage percentage
- rose_link_memory_used_bytes: Used memory in bytes
- rose_link_memory_total_bytes: Total memory in bytes
- rose_link_disk_used_bytes: Used disk space in bytes
- rose_link_disk_total_bytes: Total disk space in bytes
- rose_link_network_rx_bytes_total: Total bytes received per interface
- rose_link_network_tx_bytes_total: Total bytes transmitted per interface
- rose_link_uptime_seconds: System uptime in seconds

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from config import APP_VERSION
from services.wan_service import WANService
from services.vpn_service import VPNService
from services.hotspot_service import HotspotService
from services.system_service import SystemService
from services.bandwidth_service import BandwidthService
from core.middleware import get_request_metrics

logger = logging.getLogger("rose-link.metrics")

router = APIRouter()


def _format_metric(
    name: str,
    value: float,
    help_text: str = "",
    metric_type: str = "gauge",
    labels: dict = None
) -> str:
    """
    Format a single metric in Prometheus format.

    Args:
        name: Metric name
        value: Metric value
        help_text: Help text for the metric
        metric_type: Metric type (gauge, counter, etc.)
        labels: Optional labels dictionary

    Returns:
        Formatted metric string
    """
    lines = []

    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} {metric_type}")

    if labels:
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        lines.append(f"{name}{{{label_str}}} {value}")
    else:
        lines.append(f"{name} {value}")

    return "\n".join(lines)


def _collect_metrics() -> List[str]:
    """
    Collect all metrics.

    Returns:
        List of formatted metric strings
    """
    metrics = []

    # Application info
    metrics.append(_format_metric(
        "rose_link_info",
        1,
        "ROSE Link application information",
        "gauge",
        {"version": APP_VERSION}
    ))

    # VPN status
    try:
        vpn_status = VPNService.get_status()
        metrics.append(_format_metric(
            "rose_link_vpn_status",
            1 if vpn_status.active else 0,
            "VPN connection status (1=connected, 0=disconnected)",
            "gauge"
        ))
    except Exception as e:
        logger.debug(f"Failed to get VPN status: {e}")
        metrics.append(_format_metric(
            "rose_link_vpn_status",
            0,
            "VPN connection status (1=connected, 0=disconnected)",
            "gauge"
        ))

    # WAN status
    try:
        wan_status = WANService.get_status()
        metrics.append(_format_metric(
            "rose_link_wan_status",
            1 if wan_status.active else 0,
            "WAN connection status (1=connected, 0=disconnected)",
            "gauge"
        ))
    except Exception as e:
        logger.debug(f"Failed to get WAN status: {e}")

    # Hotspot status
    try:
        hotspot_status = HotspotService.get_status()
        metrics.append(_format_metric(
            "rose_link_hotspot_status",
            1 if hotspot_status.active else 0,
            "Hotspot status (1=active, 0=inactive)",
            "gauge"
        ))

        # Connected clients
        clients = HotspotService.get_clients()
        metrics.append(_format_metric(
            "rose_link_hotspot_clients",
            len(clients),
            "Number of connected hotspot clients",
            "gauge"
        ))
    except Exception as e:
        logger.debug(f"Failed to get hotspot status: {e}")

    # System info
    try:
        sys_info = SystemService.get_info()

        # CPU temperature
        if sys_info.cpu_temp_c is not None:
            metrics.append(_format_metric(
                "rose_link_cpu_temperature_celsius",
                sys_info.cpu_temp_c,
                "CPU temperature in Celsius",
                "gauge"
            ))

        # CPU usage
        if sys_info.cpu_usage_percent is not None:
            metrics.append(_format_metric(
                "rose_link_cpu_usage_percent",
                sys_info.cpu_usage_percent,
                "CPU usage percentage",
                "gauge"
            ))

        # Memory
        if sys_info.ram_mb is not None:
            total_bytes = sys_info.ram_mb * 1024 * 1024
            free_bytes = (sys_info.ram_free_mb or 0) * 1024 * 1024
            used_bytes = total_bytes - free_bytes

            metrics.append(_format_metric(
                "rose_link_memory_total_bytes",
                total_bytes,
                "Total memory in bytes",
                "gauge"
            ))
            metrics.append(_format_metric(
                "rose_link_memory_used_bytes",
                used_bytes,
                "Used memory in bytes",
                "gauge"
            ))

        # Disk
        if sys_info.disk_total_gb is not None:
            total_bytes = sys_info.disk_total_gb * 1024 * 1024 * 1024
            free_bytes = (sys_info.disk_free_gb or 0) * 1024 * 1024 * 1024
            used_bytes = total_bytes - free_bytes

            metrics.append(_format_metric(
                "rose_link_disk_total_bytes",
                total_bytes,
                "Total disk space in bytes",
                "gauge"
            ))
            metrics.append(_format_metric(
                "rose_link_disk_used_bytes",
                used_bytes,
                "Used disk space in bytes",
                "gauge"
            ))

        # Uptime
        if sys_info.uptime_seconds is not None:
            metrics.append(_format_metric(
                "rose_link_uptime_seconds",
                sys_info.uptime_seconds,
                "System uptime in seconds",
                "counter"
            ))

    except Exception as e:
        logger.debug(f"Failed to get system info: {e}")

    # Network bandwidth
    try:
        bandwidth = BandwidthService.get_stats()
        interfaces = bandwidth.get("interfaces", {})

        for iface, stats in interfaces.items():
            metrics.append(_format_metric(
                "rose_link_network_rx_bytes_total",
                stats.get("rx_bytes", 0),
                "Total bytes received",
                "counter",
                {"interface": iface}
            ))
            metrics.append(_format_metric(
                "rose_link_network_tx_bytes_total",
                stats.get("tx_bytes", 0),
                "Total bytes transmitted",
                "counter",
                {"interface": iface}
            ))
            metrics.append(_format_metric(
                "rose_link_network_rx_packets_total",
                stats.get("rx_packets", 0),
                "Total packets received",
                "counter",
                {"interface": iface}
            ))
            metrics.append(_format_metric(
                "rose_link_network_tx_packets_total",
                stats.get("tx_packets", 0),
                "Total packets transmitted",
                "counter",
                {"interface": iface}
            ))

    except Exception as e:
        logger.debug(f"Failed to get bandwidth stats: {e}")

    return metrics


@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics() -> str:
    """
    Get all metrics in Prometheus format.

    Returns:
        Metrics in Prometheus exposition format
    """
    metrics = _collect_metrics()
    return "\n\n".join(metrics) + "\n"


@router.get("/metrics/performance")
async def get_performance_metrics() -> dict:
    """
    Get application performance metrics.

    Returns JSON with:
    - total_requests: Total number of requests processed
    - total_errors: Total number of 5xx errors
    - error_rate: Error rate (0-1)
    - latency_ms: Latency statistics (avg, min, max, p50, p95, p99)
    - requests_by_path: Request count per endpoint

    Returns:
        Performance metrics dictionary
    """
    return get_request_metrics()
