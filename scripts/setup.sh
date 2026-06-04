#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE_NAME="${LEXMAPA_PROCESSOR_IMAGE:-lexmapa/legal-remote-processor:local-ocr}"
INSTALL_DEPENDENCIES="${INSTALL_DEPENDENCIES:-0}"
ENABLE_OLLAMA="${ENABLE_OLLAMA:-0}"
SKIP_IMAGE_BUILD="${SKIP_IMAGE_BUILD:-0}"

set_env_value() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" .env 2>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    sed "s|^${key}=.*|${key}=${value}|" .env > "$tmp"
    mv "$tmp" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

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

if command -v python3 >/dev/null 2>&1; then
  PYTHONPATH=src python3 -m processor.main preflight
elif command -v python >/dev/null 2>&1; then
  PYTHONPATH=src python -m processor.main preflight
else
  echo "Python is missing; skipping processor preflight. Docker build can still run." >&2
fi

if [ ! -f .env ]; then
  cp .env.example .env
fi
set_env_value "LEXMAPA_PROCESSOR_IMAGE" "$IMAGE_NAME"

if ! command -v docker >/dev/null 2>&1; then
  if [ "$INSTALL_DEPENDENCIES" != "1" ]; then
    echo "Docker is missing. Install Docker or rerun with INSTALL_DEPENDENCIES=1." >&2
    exit 1
  fi

  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose-plugin
  elif command -v brew >/dev/null 2>&1; then
    brew install --cask docker
  else
    echo "Automatic Docker installation is not supported on this OS." >&2
    exit 1
  fi
fi

if [ "$ENABLE_OLLAMA" = "1" ]; then
  set_env_value "PROCESSOR_ENABLE_OLLAMA" "true"
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama is not installed. Install it manually for IA-assisted mode." >&2
  fi
fi

wait_for_docker

if [ "$SKIP_IMAGE_BUILD" != "1" ]; then
  LEXMAPA_PROCESSOR_IMAGE="$IMAGE_NAME" INSTALL_OCR=true ./scripts/build-image.sh
fi

echo "Initial setup completed."
echo "Next: configure .env credentials, then run ./scripts/run.sh"
