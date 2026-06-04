#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE_NAME="${LEXMAPA_PROCESSOR_IMAGE:-lexmapa/legal-remote-processor:local-ocr}"
INSTALL_OCR="${INSTALL_OCR:-true}"
REBUILD="${REBUILD:-0}"
MODE="${1:-worker}"

wait_for_docker() {
  if docker info >/dev/null 2>&1; then
    return 0
  fi

  if [ "$(uname -s)" = "Darwin" ] && command -v open >/dev/null 2>&1; then
    echo "Docker is not running. Starting Docker Desktop..."
    open -a Docker || true
  elif command -v systemctl >/dev/null 2>&1; then
    echo "Docker is not running. Trying to start Docker service..."
    sudo -n systemctl start docker >/dev/null 2>&1 || true
  fi

  for _ in $(seq 1 60); do
    if docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 3
  done

  echo "Docker is installed but did not respond in time." >&2
  exit 1
}

if [ ! -f .env ]; then
  echo ".env does not exist. Run ./scripts/setup.sh and configure credentials." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is missing. Run ./scripts/setup.sh." >&2
  exit 1
fi

wait_for_docker

if [ "$REBUILD" = "1" ] || ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "Image $IMAGE_NAME not found or rebuild requested. Building..."
  LEXMAPA_PROCESSOR_IMAGE="$IMAGE_NAME" INSTALL_OCR="$INSTALL_OCR" ./scripts/build-image.sh
fi

export LEXMAPA_PROCESSOR_IMAGE="$IMAGE_NAME"
export INSTALL_OCR

case "$MODE" in
  once)
    docker compose run --rm processor python -m processor.main once
    ;;
  worker)
    docker compose up -d processor
    echo "Processor started with image $IMAGE_NAME."
    echo "Ops: https://lexmapa.linqorait.com/ops"
    ;;
  *)
    echo "Usage: ./scripts/run.sh [worker|once]" >&2
    exit 2
    ;;
esac
