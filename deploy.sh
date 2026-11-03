#!/usr/bin/env bash

# ==============================================================================
#  Trading Signals - Master Unified Deployment Script
#  Deploy everything to the VPS (API, OSINT AI Worker, Web UI, Python Scripts,
#  24/7 Daemon, Cronjobs). Driven by DEPLOY_HOST in .env so the whole stack can
#  be moved to any server by changing one variable.
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

print_usage() {
    echo "Usage: $0 [all|api|worker|web|scripts]"
    echo ""
    echo "Targets (all deploy to VPS $DEPLOY_HOST):"
    echo "  all       Deploy EVERYTHING theo thứ tự: API -> OSINT AI Worker -> Scripts/Daemon/Cronjobs -> Web UI (có chạy test trước; SKIP_TESTS=1 để bỏ qua)"
    echo "  api       Deploy only Trading API Go backend (port 8080)"
    echo "  worker    Deploy only OSINT AI Worker & NotebookLM worker (port 8081)"
    echo "  web       Deploy only Web UI (builds dist and runs Nginx on port 80 & 3000)"
    echo "  scripts   Deploy Python scripts, start 24/7 alert daemon, and install cronjobs"
}

# Chạy test trước khi deploy (bỏ qua bằng SKIP_TESTS=1). Chỉ chạy phần nào có công cụ trên máy.
run_preflight_tests() {
    if [ "${SKIP_TESTS:-0}" = "1" ]; then
        echo -e "${YELLOW}⚠ SKIP_TESTS=1 → bỏ qua test trước khi deploy.${NC}"
        return 0
    fi
    echo -e "\n${CYAN}${BOLD}[0/4] Chạy test trước khi deploy...${NC}"
    if command -v python3 >/dev/null 2>&1; then
        (cd "$SCRIPT_DIR/scripts" && python3 -m unittest discover -s tests) || { echo -e "${RED}✗ Test Python (scripts) thất bại — dừng deploy.${NC}"; exit 1; }
        (cd "$SCRIPT_DIR/osint_ai_worker" && python3 -m unittest discover -s tests) || { echo -e "${RED}✗ Test Python (worker) thất bại — dừng deploy.${NC}"; exit 1; }
    else
        echo -e "${YELLOW}⚠ Không có python3 → bỏ qua test Python.${NC}"
    fi
    if command -v go >/dev/null 2>&1; then
        (cd "$SCRIPT_DIR/trading_api" && go test ./...) || { echo -e "${RED}✗ Test Go thất bại — dừng deploy.${NC}"; exit 1; }
    else
        echo -e "${YELLOW}⚠ Không có Go → bỏ qua test Go.${NC}"
    fi
    echo -e "${GREEN}✓ Test OK${NC}"
}

# Đợi Go API lên (migration DB chạy lúc API khởi động) trước khi deploy các thành phần phụ thuộc. SKIP_HEALTHCHECK=1 để bỏ qua.
wait_for_api() {
    if [ "${SKIP_HEALTHCHECK:-0}" = "1" ]; then return 0; fi
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Không có curl → bỏ qua kiểm tra /health.${NC}"
        return 0
    fi
    echo -e "${CYAN}Đợi Trading API sẵn sàng (http://$DEPLOY_HOST:8080/health)...${NC}"
    for i in $(seq 1 30); do
        if curl -fsS --max-time 3 "http://$DEPLOY_HOST:8080/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Trading API đã chạy (migration DB đã áp dụng).${NC}"
            return 0
        fi
        sleep 2
    done
    echo -e "${RED}✗ Trading API không phản hồi /health sau 60s — dừng để tránh deploy worker/script lệch schema DB.${NC}"
    echo -e "${YELLOW}  Xem log: docker logs trading_api. Bỏ qua kiểm tra: SKIP_HEALTHCHECK=1${NC}"
    exit 1
}

deploy_api() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[1/4] Deploying Trading API (Go Backend)...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/trading_api/deploy.sh"
}

deploy_worker() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[2/4] Deploying OSINT AI Worker (Python Worker on Port 8081)...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/osint_ai_worker/deploy.sh"
}

deploy_web() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[4/4] Deploying Web UI (Vue.js + Nginx on Port 80 & 3000)...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/deploy_web.sh"
}

deploy_scripts() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}[3/4] Deploying Python Scripts, 24/7 Alert Daemon & Cronjobs...${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    bash "$SCRIPT_DIR/scripts/deploy.sh"
}

deploy_all() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}${BOLD}       🚀 Starting FULL UNIFIED DEPLOYMENT to $DEPLOY_HOST        ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    # THỨ TỰ BẮT BUỘC: API (chạy migration DB) -> Worker AI -> Scripts (alert.py) -> Web (frontend + nginx)
    run_preflight_tests
    deploy_api
    wait_for_api
    deploy_worker
    deploy_scripts
    deploy_web

    echo -e "\n${GREEN}======================================================================${NC}"
    echo -e "${GREEN}${BOLD}🎉 ALL SERVICES DEPLOYED & CONSOLIDATED ON $DEPLOY_HOST!${NC}"
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "  • Web UI (SPA)         : ${BOLD}http://$DEPLOY_HOST/${NC} or ${BOLD}http://$DEPLOY_HOST:3000/${NC}"
    echo -e "  • Trading API          : ${BOLD}http://$DEPLOY_HOST:8080/health${NC}"
    echo -e "  • OSINT AI Worker      : ${BOLD}Port 8081 (internal trigger server)${NC}"
    echo -e "  • Ntfy Push Service    : ${BOLD}http://$DEPLOY_HOST:8088/${NC}"
    echo -e "  • PostgreSQL Database  : ${BOLD}$DEPLOY_HOST:5432 (DB: thehaohcm_trading_signal_db)${NC}"
    echo -e "  • 24/7 Alert Daemon    : ${BOLD}Active (systemctl status trading-alert)${NC}"
    echo -e "  • Scheduled Cronjobs   : ${BOLD}Installed for user $DEPLOY_USER (crontab -l)${NC}"
    echo -e "${GREEN}======================================================================${NC}\n"
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
    worker|--worker)
        deploy_worker
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
    help|--help|-h)
        print_usage
        exit 0
        ;;
    "")
        ;;
    *)
        echo -e "${RED}✗ Unknown target: $TARGET${NC}"
        print_usage
        exit 1
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
    echo -e "  ${BOLD}4)${NC} ${CYAN}OSINT AI Worker only (Python worker on port 8081)${NC}"
    echo -e "  ${BOLD}5)${NC} ${CYAN}Python Scripts only (24/7 alert daemon + cronjobs)${NC}"
    echo -e "  ${BOLD}6)${NC} Cancel"
    echo ""
    read -t 10 -p "Enter choice [1-6] (default: 1 in 10s): " choice || choice=1
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
            deploy_worker
            ;;
        5)
            deploy_scripts
            ;;
        6)
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
