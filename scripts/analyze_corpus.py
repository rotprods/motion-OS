from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.extraction.pipeline import AnalysisConfig, analyze_video
from src.knowledge.style_signature import canonical_style_family, evidence_coverage, feature_pack_style_vector
from src.knowledge.style_store import connect, upsert_style_signature, retrieve_similar

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def _source_id(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return f"{path.stem}:{digest}"


def analyze_corpus(input_dir: str | Path, output_dir: str | Path, *, db_path: str | Path, config: AnalysisConfig | None = None) -> dict[str, Any]:
    src = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    videos = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)
    conn = connect(db_path)
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for index, video in enumerate(videos, start=1):
        sid = _source_id(video)
        item_out = out / f"{index:03d}_{video.stem}"
        try:
            result = analyze_video(video, item_out, config=config or AnalysisConfig())
            pack = result["feature_pack"]
            motionstyle = result["motionstyle"]
            vector = feature_pack_style_vector(pack)
            coverage = evidence_coverage(pack)
            family = canonical_style_family(motionstyle)
            signature_id = f"style:{sid}"
            payload = {
                "source": str(video),
                "analysis_dir": str(item_out),
                "style_system": motionstyle.get("style_system", {}),
                "quality": motionstyle.get("quality", {}),
                "manifest": result["manifest"],
            }
            upsert_style_signature(
                conn,
                signature_id=signature_id,
                source_id=sid,
                style_family=family,
                payload=payload,
                vector=vector,
                evidence_coverage=coverage,
            )
            rows.append({
                "source_id": sid,
                "path": str(video),
                "style_family": family,
                "evidence_coverage": coverage,
                "vector": vector,
                "warnings": result["manifest"].get("warnings", []),
                "analysis_dir": str(item_out),
            })
        except Exception as exc:
            failures.append({"path": str(video), "error": f"{type(exc).__name__}:{exc}"})

    # Inspectability benchmark: each analyzed source should retrieve itself first when queried by its own measured vector.
    self_top1 = 0
    retrieval_rows = []
    for row in rows:
        neighbors = retrieve_similar(conn, row["vector"], limit=min(5, max(1, len(rows))))
        top = neighbors[0]["source_id"] if neighbors else None
        if top == row["source_id"]:
            self_top1 += 1
        retrieval_rows.append({
            "source_id": row["source_id"],
            "top_neighbors": [
                {"source_id": n["source_id"], "style_family": n["style_family"], "similarity": n["similarity"], "evidence_coverage": n["evidence_coverage"]}
                for n in neighbors
            ],
        })
    summary = {
        "schema": "motion-os.corpus-analysis/v1",
        "input_dir": str(src),
        "video_count": len(videos),
        "analyzed_count": len(rows),
        "failure_count": len(failures),
        "style_family_counts": {},
        "mean_evidence_coverage": round(sum(r["evidence_coverage"] for r in rows) / len(rows), 6) if rows else 0.0,
        "retrieval_self_top1_rate": round(self_top1 / len(rows), 6) if rows else 0.0,
        "note": "self-top1 is a deterministic sanity check, not evidence that semantic visual retrieval is good; corpus labels/human relevance judgments are still required",
        "items": rows,
        "retrieval": retrieval_rows,
        "failures": failures,
    }
    for row in rows:
        fam = row["style_family"]
        summary["style_family_counts"][fam] = summary["style_family_counts"].get(fam, 0) + 1
    (out / "corpus_report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze a video corpus into evidence-bound MOTION.OS style signatures")
    p.add_argument("input_dir")
    p.add_argument("--out", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--analysis-width", type=int, default=640)
    p.add_argument("--ocr-every", type=int, default=20)
    p.add_argument("--flow-stride", type=int, default=3)
    p.add_argument("--transcript", choices=["none", "whisper"], default="none")
    args = p.parse_args()
    report = analyze_corpus(
        args.input_dir,
        args.out,
        db_path=args.db,
        config=AnalysisConfig(
            analysis_width=args.analysis_width,
            ocr_every_n=args.ocr_every,
            optical_flow_stride=args.flow_stride,
            transcript_provider=args.transcript,
        ),
    )
    print(json.dumps({k: report[k] for k in ("video_count", "analyzed_count", "failure_count", "style_family_counts", "mean_evidence_coverage", "retrieval_self_top1_rate")}, indent=2))
    return 0 if report["failure_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
