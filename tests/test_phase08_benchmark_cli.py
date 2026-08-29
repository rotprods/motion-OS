from pathlib import Path
import json
import subprocess
import sys


def test_benchmark_cli_generate_runs_as_direct_script():
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "scripts/benchmark_smoke_batch.py", "generate"],
        cwd=root,
        check=True,
    )
    manifest = root / ".artifacts" / "benchmark-smoke" / "fixture_manifest.json"
    payload = json.loads(manifest.read_text())
    assert len(payload) == 5
    assert len({row["brief_id"] for row in payload}) == 5
