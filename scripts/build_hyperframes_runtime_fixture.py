from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.compilers.hyperframes import (
    build_hyperframes_render_contract,
    compile_editing_graph_to_hyperframes,
    emit_hyperframes_project,
)
from src.graph.model import Edge, MotionGraph, Node

OUT = ROOT / "runtime" / "hyperframes"
EVIDENCE = OUT / "compiler_evidence.json"


def fixture_graph() -> MotionGraph:
    nodes = [
        Node("scene-runtime", "Scene", {"data": {"start_ms": 0, "end_ms": 3000}}),
        Node("runtime-bg", "Layer", {"data": {
            "layer_class": "ENVIRONMENT", "z": 0, "text": "MOTION.OS",
            "entry": {"at_ms": 120, "duration_ms": 450, "ease": "power2.out", "channels": {"opacity": 0.72}},
        }}),
        Node("runtime-hero", "Layer", {"data": {
            "layer_class": "SUBJECT", "z": 3, "attention_role": "primary", "text": "HYPERFRAMES",
            "entry": {"at_ms": 220, "duration_ms": 650, "ease": "power3.out", "channels": {"scale": 1.06}},
            "settle": {"at_ms": 1200, "duration_ms": 700, "ease": "power2.inOut", "channels": {"x": 32}},
        }}),
        Node("runtime-type", "Layer", {"data": {
            "layer_class": "TYPOGRAPHY", "z": 6, "text": "PHYSICAL RUNTIME PROOF",
            "entry": {"at_ms": 500, "duration_ms": 550, "ease": "expo.out", "channels": {"y": -24}},
        }}),
    ]
    edges = [
        Edge("scene-runtime", "runtime-bg", "CONTAINS"),
        Edge("scene-runtime", "runtime-hero", "CONTAINS"),
        Edge("scene-runtime", "runtime-type", "CONTAINS"),
    ]
    return MotionGraph(nodes, edges)


def main() -> int:
    spec = compile_editing_graph_to_hyperframes(fixture_graph(), width=640, height=360, fps=30)
    if spec.duration_ms != 3000:
        raise SystemExit(f"unexpected fixture duration: {spec.duration_ms}")
    files = emit_hyperframes_project(spec)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")

    contract = build_hyperframes_render_contract(spec, output="out/runtime-local.mp4")
    evidence = {
        "schema": "motion-os.hyperframes-compiler-evidence/v1",
        "source": "scripts/build_hyperframes_runtime_fixture.py",
        "compiler": "src.compilers.hyperframes.compile_editing_graph_to_hyperframes",
        "emitter": "src.compilers.hyperframes.emit_hyperframes_project",
        "spec_sha256": spec.content_hash(),
        "emitted_sha256": {
            name: hashlib.sha256(content.encode("utf-8")).hexdigest()
            for name, content in sorted(files.items())
        },
        "render_contract": contract,
        "scene_count": len(spec.scenes),
        "event_count": len(spec.timeline),
        "authority": "deterministic_compiler_fixture",
        "creative_authority": "none",
    }
    EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
