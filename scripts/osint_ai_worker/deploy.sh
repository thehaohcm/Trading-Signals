#!/usr/bin/env bash

# ==============================================================================
#  OSINT AI Worker Deployment Script (Tarball-based Upload preserving structure)
# ==============================================================================

set -e

# ANSI Color Codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}             OSINT AI Worker Git Diff Deploy Script                   ${NC}"
echo -e "${CYAN}======================================================================${NC}"

# Find script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to load environment variables from a file
load_env() {
    local env_path="$1"
    if [ -f "$env_path" ]; then
        echo -e "${GREEN}✓ Found env file at: $env_path${NC}"
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

# Load configuration (looking in trading_api/.env first then .env)
echo -e "Loading configuration..."
if load_env "$SCRIPT_DIR/trading_api/.env"; then
    :
elif load_env "$SCRIPT_DIR/.env"; then
    :
else
    echo -e "${RED}✗ Error: .env file containing DEPLOY_* variables not found.${NC}"
    exit 1
fi

# Set deployment destination
DEPLOY_PATH="/home/thehaohcm/osint_ai_worker"

# Validate required variables
MISSING_VARS=()
[ -z "$DEPLOY_HOST" ] && MISSING_VARS+=("DEPLOY_HOST")
[ -z "$DEPLOY_USER" ] && MISSING_VARS+=("DEPLOY_USER")

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}✗ Error: Missing required deployment configuration in .env:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "  - $var"
    done
    exit 1
fi

DEPLOY_PORT=${DEPLOY_PORT:-22}

# Setup SSH and SCP authentication prefixes
SSH_PREFIX=""
SCP_PREFIX=""
USE_PASSWORD=false

if [ -n "$DEPLOY_PASSWORD" ] && [ "$DEPLOY_PASSWORD" != "your_ssh_password" ]; then
    USE_PASSWORD=true
fi

if [ "$USE_PASSWORD" = true ]; then
    if command -v sshpass >/dev/null 2>&1; then
        echo -e "${GREEN}✓ sshpass detected. Using password-based authentication.${NC}"
        SSH_PREFIX="sshpass -p $DEPLOY_PASSWORD"
        SCP_PREFIX="sshpass -p $DEPLOY_PASSWORD"
    else
        echo -e "${YELLOW}⚠ Warning: DEPLOY_PASSWORD is configured, but 'sshpass' is not installed.${NC}"
        echo -e "  Falling back to native SSH/SCP. You may be prompted for your password.${NC}\n"
    fi
else
    echo -e "${CYAN}ℹ Info: Using SSH Key / Agent auth.${NC}"
fi

# Detect Git root and paths
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo -e "${RED}✗ Error: This directory is not inside a Git repository. Diffs cannot be calculated.${NC}"
    exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
REL_SCRIPT_DIR="${SCRIPT_DIR#"$REPO_ROOT/"}"

echo -e "Detecting modified and untracked files inside $REL_SCRIPT_DIR via Git..."
FILES_TO_DEPLOY=()

while IFS= read -r file; do
    if [ -n "$file" ] && [ -f "$REPO_ROOT/$file" ]; then
        # Calculate path relative to scripts/osint_ai_worker
        SCRIPT_REL_PATH="${file#"$REL_SCRIPT_DIR/"}"
        if [[ ! " ${FILES_TO_DEPLOY[*]} " =~ " ${SCRIPT_REL_PATH} " ]]; then
            FILES_TO_DEPLOY+=("$SCRIPT_REL_PATH")
        fi
    fi
done < <( (git diff --name-only HEAD -- "$SCRIPT_DIR"; git ls-files --others --exclude-standard -- "$SCRIPT_DIR") || true )

# Build the final list of files to archive (including untracked local .env files)
FILES_TO_TAR=("${FILES_TO_DEPLOY[@]}")

if [ -f "$SCRIPT_DIR/.env" ]; then
    if [[ ! " ${FILES_TO_TAR[*]} " =~ " .env " ]]; then
        FILES_TO_TAR+=(".env")
    fi
fi
if [ -f "$SCRIPT_DIR/trading_api/.env" ]; then
    if [[ ! " ${FILES_TO_TAR[*]} " =~ " trading_api/.env " ]]; then
        FILES_TO_TAR+=("trading_api/.env")
    fi
fi

if [ ${#FILES_TO_TAR[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠ No modified, untracked, or .env files detected. Nothing to deploy. Exiting.${NC}"
    exit 0
fi

echo -e "${GREEN}✓ Ready to deploy ${#FILES_TO_TAR[@]} files/directories:${NC}"
for file in "${FILES_TO_TAR[@]}"; do
    echo -e "  - $file"
done
echo -e ""

echo -e "Deployment settings:"
echo -e "  - Host      : ${YELLOW}$DEPLOY_HOST${NC}"
echo -e "  - User      : ${YELLOW}$DEPLOY_USER${NC}"
echo -e "  - Port      : ${YELLOW}$DEPLOY_PORT${NC}"
echo -e "  - Remote Path: ${YELLOW}$DEPLOY_PATH${NC} ${CYAN}(Preserves structure)${NC}"
echo -e ""

# 1. Connection check
echo -e "${CYAN}[1/3] Testing SSH connection...${NC}"
if $SSH_PREFIX ssh -p "$DEPLOY_PORT" -o ConnectTimeout=5 -o BatchMode=no "$DEPLOY_USER@$DEPLOY_HOST" "echo -n Connection successful!" > /dev/null; then
    echo -e "${GREEN}✓ SSH Connection successfully established.${NC}\n"
else
    echo -e "${RED}✗ Error: Cannot connect to $DEPLOY_HOST via SSH on port $DEPLOY_PORT.${NC}"
    exit 1
fi

# Ensure remote target path exists
$SSH_PREFIX ssh -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" "mkdir -p \"$DEPLOY_PATH\""

# 2. Package files locally
echo -e "${CYAN}[2/3] Bundling files into deploy.tar.gz...${NC}"
tar -czf "$SCRIPT_DIR/deploy.tar.gz" -C "$SCRIPT_DIR" "${FILES_TO_TAR[@]}"
echo -e "${GREEN}✓ Package created successfully.${NC}\n"

# 3. Upload & extract on remote server
echo -e "${CYAN}[3/3] Uploading tarball and extracting to $DEPLOY_PATH...${NC}"
$SCP_PREFIX scp -P "$DEPLOY_PORT" "$SCRIPT_DIR/deploy.tar.gz" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/deploy.tar.gz"

echo -e "Extracting files on remote server..."
$SSH_PREFIX ssh -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" "tar -xzf \"$DEPLOY_PATH/deploy.tar.gz\" -C \"$DEPLOY_PATH/\" && rm \"$DEPLOY_PATH/deploy.tar.gz\" && cd \"$DEPLOY_PATH\" && docker compose down && docker compose up --build -d"

# Cleanup local package
rm "$SCRIPT_DIR/deploy.tar.gz"

echo -e ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}🎉 OSINT AI Worker deployed successfully to $DEPLOY_PATH! ${NC}"
echo -e "${CYAN}======================================================================${NC}"
