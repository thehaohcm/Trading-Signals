#!/usr/bin/env bash

# ==============================================================================
#  Deploy Python Scripts, 24/7 Alert Daemon, and Cronjobs to VPS
# ==============================================================================

set -e

# ANSI Color Codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}${BOLD}    Deploying Python Scripts, 24/7 Alert Daemon & Cronjobs to VPS    ${NC}"
echo -e "${CYAN}======================================================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Function to load environment variables from a file
load_env() {
    local env_path="$1"
    if [ -f "$env_path" ]; then
        echo -e "${GREEN}✓ Loading env: $env_path${NC}"
        while IFS= read -r line || [ -n "$line" ]; do
            line=$(echo "$line" | xargs | tr -d '\r')
            if [[ ! "$line" =~ ^# ]] && [[ "$line" == *=* ]]; then
                export "$line"
            fi
        done < "$env_path"
        return 0
    fi
    return 1
}

# Load environment configuration
echo -e "${CYAN}[1/6] Loading configuration...${NC}"
if [ -f "$PROJECT_ROOT/.env" ]; then
    load_env "$PROJECT_ROOT/.env"
fi
if [ -f "$SCRIPT_DIR/.env" ]; then
    load_env "$SCRIPT_DIR/.env"
fi

DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_USER="${DEPLOY_USER:-}"
DEPLOY_PASSWORD="${DEPLOY_PASSWORD:-}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
DEPLOY_PATH="/home/$DEPLOY_USER/scripts"

if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ]; then
    echo -e "${RED}✗ Error: DEPLOY_HOST or DEPLOY_USER not set. Please configure .env file.${NC}"
    exit 1
fi

echo -e "Target VPS: ${YELLOW}$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH${NC}"

# Configure SSH and SCP command
SSH_OPTS="-p $DEPLOY_PORT -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH_CMD="ssh $SSH_OPTS $DEPLOY_USER@$DEPLOY_HOST"
SCP_CMD="scp -P $DEPLOY_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

if [ -n "$DEPLOY_PASSWORD" ]; then
    if command -v sshpass >/dev/null 2>&1; then
        SSH_CMD="sshpass -p $DEPLOY_PASSWORD $SSH_CMD"
        SCP_CMD="sshpass -p $DEPLOY_PASSWORD $SCP_CMD"
    fi
fi

# 1. Test SSH connection
echo -e "${CYAN}[2/6] Testing SSH connection to $DEPLOY_HOST...${NC}"
if ! $SSH_CMD "echo 'SSH_OK'" >/dev/null 2>&1; then
    echo -e "${RED}✗ Error: Cannot connect to $DEPLOY_USER@$DEPLOY_HOST via SSH.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection OK!${NC}"

# 2. Ensure directories exist on server
echo -e "${CYAN}[3/6] Setting up server directories & Python virtualenv...${NC}"
$SSH_CMD "
    echo '$DEPLOY_PASSWORD' | sudo -S mkdir -p '$DEPLOY_PATH' '/home/$DEPLOY_USER/www' 2>/dev/null || true
    echo '$DEPLOY_PASSWORD' | sudo -S chown -R $DEPLOY_USER:$DEPLOY_USER '$DEPLOY_PATH' '/home/$DEPLOY_USER/www' 2>/dev/null || true
    if [ ! -d '$DEPLOY_PATH/venv' ]; then
        echo 'Creating Python virtualenv at $DEPLOY_PATH/venv...'
        python3 -m venv '$DEPLOY_PATH/venv'
    fi
"
echo -e "${GREEN}✓ Remote directories and virtualenv verified.${NC}"

# 3. Package and upload scripts
echo -e "${CYAN}[4/6] Packaging and uploading scripts...${NC}"
TARBALL="$SCRIPT_DIR/scripts_deploy.tar.gz"
rm -f "$TARBALL"

export COPYFILE_DISABLE=1
tar --no-mac-metadata -czf "$TARBALL" \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude="*.log" \
    --exclude=".git" \
    --exclude="*.tar.gz" \
    --exclude=".DS_Store" \
    --exclude="._*" \
    --exclude=".env" \
    -C "$SCRIPT_DIR" .

$SCP_CMD "$TARBALL" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/scripts_deploy.tar.gz"
rm -f "$TARBALL"

# Extract and install dependencies
$SSH_CMD "
    set -e
    cd '$DEPLOY_PATH'
    mkdir -p '/home/$DEPLOY_USER/www'
    tar -xzf scripts_deploy.tar.gz
    rm -f scripts_deploy.tar.gz
    find . -name '._*' -delete 2>/dev/null || true

    # Configure .env from .env.server template
    if [ -f .env.server ]; then
        cp -f .env.server .env
        sed -i 's|DEPLOY_HOST=.*|DEPLOY_HOST=$DEPLOY_HOST|g' .env
        sed -i 's|NTFY_CLICK_URL=.*|NTFY_CLICK_URL=http://$DEPLOY_HOST/|g' .env
    fi

    chmod +x *.sh 2>/dev/null || true

    echo 'Installing / updating python dependencies in venv...'
    '$DEPLOY_PATH/venv/bin/pip' install --upgrade pip >/dev/null 2>&1
    '$DEPLOY_PATH/venv/bin/pip' install -r requirements.txt
"
echo -e "${GREEN}✓ Scripts uploaded and dependencies installed!${NC}"

# 4. Set up 24/7 background service for alert.py via Systemd
echo -e "${CYAN}[5/6] Setting up systemd service 'trading-alert.service' (24/7 background daemon)...${NC}"
SERVICE_CONTENT="[Unit]
Description=Trading Signals Alert Daemon
After=network.target docker.service

[Service]
Type=simple
User=$DEPLOY_USER
WorkingDirectory=$DEPLOY_PATH
ExecStart=/bin/bash -c 'exec $DEPLOY_PATH/venv/bin/python3 -u alert.py >> $DEPLOY_PATH/alert.log 2>&1'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"

$SSH_CMD "
    cat <<'SVCEOF' > '$DEPLOY_PATH/trading-alert.service'
$SERVICE_CONTENT
SVCEOF
    echo '$DEPLOY_PASSWORD' | sudo -S cp -f '$DEPLOY_PATH/trading-alert.service' /etc/systemd/system/trading-alert.service
    echo '$DEPLOY_PASSWORD' | sudo -S systemctl unmask trading-alert.service 2>/dev/null || true
    echo '$DEPLOY_PASSWORD' | sudo -S systemctl daemon-reload
    echo '$DEPLOY_PASSWORD' | sudo -S systemctl enable trading-alert.service
    echo '$DEPLOY_PASSWORD' | sudo -S systemctl restart trading-alert.service
"
echo -e "${GREEN}✓ Systemd service 'trading-alert' configured and started!${NC}"

# 5. Configure Crontab for user
echo -e "${CYAN}[6/6] Configuring scheduled Cronjobs...${NC}"
CRON_ENTRIES="# === TRADING SIGNALS CRONJOBS (Auto-managed) ===
0 */4 * * * /bin/bash $DEPLOY_PATH/run_crypto.sh >> $DEPLOY_PATH/cron.log 2>&1
0 */4 * * 1-5 $DEPLOY_PATH/venv/bin/python3 $DEPLOY_PATH/fetch_potential_world_stocks.py >> $DEPLOY_PATH/cron.log 2>&1
0 */4 * * 1-5 /bin/bash $DEPLOY_PATH/run_forex.sh >> $DEPLOY_PATH/cron.log 2>&1
5 0 * * * $DEPLOY_PATH/venv/bin/python3 $DEPLOY_PATH/rrg_assets_chart.py >> $DEPLOY_PATH/cron.log 2>&1
5 0 * * * $DEPLOY_PATH/venv/bin/python3 $DEPLOY_PATH/rrg_crypto_chart.py >> $DEPLOY_PATH/cron.log 2>&1
0 0 * * 0 $DEPLOY_PATH/venv/bin/python3 $DEPLOY_PATH/fetch_highest_interest_rate.py >> $DEPLOY_PATH/cron.log 2>&1
# ================================================"

$SSH_CMD "
    # Get existing crontab excluding previous trading signals jobs
    EXISTING_CRON=\$(crontab -l 2>/dev/null | grep -v 'TRADING SIGNALS' | grep -v '$DEPLOY_PATH' || true)
    NEW_CRON=\"\$EXISTING_CRON
$CRON_ENTRIES\"
    echo \"\$NEW_CRON\" | sed '/^[[:space:]]*$/d' | crontab -
"
echo -e "${GREEN}✓ Cronjobs installed successfully!${NC}"
echo ""

# Verify status
echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 Scripts & Daemons successfully deployed to $DEPLOY_HOST!${NC}"
echo ""
echo -e "${CYAN}--- Alert Daemon Status (systemctl status trading-alert) ---${NC}"
$SSH_CMD "echo '$DEPLOY_PASSWORD' | sudo -S systemctl status trading-alert --no-pager | head -n 12"

echo ""
echo -e "${CYAN}--- Installed Crontab (crontab -l) ---${NC}"
$SSH_CMD "crontab -l"
echo -e "${CYAN}======================================================================${NC}"
