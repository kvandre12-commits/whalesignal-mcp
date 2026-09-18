#!/usr/bin/env bash
# WhaleSignal guided demo tour (runs entirely on synthetic demo data - no API key).
#
#   ./scripts/demo.sh
#
# Assumes you've created the venv and installed requirements. If not:
#   python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] && . .venv/bin/activate || true

hr() { printf '\n\033[36m== %s ==\033[0m\n' "$1"; }

hr "1) Single-ticker conviction (fused signals + rationale)"
python -m whalesignal.cli NVDA --demo

hr "2) Rank a watchlist (heatmap-ready, best first)"
python -m whalesignal.cli NVDA AAPL TSLA AMZN MSFT META AMD GOOG --demo

hr "3) One-call written market briefing"
python -m whalesignal.cli --brief --demo

hr "4) Also available"
cat <<'EOF'
  * MCP server : python -m whalesignal.server            (WHALESIGNAL_DEMO=1 for demo)
  * Web heatmap: python -m whalesignal.web --demo        (http://127.0.0.1:8000)
  * Tests      : python tests/test_signals.py  (+ demo_pipeline / briefing / web)
EOF
