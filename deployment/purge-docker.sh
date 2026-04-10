#!/usr/bin/env bash

# Aggressive Docker cleanup for low-disk droplet.
# By default removes Docker artifacts only.
# Use --purge-engine to uninstall Docker packages too.

set -euo pipefail

PURGE_ENGINE="false"
PROJECT_DIR="${PROJECT_DIR:-/root/maya-mvp}"

if [ "${1:-}" = "--purge-engine" ]; then
  PURGE_ENGINE="true"
fi

if [ "${EUID}" -ne 0 ]; then
  echo "Run as root: sudo bash deployment/purge-docker.sh [--purge-engine]"
  exit 1
fi

echo "[purge] Stopping compose stack if present..."
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
  cd "$PROJECT_DIR"
  docker compose down --remove-orphans || true
fi

echo "[purge] Removing containers/images/networks/volumes/cache..."
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker system prune -af --volumes || true
docker builder prune -af || true

echo "[purge] Stopping Docker services..."
systemctl stop docker docker.socket containerd 2>/dev/null || true
systemctl disable docker docker.socket containerd 2>/dev/null || true

if [ "$PURGE_ENGINE" = "true" ]; then
  echo "[purge] Uninstalling Docker engine packages..."
  apt-get purge -y \
    docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin \
    docker.io containerd containerd.io runc || true
  apt-get autoremove -y --purge
fi

echo "[purge] Removing Docker data directories..."
rm -rf /var/lib/docker /var/lib/containerd /etc/docker /var/run/docker.sock 2>/dev/null || true

echo "[purge] Disk usage after cleanup:"
df -h /

echo "[purge] Done."
