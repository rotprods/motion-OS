from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.extraction.pipeline import AnalysisConfig, analyze_video
from src.reverse_engineering import (
    compile_editing_template,
    validate_editing_template,
    write_reverse_engineering_bundle,
)


MODE_MAP = {
    "exact": "RECONSTRUCT_EXACT",
    "structural": "STRUCTURAL_TEMPLATE",
    "style": "STYLE_TRANSFER",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MOTION.OS evidence-bound video reverse engineering + reusable editing template compiler"
    )
    parser.add_argument("video", help="Reference video to analyze")
    parser.add_argument("--out", required=True, help="Output ReverseEngineeringBundle directory")
    parser.add_argument("--mode", choices=sorted(MODE_MAP), default="structural")
    parser.add_argument("--template-id", default=None)
    parser.add_argument("--shot-threshold", type=float, default=None)
    parser.add_argument("--analysis-width", type=int, default=640)
    parser.add_argument("--ocr-every", type=int, default=15)
    parser.add_argument("--flow-stride", type=int, default=1, help="Use 1 for the densest measured frame-pair motion timeline")
    parser.add_argument("--transcript", choices=["none", "whisper"], default="none")
    parser.add_argument("--whisper-model", default="tiny")
    parser.add_argument("--keep-frames", action="store_true")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    analysis_dir = out / "analysis"
    cfg = AnalysisConfig(
        shot_threshold=args.shot_threshold,
        analysis_width=args.analysis_width,
        ocr_every_n=args.ocr_every,
        optical_flow_stride=args.flow_stride,
        transcript_provider=args.transcript,
        whisper_model=args.whisper_model,
        keep_frames=args.keep_frames,
    )
    analysis = analyze_video(args.video, analysis_dir, config=cfg)
    mode = MODE_MAP[args.mode]
    template, frame_timeline = compile_editing_template(
        analysis["feature_pack"],
        analysis["motionstyle"],
        replication_mode=mode,
        template_id=args.template_id,
        frame_timeline_ref="frame_timeline.json",
    )
    validate_editing_template(template)
    artifacts = write_reverse_engineering_bundle(out, template, frame_timeline)

    manifest = {
        "schema_version": "1.0.0",
        "source": str(Path(args.video)),
        "source_sha256": template["source"]["sha256"],
        "replication_mode": mode,
        "template_id": template["template_id"],
        "template_content_hash": template["content_hash"],
        "frame_count": template["frame_contract"]["total_frames"],
        "frame_coverage": template["qa"]["frame_coverage"],
        "analysis_manifest": "analysis/analysis_manifest.json",
        "artifacts": {
            "feature_pack": "analysis/feature_pack.json",
            "motionstyle": "analysis/motionstyle2json.json",
            "remotion_scene_spec": "analysis/remotion_scene_spec.json",
            "motion_spec_typescript": "analysis/motionSpec.ts",
            "editing_template": Path(artifacts["editing_template"]).name,
            "frame_timeline": Path(artifacts["frame_timeline"]).name,
        },
        "authority": {
            "physical_measurements": "provider_defined",
            "editing_signature": "deterministic_from_evidence",
            "template_generalization": "IMPLEMENTED_NOT_EMPIRICALLY_QUALIFIED",
        },
        "warnings": template["evidence"]["warnings"] + template["qa"]["warnings"],
    }
    (out / "reverse_engineering_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
