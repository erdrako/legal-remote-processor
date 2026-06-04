#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHONPATH=src python -m processor.main preflight

if [ ! -f .env ]; then
  cp .env.example .env
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is missing. Install Docker Engine, then rerun this script." >&2
  exit 1
fi

./scripts/build-image.sh
echo "Bootstrap completed. Run scripts/enroll-local.ps1 on Windows or configure .env manually on Linux."
