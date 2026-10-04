#!/usr/bin/env bash

# ==============================================================================
#  Trading API Multi-Target Deployment Script
#  Supports deploying to VPS Server, Fly.io, or Both.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI Color Codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

deploy_to_server() {
    echo -e "\n${CYAN}>>> Initiating deployment to VPS Server...${NC}"
    bash "$SCRIPT_DIR/deploy_server.sh"
}

deploy_to_fly() {
    echo -e "\n${CYAN}>>> Initiating deployment to Fly.io (flyctl)...${NC}"
    if ! command -v flyctl >/dev/null 2>&1 && ! command -v fly >/dev/null 2>&1; then
        echo -e "${RED}✗ Error: flyctl CLI is not installed or not in PATH.${NC}"
        return 1
    fi
    FLY_BIN="$(command -v flyctl || command -v fly)"
    cd "$SCRIPT_DIR"
    $FLY_BIN deploy
    echo -e "${GREEN}✓ Fly.io deployment completed!${NC}"
}

deploy_both() {
    deploy_to_server
    deploy_to_fly
}

# Parse CLI arguments
TARGET="$1"

case "$TARGET" in
    server|--server|-s)
        deploy_to_server
        exit 0
        ;;
    fly|--fly|-f)
        deploy_to_fly
        exit 0
        ;;
    all|both|--all|-a)
        deploy_both
        exit 0
        ;;
    help|--help|-h)
        echo "Usage: $0 [server|fly|all]"
        echo ""
        echo "Options:"
        echo "  server    Deploy to VPS Server (Docker container on port 8080)"
        echo "  fly       Deploy to Fly.io via flyctl"
        echo "  all       Deploy to both VPS Server and Fly.io"
        exit 0
        ;;
esac

# Interactive prompt if no argument passed
if [ -t 0 ]; then
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}                 Trading API Deployment Selector                      ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "Select deployment target:"
    echo -e "  ${BOLD}1)${NC} ${GREEN}VPS Server${NC} [Default]"
    echo -e "  ${BOLD}2)${NC} ${YELLOW}Fly.io (flyctl)${NC}"
    echo -e "  ${BOLD}3)${NC} ${CYAN}Both (VPS Server + Fly.io)${NC}"
    echo -e "  ${BOLD}4)${NC} Cancel"
    echo ""
    read -t 10 -p "Enter choice [1-4] (default: 1 in 10s): " choice || choice=1
    echo ""

    case "$choice" in
        1|"")
            deploy_to_server
            ;;
        2)
            deploy_to_fly
            ;;
        3)
            deploy_both
            ;;
        4)
            echo "Deployment cancelled."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option selected.${NC}"
            exit 1
            ;;
    esac
else
    # Default to server when running non-interactively
    deploy_to_server
fi
