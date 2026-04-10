#!/usr/bin/env bash

# Safe disk cleanup for Ubuntu droplet.
# Keeps application data intact (does not delete Docker volumes).

set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Run as root: sudo bash deployment/cleanup-disk.sh"
  exit 1
fi

log() {
  echo "[cleanup] $*"
}

show_usage() {
  log "Disk usage summary"
  df -h /
  echo
  du -xhd1 /var 2>/dev/null | sort -h || true
  echo
  docker system df || true
  echo
}

log "Before cleanup"
show_usage

log "Pruning unused Docker images/containers/build cache (keeping volumes)"
docker system prune -af || true
docker builder prune -af || true

log "Cleaning apt cache and unused packages"
apt-get clean
apt-get autoremove -y

log "Vacuuming systemd journal logs (keep last 7 days)"
journalctl --vacuum-time=7d || true

log "Removing rotated/compressed logs"
find /var/log -type f -name '*.gz' -delete 2>/dev/null || true
find /var/log -type f -name '*.1' -delete 2>/dev/null || true

log "Truncating very large active logs (>200MB)"
find /var/log -type f -size +200M -exec truncate -s 0 {} \; 2>/dev/null || true

log "Cleaning old temp files (>7 days)"
find /tmp -xdev -mindepth 1 -mtime +7 -delete 2>/dev/null || true

log "Cleaning root cache directories"
rm -rf /root/.cache/pip/* 2>/dev/null || true
rm -rf /root/.npm/_cacache/* 2>/dev/null || true

log "After cleanup"
show_usage

log "Done"
