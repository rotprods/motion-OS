#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOTION_REPO="${MOTION_REPO:-$ROOT_DIR}"
AVE_REPO="${AVE_REPO:-$(cd "$ROOT_DIR/../ave" 2>/dev/null && pwd || true)}"
ARTIFACT_DIR="${SEMANTIC_ARTIFACT_DIR:-$ROOT_DIR/artifacts/semantic-corpus-qualification}"
DATASET="${SEMANTIC_DATASET:-$MOTION_REPO/benchmarks/semantic_retrieval_v1.json}"
export OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
export OLLAMA_EMBED_MODEL="${OLLAMA_EMBED_MODEL:-bge-m3}"
export QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
export QDRANT_COLLECTION="${QDRANT_COLLECTION:-ave_motion_semantic_v1}"
export SEMANTIC_BATCH_SIZE="${SEMANTIC_BATCH_SIZE:-16}"
export COS_ROUTE_MULTIPLIER="${COS_ROUTE_MULTIPLIER:-32}"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
for cmd in git python curl; do command -v "$cmd" >/dev/null || fail "missing required command: $cmd"; done
[[ -n "$AVE_REPO" && -d "$AVE_REPO/.git" ]] || fail "AVE_REPO must point to a git checkout (default expects ../ave)"
[[ -d "$MOTION_REPO/.git" ]] || fail "MOTION_REPO must point to a git checkout"
[[ -f "$AVE_REPO/.semantic-index.json" ]] || fail "AVE semantic manifest missing: $AVE_REPO/.semantic-index.json"
[[ -f "$MOTION_REPO/.semantic-index.json" ]] || fail "Motion semantic manifest missing: $MOTION_REPO/.semantic-index.json"
[[ -f "$DATASET" ]] || fail "retrieval dataset missing: $DATASET"
mkdir -p "$ARTIFACT_DIR"

AVE_SHA="$(git -C "$AVE_REPO" rev-parse HEAD)"
MOTION_SHA="$(git -C "$MOTION_REPO" rev-parse HEAD)"
printf '{"ave_sha":"%s","motion_sha":"%s","collection":"%s"}\n' "$AVE_SHA" "$MOTION_SHA" "$QDRANT_COLLECTION" > "$ARTIFACT_DIR/source-heads.json"

echo '== Preflight labeled retrieval targets =='
AVE_REPO="$AVE_REPO" MOTION_REPO="$MOTION_REPO" DATASET="$DATASET" ARTIFACT_DIR="$ARTIFACT_DIR" python - <<'PY'
import fnmatch, json, os
from pathlib import Path

roots = {
    "rotprods/ave": Path(os.environ["AVE_REPO"]),
    "rotprods/motion-OS": Path(os.environ["MOTION_REPO"]),
}
dataset = json.loads(Path(os.environ["DATASET"]).read_text(encoding="utf-8"))
files = {}
for repo, root in roots.items():
    files[repo] = [
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    ]
missing = []
for case in dataset["cases"]:
    for target in case["expected"]:
        repo, pattern = target["repo"], target["path_glob"]
        matches = [p for p in files.get(repo, []) if fnmatch.fnmatch(p, pattern)]
        if not matches:
            missing.append({"case": case["id"], "repo": repo, "path_glob": pattern})
report = {
    "dataset": dataset.get("name"),
    "case_count": len(dataset["cases"]),
    "missing_target_count": len(missing),
    "missing_targets": missing,
    "passed": len(dataset["cases"]) >= 25 and not missing,
}
out = Path(os.environ["ARTIFACT_DIR"]) / "preflight.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if not report["passed"]:
    raise SystemExit("semantic ground-truth preflight failed")
PY

if [[ "${SEMANTIC_SKIP_BOOTSTRAP:-0}" != "1" ]]; then
  echo '== Bootstrap local Ollama + Qdrant =='
  bash "$MOTION_REPO/scripts/bootstrap_semantic_plane.sh"
fi

echo '== Doctor =='
(
  cd "$MOTION_REPO"
  python -m src.semantic_index doctor | tee "$ARTIFACT_DIR/doctor.json"
)

echo '== Index full AVE + MOTION corpus =='
(
  cd "$MOTION_REPO"
  python -m src.semantic_index index --repo "$AVE_REPO" --repo "$MOTION_REPO" | tee "$ARTIFACT_DIR/index.json"
)

echo '== Graphify cross-repository corpus =='
(
  cd "$MOTION_REPO"
  python -m src.semantic_index graphify \
    --repo-id rotprods/ave \
    --repo-id rotprods/motion-OS \
    --neighbors 8 \
    --min-score 0.15 \
    | tee "$ARTIFACT_DIR/graphify.json"
)

echo '== Evaluate labeled real-corpus retrieval =='
(
  cd "$MOTION_REPO"
  python -m src.semantic_index evaluate --dataset "$DATASET" | tee "$ARTIFACT_DIR/evaluation.json"
)

echo '== Live latency/throughput benchmark =='
(
  cd "$MOTION_REPO"
  python -m src.semantic_index benchmark --live --iterations "${SEMANTIC_BENCH_ITERATIONS:-8}" | tee "$ARTIFACT_DIR/benchmark.json"
)

echo '== Create portable Qdrant snapshot =='
ARTIFACT_DIR="$ARTIFACT_DIR" python - <<'PY'
import hashlib, json, os, urllib.request
from pathlib import Path

root = Path(os.environ["ARTIFACT_DIR"])
base = os.environ["QDRANT_URL"].rstrip("/")
collection = os.environ["QDRANT_COLLECTION"]
req = urllib.request.Request(
    f"{base}/collections/{collection}/snapshots?wait=true",
    data=b"",
    headers={"content-type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=600) as response:
    created = json.loads(response.read().decode())
result = created.get("result") or {}
name = result.get("name")
if not name:
    raise SystemExit(f"Qdrant snapshot creation failed: {created}")
with urllib.request.urlopen(f"{base}/collections/{collection}/snapshots/{name}", timeout=600) as response:
    data = response.read()
path = root / name
path.write_bytes(data)
meta = {
    "collection": collection,
    "snapshot": result,
    "downloaded_bytes": len(data),
    "sha256": hashlib.sha256(data).hexdigest(),
}
(root / "snapshot.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print(json.dumps(meta, indent=2))
PY

echo '== Assert qualification =='
ARTIFACT_DIR="$ARTIFACT_DIR" python - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ["ARTIFACT_DIR"])
load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
preflight = load("preflight.json")
doctor = load("doctor.json")
index = load("index.json")
graphify = load("graphify.json")
evaluation = load("evaluation.json")
benchmark = load("benchmark.json")
snapshot = load("snapshot.json")
assert preflight["passed"] is True and preflight["case_count"] >= 25, preflight
assert doctor["ok"] is True and doctor["ollama"]["probe_dims"] == 1024, doctor
reports = {r["repo"]: r for r in index["reports"]}
for repo in ("rotprods/ave", "rotprods/motion-OS"):
    assert repo in reports and reports[repo]["chunks"] > 0 and reports[repo]["upserted"] > 0, reports
assert graphify["graphify_version"] == "graphify-v4-qdrant-prefetch-rerank", graphify
assert graphify["vector_payload_transfer"] == "none", graphify
assert graphify["nodes_updated"] > 0 and graphify["edges"] > 0 and graphify["cross_repo_edges"] > 0, graphify
assert evaluation["passed"] is True and evaluation["case_count"] >= 25, evaluation
assert benchmark["passed"] is True and benchmark["live"]["passed"] is True, benchmark
assert snapshot["downloaded_bytes"] > 0, snapshot
snap = root / snapshot["snapshot"]["name"]
assert snap.is_file() and snap.stat().st_size == snapshot["downloaded_bytes"]
print("FULL_SEMANTIC_CORPUS_QUALIFICATION=PASS")
PY

printf '\nSemantic corpus qualification PASS\nArtifacts: %s\nAVE: %s\nMOTION: %s\n' "$ARTIFACT_DIR" "$AVE_SHA" "$MOTION_SHA"
