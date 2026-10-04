#!/usr/bin/env bash

# ==============================================================================
#  Trading API - VPS Server Deployment Script
#  Builds & updates the Go trading_api container inside docker-compose on VPS.
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
echo -e "${CYAN}${BOLD}       Trading API Deployment -> VPS Server                         ${NC}"
echo -e "${CYAN}======================================================================${NC}"

# Find directories
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
echo -e "${CYAN}[1/5] Loading configuration...${NC}"
ENV_LOADED=false
if [ -f "$PROJECT_ROOT/.env" ]; then
    load_env "$PROJECT_ROOT/.env" && ENV_LOADED=true
fi
if [ -f "$SCRIPT_DIR/.env" ]; then
    load_env "$SCRIPT_DIR/.env" && ENV_LOADED=true
fi

if [ "$ENV_LOADED" = false ]; then
    echo -e "${RED}✗ Error: .env file with DEPLOY_* variables not found.${NC}"
    exit 1
fi

DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_USER="${DEPLOY_USER:-}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
DEPLOY_PATH="/home/$DEPLOY_USER/trading_api"

if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ]; then
    echo -e "${RED}✗ Error: DEPLOY_HOST or DEPLOY_USER not set. Please configure .env file.${NC}"
    exit 1
fi

echo -e "Deploy target: ${YELLOW}$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH${NC}"

# Configure SSH and SCP command
SSH_OPTS="-p $DEPLOY_PORT -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH_CMD="ssh $SSH_OPTS $DEPLOY_USER@$DEPLOY_HOST"
SCP_CMD="scp -P $DEPLOY_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

if [ -n "$DEPLOY_PASSWORD" ] && [ "$DEPLOY_PASSWORD" != "your_ssh_password" ]; then
    if command -v sshpass >/dev/null 2>&1; then
        SSH_CMD="sshpass -p $DEPLOY_PASSWORD $SSH_CMD"
        SCP_CMD="sshpass -p $DEPLOY_PASSWORD $SCP_CMD"
    else
        echo -e "${YELLOW}Warning: sshpass not installed. Password will be requested interactively.${NC}"
    fi
fi

# Test SSH connection
echo -e "${CYAN}[2/5] Testing SSH connection to $DEPLOY_HOST...${NC}"
if ! $SSH_CMD "echo 'SSH_OK'" >/dev/null 2>&1; then
    echo -e "${RED}✗ Error: Cannot connect to $DEPLOY_USER@$DEPLOY_HOST via SSH (Port $DEPLOY_PORT).${NC}"
    echo -e "Please check your network and credentials in $SCRIPT_DIR/.env"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful!${NC}"

# Create deployment tarball of trading_api
echo -e "${CYAN}[3/5] Packaging trading_api source files...${NC}"
TARBALL="$SCRIPT_DIR/trading_api_deploy.tar.gz"
rm -f "$TARBALL"

export COPYFILE_DISABLE=1
tar --no-mac-metadata -czf "$TARBALL" \
    --exclude="*.exe" \
    --exclude="*.log" \
    --exclude="trading_api_server" \
    --exclude=".git" \
    --exclude="vendor" \
    --exclude=".env" \
    --exclude=".DS_Store" \
    --exclude="._*" \
    --exclude="deploy*.tar.gz" \
    -C "$SCRIPT_DIR" \
    cmd internal migrations static Dockerfile docker-compose.yaml .dockerignore go.mod go.sum

TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)
echo -e "${GREEN}✓ Tarball created: $TARBALL_SIZE${NC}"

# Upload tarball to server
echo -e "${CYAN}[4/5] Uploading source to server...${NC}"
$SSH_CMD "mkdir -p '$DEPLOY_PATH'"
$SCP_CMD "$TARBALL" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/trading_api_deploy.tar.gz"
rm -f "$TARBALL"
echo -e "${GREEN}✓ Upload complete!${NC}"

# Remote extraction & Docker Compose rebuild
echo -e "${CYAN}[5/5] Extracting on server and running Docker container 'trading_api'...${NC}"
REMOTE_SCRIPT="
    set -e
    cd '$DEPLOY_PATH'
    tar -xzf trading_api_deploy.tar.gz
    rm -f trading_api_deploy.tar.gz
    find . -name '._*' -delete 2>/dev/null || true

    # Ensure remote .env exists for trading_api if missing
    if [ ! -f .env ]; then
        echo 'Creating default trading_api/.env...'
        cat << EOF > .env
DB_HOST=\${DB_HOST:-osint_postgres}
DB_USER=$DEPLOY_USER
DB_PASSWORD=$DEPLOY_PASSWORD
DB_NAME=\${DB_NAME:-thehaohcm_trading_signal_db}
DB_PORT=\${DB_PORT:-5432}
GROQ_API_KEY=\${GROQ_API_KEY:-}
EOF
    fi

    # Ensure docker network exists
    docker network inspect osint_ai_worker_default >/dev/null 2>&1 || docker network create osint_ai_worker_default

    # Stop legacy osint_api container if running so port 8080 is used by trading_api
    docker stop osint_api 2>/dev/null || true
    docker rm osint_api 2>/dev/null || true

    # Rebuild and start standalone trading_api container
    docker compose up -d --build --force-recreate
"

if ! $SSH_CMD "$REMOTE_SCRIPT"; then
    echo -e "${RED}✗ Error: Remote build failed. Check docker logs on server:${NC}"
    $SSH_CMD "cd '$DEPLOY_PATH' && docker compose logs --tail 30" || true
    exit 1
fi

echo -e "${GREEN}✓ Docker container rebuilt and restarted successfully!${NC}"
echo ""

# Health Check verification
echo -e "${CYAN}Verifying API service health...${NC}"
sleep 3

HEALTH_STATUS="UNKNOWN"
for i in {1..6}; do
    RESPONSE=$(curl -s -m 5 "http://$DEPLOY_HOST:8080/health" || true)
    if [ "$RESPONSE" = "OK" ]; then
        HEALTH_STATUS="HEALTHY (HTTP 200 OK)"
        break
    fi
    echo -e "Waiting for API to start up (attempt $i/6)..."
    sleep 2
done

echo ""
echo -e "${CYAN}======================================================================${NC}"
if [ "$HEALTH_STATUS" = "HEALTHY (HTTP 200 OK)" ]; then
    echo -e "${GREEN}${BOLD}🎉 Trading API deployed successfully to $DEPLOY_HOST:8080!${NC}"
    echo -e "Health check: ${GREEN}$HEALTH_STATUS${NC}"
else
    echo -e "${YELLOW}⚠️ API container started, but health endpoint returned: '$RESPONSE'${NC}"
    echo -e "Checking container logs below:${NC}"
fi

echo -e "${CYAN}--- Container Status ---${NC}"
$SSH_CMD "docker ps --filter name=trading_api --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo -e "${CYAN}--- Recent Logs ---${NC}"
$SSH_CMD "docker logs --tail 15 trading_api"

echo -e "${CYAN}======================================================================${NC}"
