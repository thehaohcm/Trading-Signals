#!/usr/bin/env bash

# ==============================================================================
#  Trading Signals - Master Unified Deployment Script
#  Deploy everything (Web UI, API, Python Scripts, 24/7 Daemon, Cronjobs)
#  Driven by DEPLOY_HOST in .env for seamless migration to any server.
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

# Load environment configuration (root .env takes priority)
if [ -f "$SCRIPT_DIR/.env" ]; then
    load_env "$SCRIPT_DIR/.env"
fi
if [ -f "$SCRIPT_DIR/trading_api/.env" ]; then
    load_env "$SCRIPT_DIR/trading_api/.env"
fi

if [ -z "$DEPLOY_HOST" ]; then
    echo -e "${RED}✗ Error: DEPLOY_HOST is not set. Please configure it in .env file.${NC}"
    exit 1
fi

deploy_api() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[1/3] Deploying Trading API (Go Backend)...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/trading_api/deploy_server.sh"
}

deploy_web() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[2/3] Deploying Web UI (Vue.js + Nginx on Port 80 & 3000)...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/deploy_web.sh"
}

deploy_scripts() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[3/3] Deploying Python Scripts, 24/7 Alert Daemon & Cronjobs...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/scripts/deploy_scripts_to_vps.sh"
}

deploy_all() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}       🚀 Starting FULL UNIFIED DEPLOYMENT to $DEPLOY_HOST        ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    deploy_api
    deploy_web
    deploy_scripts

    echo -e "\n${GREEN}======================================================================${NC}"
    echo -e "${GREEN}${BOLD}🎉 ALL SERVICES DEPLOYED & CONSOLIDATED ON $DEPLOY_HOST!${NC}"
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "  • Web UI (SPA)         : ${BOLD}http://$DEPLOY_HOST/${NC} or ${BOLD}http://$DEPLOY_HOST:3000/${NC}"
    echo -e "  • Trading API          : ${BOLD}http://$DEPLOY_HOST:8080/health${NC}"
    echo -e "  • Ntfy Push Service    : ${BOLD}http://$DEPLOY_HOST:8088/${NC}"
    echo -e "  • PostgreSQL Database  : ${BOLD}$DEPLOY_HOST:5432 (DB: thehaohcm_trading_signal_db)${NC}"
    echo -e "  • 24/7 Alert Daemon    : ${BOLD}Active (systemctl status trading-alert)${NC}"
    echo -e "  • Scheduled Cronjobs   : ${BOLD}Installed for user $DEPLOY_USER (crontab -l)${NC}"
    echo -e "${GREEN}======================================================================${NC}\n"
}

deploy_fly() {
    echo -e "\n${CYAN}>>> Deploying Trading API to Fly.io...${NC}"
    cd "$SCRIPT_DIR/trading_api"
    flyctl deploy
}

deploy_vercel() {
    echo -e "\n${CYAN}>>> Deploying Web UI to Vercel...${NC}"
    cd "$SCRIPT_DIR"
    vercel --prod
}

# Parse CLI arguments
TARGET="$1"

case "$TARGET" in
    all|--all|-a)
        deploy_all
        exit 0
        ;;
    api|--api)
        deploy_api
        exit 0
        ;;
    web|--web)
        deploy_web
        exit 0
        ;;
    scripts|--scripts)
        deploy_scripts
        exit 0
        ;;
    fly|--fly)
        deploy_fly
        exit 0
        ;;
    vercel|--vercel)
        deploy_vercel
        exit 0
        ;;
    help|--help|-h)
        echo "Usage: $0 [all|web|api|scripts|fly|vercel]"
        echo ""
        echo "Targets:"
        echo "  all       Deploy EVERYTHING to VPS ($DEPLOY_HOST): API + Web UI + Scripts + Daemon + Cronjobs"
        echo "  web       Deploy only Web UI (builds dist and runs Nginx on port 80 & 3000)"
        echo "  api       Deploy only Trading API Go backend (port 8080)"
        echo "  scripts   Deploy Python scripts, start 24/7 alert daemon, and install cronjobs"
        echo "  fly       Deploy Trading API to Fly.io"
        echo "  vercel    Deploy Web UI to Vercel"
        exit 0
        ;;
esac

# Interactive prompt if no argument passed
if [ -t 0 ]; then
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}       Trading Signals Unified Server Deployment ($DEPLOY_HOST)      ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "Select what you want to deploy:"
    echo -e "  ${BOLD}1)${NC} ${GREEN}${BOLD}ALL: Everything to VPS ($DEPLOY_HOST)${NC} [Default]"
    echo -e "  ${BOLD}2)${NC} ${CYAN}Web UI only (Vue.js + Nginx on port 80)${NC}"
    echo -e "  ${BOLD}3)${NC} ${CYAN}Trading API only (Go backend on port 8080)${NC}"
    echo -e "  ${BOLD}4)${NC} ${CYAN}Python Scripts only (24/7 alert daemon + cronjobs)${NC}"
    echo -e "  ${BOLD}5)${NC} ${YELLOW}Fly.io (API)${NC}"
    echo -e "  ${BOLD}6)${NC} ${YELLOW}Vercel (Web UI)${NC}"
    echo -e "  ${BOLD}7)${NC} Cancel"
    echo ""
    read -t 10 -p "Enter choice [1-7] (default: 1 in 10s): " choice || choice=1
    echo ""

    case "$choice" in
        1|"")
            deploy_all
            ;;
        2)
            deploy_web
            ;;
        3)
            deploy_api
            ;;
        4)
            deploy_scripts
            ;;
        5)
            deploy_fly
            ;;
        6)
            deploy_vercel
            ;;
        7)
            echo "Deployment cancelled."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option selected.${NC}"
            exit 1
            ;;
    esac
else
    # Default to deploy_all when running non-interactively
    deploy_all
fi
