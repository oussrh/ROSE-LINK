#!/bin/bash
#
# ROSE Link VPN Watchdog
# Monitors WireGuard connection and restarts if needed
# Settings can be configured via web interface or /opt/rose-link/system/vpn-settings.conf
#

set -euo pipefail

INTERFACE="wg0"
LOG_TAG="rose-watchdog"
SETTINGS_FILE="/opt/rose-link/system/vpn-settings.conf"

# Default values (can be overridden by config file)
CHECK_INTERVAL=60
PING_HOST="8.8.8.8"

# Load settings from config file if it exists
load_settings() {
    if [ -f "$SETTINGS_FILE" ]; then
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue

            # Remove leading/trailing whitespace
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | tr -d '"')

            case "$key" in
                PING_HOST)
                    PING_HOST="$value"
                    ;;
                CHECK_INTERVAL)
                    CHECK_INTERVAL="$value"
                    ;;
            esac
        done < "$SETTINGS_FILE"
    fi
}

log() {
    logger -t "$LOG_TAG" "$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
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

    local current_time
    current_time=$(date +%s)
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
    # Load settings from config file
    load_settings

    log "ROSE Link VPN Watchdog started"
    log "Configuration: PING_HOST=$PING_HOST, CHECK_INTERVAL=${CHECK_INTERVAL}s"

    while true; do
        # Reload settings each cycle to pick up changes without restart
        load_settings

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
            log "VPN status: OK (ping to $PING_HOST successful)"
        fi

        sleep "$CHECK_INTERVAL"
    done
}

main "$@"
