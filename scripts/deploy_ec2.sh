#!/usr/bin/env bash
# ==============================================================================
# BUST Backend EC2 Turnkey Deployment Script
# Usage:
#   ./scripts/deploy_ec2.sh <EC2_HOST_OR_IP> <PEM_FILE_PATH> [USER=ubuntu]
#
# Example:
#   ./scripts/deploy_ec2.sh 54.210.120.45 ~/.ssh/my-key.pem ubuntu
# ==============================================================================

set -euo pipefail

HOST="${1:-}"
KEY_PATH="${2:-}"
REMOTE_USER="${3:-ubuntu}"

if [[ -z "$HOST" || -z "$KEY_PATH" ]]; then
    echo "======================================================================"
    echo "  BUST Backend EC2 Deployment"
    echo "======================================================================"
    echo "Usage:"
    echo "  $0 <EC2_HOST_OR_IP> <PATH_TO_PEM_KEY> [REMOTE_USER]"
    echo ""
    echo "Example:"
    echo "  $0 54.210.120.45 ./my-ec2-key.pem ubuntu"
    echo "======================================================================"
    exit 1
fi

if [[ ! -f "$KEY_PATH" ]]; then
    echo "❌ Error: Key file not found at '$KEY_PATH'"
    exit 1
fi

# Ensure correct permissions on private key
chmod 400 "$KEY_PATH"

REMOTE_TARGET="${REMOTE_USER}@${HOST}"
REMOTE_DIR="/home/${REMOTE_USER}/bust/backend"

echo "======================================================================"
echo "🚀 Deploying BUST Backend to ${REMOTE_TARGET}"
echo "======================================================================"

# 1. Test SSH Connection
echo "📡 [1/6] Verifying SSH connectivity..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$REMOTE_TARGET" "echo 'Connected successfully to '\$(uname -n)"

# 2. Install Remote Prerequisites
echo "📦 [2/6] Preparing remote environment (Python, pip, venv, rsync)..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_TARGET" bash -s << 'EOF'
set -e
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv rsync curl
elif command -v dnf &> /dev/null; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip rsync curl
fi
EOF

# 3. Create destination directory
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_TARGET" "mkdir -p ${REMOTE_DIR} ${REMOTE_DIR}/data"

# 4. Sync backend source code
echo "📂 [3/6] Syncing backend source code..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

rsync -avz -e "ssh -i ${KEY_PATH} -o StrictHostKeyChecking=no" \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    "${REPO_ROOT}/backend/" "${REMOTE_TARGET}:${REMOTE_DIR}/"

# 5. Remote virtualenv setup and dependency installation
echo "🐍 [4/6] Setting up virtual environment and installing packages..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_TARGET" bash -s << EOF
set -e
cd "${REMOTE_DIR}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
EOF

# 6. Configure Systemd Service
echo "⚙️  [5/6] Configuring systemd background daemon..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_TARGET" bash -s << EOF
set -e
# Generate unit file with accurate user and path
cat << 'UNIT' | sudo tee /etc/systemd/system/bust-backend.service > /dev/null
[Unit]
Description=BUST FastAPI Agent Backend
After=network.target

[Service]
Type=simple
User=${REMOTE_USER}
WorkingDirectory=${REMOTE_DIR}
EnvironmentFile=${REMOTE_DIR}/.env
ExecStart=${REMOTE_DIR}/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable bust-backend
sudo systemctl restart bust-backend
EOF

# 7. Health Check
echo "🔍 [6/6] Verifying backend health..."
sleep 3
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_TARGET" "curl -s http://localhost:8000/api/health" || echo "Note: verify uvicorn log with: journalctl -u bust-backend -f"

echo ""
echo "======================================================================"
echo "✅ BUST Backend is live on EC2!"
echo "   Endpoint: http://${HOST}:8000"
echo "   Health:   http://${HOST}:8000/api/health"
echo "   Docs:     http://${HOST}:8000/docs"
echo ""
echo "Useful Commands on EC2:"
echo "   ssh -i ${KEY_PATH} ${REMOTE_TARGET}"
echo "   sudo journalctl -u bust-backend -f"
echo "   sudo systemctl status bust-backend"
echo "======================================================================"
