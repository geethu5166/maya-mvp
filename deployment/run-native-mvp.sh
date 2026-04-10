#!/usr/bin/env bash

# Run backend MVP natively on droplet (no Docker).
# Installs a lightweight Python environment and creates a systemd service.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/maya-mvp}"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
SERVICE_NAME="maya-backend"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [ "${EUID}" -ne 0 ]; then
  echo "Run as root: sudo bash deployment/run-native-mvp.sh"
  exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
  echo "Backend directory not found: $BACKEND_DIR"
  exit 1
fi

echo "[native] Installing system packages..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip curl

echo "[native] Creating virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel

echo "[native] Installing backend MVP dependencies..."
"$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements-mvp.txt"

echo "[native] Writing systemd service: $SERVICE_FILE"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=MAYA MVP Backend (Native)
After=network.target

[Service]
Type=simple
WorkingDirectory=$BACKEND_DIR
Environment=ENV=development
Environment=DEBUG=false
Environment=STARTUP_STRICT=false
Environment=STARTUP_MINIMAL=true
Environment=SECRET_KEY=change_this_secret_key_before_production
Environment=JWT_SECRET_KEY=change_this_secret_key_before_production
Environment=INIT_ADMIN_USERNAME=admin
Environment=INIT_ADMIN_PASSWORD=Admin#ChangeMe123
Environment=POSTGRES_PASSWORD=dummy_password_123456
Environment=CORS_ORIGINS=https://maya.vaultrap.com,http://localhost:5173
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info --no-access-log
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "[native] Reloading and starting service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "[native] Service status:"
systemctl --no-pager --full status "$SERVICE_NAME" | sed -n '1,20p'

echo "[native] Health check:"
curl -sS http://127.0.0.1:8000/health || true
echo

echo "[native] Done."
