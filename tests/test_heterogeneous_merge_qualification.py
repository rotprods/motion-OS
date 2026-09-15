from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MERGE_GATE = ROOT / ".github/workflows/merge-gate.yml"
HETEROGENEOUS = ROOT / ".github/workflows/heterogeneous-master-runtime.yml"
LOTTIE_RENDERER = ROOT / "scripts/render_lottie_sequence.mjs"
EXACT_HEAD_GATE = ROOT / "scripts/require_exact_head_workflow.py"


def test_merge_safe_requires_exact_head_heterogeneous_success():
    text = MERGE_GATE.read_text(encoding="utf-8")
    gate = text.split("\n  merge-safe:\n", 1)[1]
    assert "Require exact-head heterogeneous physical proof" in gate
    assert "scripts/require_exact_head_workflow.py" in gate
    assert "--workflow heterogeneous-master-runtime.yml" in gate
    assert 'TARGET_HEAD_SHA: ${{ github.event.pull_request.head.sha || github.sha }}' in gate
    assert 'TARGET_EVENT: ${{ github.event_name }}' in gate
    assert "actions: read" in text
    assert "Required to read exact-head workflow conclusions" in text


def test_heterogeneous_proof_runs_for_every_merge_candidate():
    text = HETEROGENEOUS.read_text(encoding="utf-8")
    trigger = text.split("\npermissions:\n", 1)[0]
    assert "pull_request:" in trigger
    assert "merge_group:" in trigger
    assert "paths:" not in trigger
    assert "b81982198d78cbca24d937c1acbf91d629c89f242b5d38952958f29a91a518fd" in text
    assert "3f7f0cb629b1edaa9dc043f2ebd36cc4e3933b7d65585105f0ef3d4716e6baa3" in text
    assert "npm ci --prefix runtime/heterogeneous-tools" in text
    assert "npm audit --prefix runtime/heterogeneous-tools --audit-level=high --omit=dev" in text


def test_lottie_renderer_resolves_puppeteer_from_installed_hyperframes_context():
    text = LOTTIE_RENDERER.read_text(encoding="utf-8")
    assert "node_modules','hyperframes','package.json" in text
    assert "createRequire(hyperframesPackage)" in text
    assert "toolRequire.resolve('hyperframes')" not in text
    assert "hyperframesRequire.resolve('puppeteer-core')" in text


def test_lottie_file_server_uses_path_aware_containment_not_prefix_matching():
    text = LOTTIE_RENDERER.read_text(encoding="utf-8")
    assert "path.relative(source,p)" in text
    assert "path.isAbsolute(contained)" in text
    assert "contained.startsWith(`..${path.sep}`)" in text
    assert "p.startsWith(source)" not in text


def test_exact_head_gate_is_bounded_and_fail_closed():
    text = EXACT_HEAD_GATE.read_text(encoding="utf-8")
    assert 'ALLOWED_EVENTS = {"pull_request", "merge_group"}' in text
    assert 'run.get("head_sha") == head' in text
    assert 'run.get("event") == event' in text
    assert 'conclusion == "success"' in text
    assert 'timeout_waiting_for_exact_head_success' in text
    assert "time.monotonic()" in text
