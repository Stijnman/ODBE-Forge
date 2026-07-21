#!/usr/bin/env bash
# Optional helper: install ODBE-Forge deps in a venv (not Home Assistant-specific).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
echo "ODBE-Forge ready. Activate with: source $ROOT/.venv/bin/activate"
