#!/usr/bin/env bash
set -euo pipefail

MODEL="${OLLAMA_EMBED_MODEL:-bge-m3}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
OLLAMA_IMAGE="${OLLAMA_DOCKER_IMAGE:-ollama/ollama:0.33.2}"
OLLAMA_CONTAINER="${OLLAMA_DOCKER_CONTAINER:-motion-semantic-ollama}"
OLLAMA_VOLUME="${OLLAMA_DOCKER_VOLUME:-motion_ollama_models}"
COMPOSE_FILE="${SEMANTIC_COMPOSE_FILE:-compose.semantic.yml}"

for cmd in curl docker python; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "$cmd is required for the semantic-plane bootstrap." >&2
    exit 1
  fi
done

wait_for_ollama() {
  for _ in $(seq 1 90); do
    if curl -fsS --max-time 2 "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Ollama did not become healthy at ${OLLAMA_URL}" >&2
  return 1
}

start_ollama_docker() {
  if [[ "${OLLAMA_URL}" != "http://127.0.0.1:11434" && "${OLLAMA_URL}" != "http://localhost:11434" ]]; then
    echo "Refusing to start a local Docker Ollama because OLLAMA_URL points elsewhere: ${OLLAMA_URL}" >&2
    return 1
  fi

  if docker container inspect "${OLLAMA_CONTAINER}" >/dev/null 2>&1; then
    current_image="$(docker container inspect -f '{{.Config.Image}}' "${OLLAMA_CONTAINER}")"
    if [[ "${current_image}" != "${OLLAMA_IMAGE}" ]]; then
      echo "Recreating ${OLLAMA_CONTAINER}: image ${current_image} != pinned ${OLLAMA_IMAGE}"
      docker rm -f "${OLLAMA_CONTAINER}" >/dev/null
    elif [[ "$(docker container inspect -f '{{.State.Running}}' "${OLLAMA_CONTAINER}")" != "true" ]]; then
      docker start "${OLLAMA_CONTAINER}" >/dev/null
      return 0
    else
      return 0
    fi
  fi

  docker pull "${OLLAMA_IMAGE}"
  docker run -d \
    --name "${OLLAMA_CONTAINER}" \
    --restart unless-stopped \
    -p 127.0.0.1:11434:11434 \
    -v "${OLLAMA_VOLUME}:/root/.ollama" \
    "${OLLAMA_IMAGE}" >/dev/null
}

if ! curl -fsS --max-time 2 "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  if command -v ollama >/dev/null 2>&1; then
    log_file="${TMPDIR:-/tmp}/motion-ollama.log"
    echo "Starting host Ollama service; log: ${log_file}"
    nohup ollama serve >"${log_file}" 2>&1 &
  else
    echo "Host Ollama CLI not found; starting pinned Docker Ollama ${OLLAMA_IMAGE}."
    start_ollama_docker
  fi
  wait_for_ollama
fi

# Pull through Ollama's HTTP API so host and Docker modes share one code path.
echo "Ensuring Ollama embedding model ${MODEL} is present."
pull_payload="$(python -c 'import json,sys; print(json.dumps({"name": sys.argv[1], "stream": False}))' "${MODEL}")"
curl -fsS --max-time 1800 \
  -H 'content-type: application/json' \
  -X POST "${OLLAMA_URL}/api/pull" \
  --data "${pull_payload}" >/dev/null

# Qdrant remains pinned and loopback-bound by compose.semantic.yml.
docker compose -f "${COMPOSE_FILE}" up -d

for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 http://127.0.0.1:6333/collections >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS --max-time 5 http://127.0.0.1:6333/collections >/dev/null

python -m src.semantic_index doctor
