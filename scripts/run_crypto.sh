#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
    PYTHON="$(command -v python3)"
fi
cd "$SCRIPT_DIR"
$PYTHON "$SCRIPT_DIR/fetch_potential_cryptos.py"
$PYTHON "$SCRIPT_DIR/rrg_crypto_chart.py"