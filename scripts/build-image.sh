#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE_NAME="${LEXMAPA_PROCESSOR_IMAGE:-lexmapa/legal-remote-processor:local-ocr}"
INSTALL_OCR="${INSTALL_OCR:-true}"
docker build --build-arg INSTALL_OCR="$INSTALL_OCR" -t "$IMAGE_NAME" .
