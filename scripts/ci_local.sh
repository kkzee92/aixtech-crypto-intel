#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/make_fixtures.py
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m pytest --cov=crypto_intel --cov-fail-under=90
python scripts/check_pdpa.py
echo "local gates passed (gitleaks runs in GitHub Actions)"
