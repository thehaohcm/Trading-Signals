#!/usr/bin/env bash

# ==============================================================================
#  Deploy Web UI (Vue.js SPA + Nginx) to VPS Server
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
echo -e "${CYAN}${BOLD}           Deploying Web UI (Vue.js + Nginx) to VPS Server            ${NC}"
echo -e "${CYAN}======================================================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
if [ -f "$SCRIPT_DIR/.env" ]; then
    load_env "$SCRIPT_DIR/.env"
fi
if [ -f "$SCRIPT_DIR/trading_api/.env" ]; then
    load_env "$SCRIPT_DIR/trading_api/.env"
fi

DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_USER="${DEPLOY_USER:-}"
DEPLOY_PASSWORD="${DEPLOY_PASSWORD:-}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/$DEPLOY_USER/osint_ai_worker}"

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
echo -e "${CYAN}[2/5] Testing SSH connection to $DEPLOY_HOST...${NC}"
if ! $SSH_CMD "echo 'SSH_OK'" >/dev/null 2>&1; then
    echo -e "${RED}✗ Error: Cannot connect to $DEPLOY_USER@$DEPLOY_HOST via SSH.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection OK!${NC}"

# 2. Build Web UI production bundle
echo -e "${CYAN}[3/5] Building Web UI production bundle (npm run build)...${NC}"
cd "$SCRIPT_DIR"
npm run build
echo -e "${GREEN}✓ Production build complete (dist/).${NC}"

# 3. Package dist and nginx.conf
echo -e "${CYAN}[4/5] Packaging and uploading Web bundle to VPS...${NC}"
TARBALL="$SCRIPT_DIR/web_deploy.tar.gz"
rm -f "$TARBALL"

export COPYFILE_DISABLE=1
tar --no-mac-metadata -czf "$TARBALL" \
    --exclude=".DS_Store" \
    --exclude="._*" \
    dist nginx.conf -C osint_ai_worker docker-compose.yaml

$SCP_CMD "$TARBALL" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/web_deploy.tar.gz"
rm -f "$TARBALL"

# 4. Extract on server and start Nginx web container
echo -e "${CYAN}[5/5] Extracting on server and starting Nginx container 'osint_web'...${NC}"
REMOTE_SCRIPT="
    set -e
    cd '$DEPLOY_PATH'
    tar -xzf web_deploy.tar.gz
    rm -f web_deploy.tar.gz
    find dist/ -name '._*' -delete 2>/dev/null || true

    # Open port 80 and 3000 in firewalld if firewalld is active
    if command -v firewall-cmd >/dev/null 2>&1 && echo '$DEPLOY_PASSWORD' | sudo -S systemctl is-active --quiet firewalld; then
        echo '$DEPLOY_PASSWORD' | sudo -S firewall-cmd --add-port=80/tcp --permanent >/dev/null 2>&1 || true
        echo '$DEPLOY_PASSWORD' | sudo -S firewall-cmd --add-port=3000/tcp --permanent >/dev/null 2>&1 || true
        echo '$DEPLOY_PASSWORD' | sudo -S firewall-cmd --reload >/dev/null 2>&1 || true
    fi

    # Start or update the 'web' service in docker compose
    docker compose up -d --force-recreate --no-deps web
"

$SSH_CMD "$REMOTE_SCRIPT"

echo -e "${GREEN}✓ Nginx Web container running on port 80 & 3000!${NC}"
echo ""

# Health check
echo -e "${CYAN}Verifying Web UI...${NC}"
sleep 2

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "http://$DEPLOY_HOST/" || true)
if [ "$STATUS_CODE" = "200" ]; then
    echo -e "${GREEN}${BOLD}🎉 Web UI deployed successfully!${NC}"
    echo -e "Access URL: ${GREEN}${BOLD}http://$DEPLOY_HOST/${NC} or ${GREEN}${BOLD}http://$DEPLOY_HOST:3000/${NC}"
else
    echo -e "${YELLOW}Notice: Web UI returned HTTP status $STATUS_CODE. Check container logs below:${NC}"
fi

echo ""
echo -e "${CYAN}--- Web Container Status ---${NC}"
$SSH_CMD "docker ps --filter name=osint_web --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
echo -e "${CYAN}======================================================================${NC}"
