from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.extraction.pipeline import AnalysisConfig, analyze_video
from src.extraction.benchmark import GroundTruth, benchmark_feature_pack, save_benchmark


def main() -> int:
    p = argparse.ArgumentParser(description="MOTION.OS real video analysis pipeline")
    p.add_argument("video")
    p.add_argument("--out", required=True)
    p.add_argument("--shot-threshold", type=float, default=None)
    p.add_argument("--analysis-width", type=int, default=640)
    p.add_argument("--ocr-every", type=int, default=15)
    p.add_argument("--flow-stride", type=int, default=2)
    p.add_argument("--transcript", choices=["none", "whisper"], default="none")
    p.add_argument("--whisper-model", default="tiny")
    p.add_argument("--keep-frames", action="store_true")
    p.add_argument("--ground-truth", help="Optional JSON with fps,total_frames,shot_boundaries,dominant_colors,text_strings,motion_direction")
    args = p.parse_args()
    cfg = AnalysisConfig(
        shot_threshold=args.shot_threshold,
        analysis_width=args.analysis_width,
        ocr_every_n=args.ocr_every,
        optical_flow_stride=args.flow_stride,
        transcript_provider=args.transcript,
        whisper_model=args.whisper_model,
        keep_frames=args.keep_frames,
    )
    result = analyze_video(args.video, args.out, config=cfg)
    if args.ground_truth:
        raw = json.loads(Path(args.ground_truth).read_text(encoding="utf-8"))
        truth = GroundTruth(
            fps=float(raw["fps"]),
            total_frames=int(raw["total_frames"]),
            shot_boundaries=tuple(int(x) for x in raw.get("shot_boundaries", [])),
            dominant_colors=tuple(raw.get("dominant_colors", [])),
            text_strings=tuple(raw.get("text_strings", [])),
            motion_direction=raw.get("motion_direction"),
        )
        report = benchmark_feature_pack(result["feature_pack"], truth)
        save_benchmark(report, Path(args.out) / "ground_truth_benchmark.json")
    print(json.dumps(result["manifest"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
