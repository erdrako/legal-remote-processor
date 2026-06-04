#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo ".env not found."; exit 1; }
docker compose up -d processor
