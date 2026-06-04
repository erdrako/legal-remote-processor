#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker --version || true
ollama --version || echo "Ollama not found; deterministic mode can still run."
PYTHONPATH=src python -m processor.main doctor
docker compose ps || true
