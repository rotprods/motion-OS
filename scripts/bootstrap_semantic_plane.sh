#!/usr/bin/env bash
set -euo pipefail

MODEL="${OLLAMA_EMBED_MODEL:-bge-m3}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
COMPOSE_FILE="${SEMANTIC_COMPOSE_FILE:-compose.semantic.yml}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama is required. On macOS with Homebrew: brew install ollama" >&2
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run the pinned local Qdrant service." >&2
  exit 1
fi

if ! curl -fsS --max-time 2 "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  log_file="${TMPDIR:-/tmp}/motion-ollama.log"
  echo "Starting local Ollama service; log: ${log_file}"
  nohup ollama serve >"${log_file}" 2>&1 &
  for _ in $(seq 1 30); do
    if curl -fsS --max-time 2 "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

curl -fsS --max-time 2 "${OLLAMA_URL}/api/tags" >/dev/null
ollama pull "${MODEL}"
docker compose -f "${COMPOSE_FILE}" up -d

for _ in $(seq 1 30); do
  if curl -fsS --max-time 2 http://127.0.0.1:6333/collections >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

python -m src.semantic_index doctor
