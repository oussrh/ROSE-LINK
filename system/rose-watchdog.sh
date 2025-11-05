#!/bin/bash
#
# ROSE Link VPN Watchdog
# Monitors WireGuard connection and restarts if needed
#

set -euo pipefail

INTERFACE="wg0"
CHECK_INTERVAL=60  # seconds
PING_HOST="192.168.178.1"  # Fritz!Box (adjust if needed)
LOG_TAG="rose-watchdog"

log() {
    logger -t "$LOG_TAG" "$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@"
}

check_wg_interface() {
    if ip link show "$INTERFACE" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

check_wg_handshake() {
    local last_handshake
    last_handshake=$(sudo wg show "$INTERFACE" latest-handshakes 2>/dev/null | awk '{print $2}')

    if [ -z "$last_handshake" ]; then
        return 1
    fi

    local current_time=$(date +%s)
    local time_diff=$((current_time - last_handshake))

    # Consider connection dead if no handshake in last 3 minutes
    if [ "$time_diff" -gt 180 ]; then
        log "WARNING: No handshake in $time_diff seconds"
        return 1
    fi

    return 0
}

check_vpn_connectivity() {
    # Try to ping Fritz!Box through VPN
    if ping -c 1 -W 3 -I "$INTERFACE" "$PING_HOST" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

restart_vpn() {
    log "Restarting WireGuard..."

    sudo systemctl restart wg-quick@wg0

    sleep 5

    if check_wg_interface; then
        log "WireGuard restarted successfully"
        return 0
    else
        log "ERROR: Failed to restart WireGuard"
        return 1
    fi
}

main() {
    log "ROSE Link VPN Watchdog started"

    while true; do
        if ! check_wg_interface; then
            log "WARNING: WireGuard interface $INTERFACE is down"
            restart_vpn
        elif ! check_wg_handshake; then
            log "WARNING: WireGuard handshake is stale"
            restart_vpn
        elif ! check_vpn_connectivity; then
            log "WARNING: Cannot reach $PING_HOST through VPN"
            restart_vpn
        else
            log "VPN status: OK"
        fi

        sleep "$CHECK_INTERVAL"
    done
}

main "$@"
