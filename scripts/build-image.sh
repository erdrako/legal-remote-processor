#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
INSTALL_OCR="${INSTALL_OCR:-false}"
docker build --build-arg INSTALL_OCR="$INSTALL_OCR" -t lexmapa-remote-processor:local .
