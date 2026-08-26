from pathlib import Path

from PIL import Image, ImageDraw

from src.extraction.providers import frame_change_score, change_scores_from_records, fx_material_heuristics, track_ocr_blocks
from src.extraction.segmentation import detect_shots_from_change_scores
from src.extraction.benchmark import GroundTruth, benchmark_feature_pack, shot_boundary_metrics


def _save(path: Path, color: tuple[int,int,int], *, square_x: int | None = None) -> dict:
    im = Image.new("RGB", (320, 180), color)
    if square_x is not None:
        d = ImageDraw.Draw(im)
        d.rectangle((square_x, 65, square_x + 35, 100), fill=(245,245,245))
    im.save(path)
    import hashlib
    return {"frame": int(path.stem), "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def test_frame_change_detects_real_cut(tmp_path: Path):
    a = Image.new("RGB", (320,180), (18,18,18))
    b = Image.new("RGB", (320,180), (18,18,18))
    c = Image.new("RGB", (320,180), (235,235,230))
    assert frame_change_score(a,b) < 0.01
    assert frame_change_score(a,c) > 0.35


def test_change_scores_feed_contiguous_shots(tmp_path: Path):
    records=[]
    for i in range(12):
        records.append(_save(tmp_path / f"{i}.png", (15,15,15) if i < 6 else (235,230,220)))
    scores=change_scores_from_records(records)
    shots=detect_shots_from_change_scores(scores, fps=30, threshold=0.30, min_shot_frames=2)
    assert len(shots) == 2
    assert shots[0].end_frame == 6
    assert shots[1].start_frame == 6
    assert shots[-1].end_frame == 12


def test_ocr_tracker_persists_id_for_same_text():
    blocks=[
        {"id":"a","frame":1,"text":"HELLO","bbox":[.1,.1,.2,.1]},
        {"id":"b","frame":10,"text":"HELLO","bbox":[.105,.1,.2,.1]},
        {"id":"c","frame":70,"text":"HELLO","bbox":[.8,.8,.1,.1]},
    ]
    out=track_ocr_blocks(blocks,max_frame_gap=20)
    assert out[0]["continuity_id"] == out[1]["continuity_id"]
    assert out[2]["continuity_id"] != out[1]["continuity_id"]


def test_fx_heuristic_is_evidence_bound(tmp_path: Path):
    records=[]
    for i in range(5):
        records.append(_save(tmp_path / f"{i}.png", (230,230,230), square_x=25+i*4))
    fx, assets=fx_material_heuristics(records,sample_count=5)
    assert fx["authority"] == "measured_heuristic"
    assert all("frame" in m for m in fx["measurements"])
    assert assets["authority"] == "inferred_from_measured_pixels"


def test_ground_truth_report_does_not_hide_boundary_errors():
    m=shot_boundary_metrics([30,60],[31,88],tolerance_frames=2)
    assert m["tp"] == 1
    assert m["fp"] == 1
    assert m["fn"] == 1
    assert m["f1"] == 0.5


def test_benchmark_keeps_vertical_metrics_separate():
    pack={
        "shots":[{"start_frame":0},{"start_frame":30},{"start_frame":60}],
        "color_stats":{"palette":[{"hex":"#101010"}]},
        "ocr":[{"text":"HELLO"}],
        "keyframes":[{"id":"k1"}],
        "warnings":[],
    }
    truth=GroundTruth(fps=30,total_frames=90,shot_boundaries=(30,60),dominant_colors=("#101010",),text_strings=("HELLO",))
    report=benchmark_feature_pack(pack,truth)
    assert report["shot_detection"]["f1"] == 1.0
    assert report["colors"]["mean_rgb_distance"] == 0.0
    assert report["ocr"]["exact_or_containment_recall"] == 1.0
    assert "score" not in report
    assert report["promotion_authority"] == "ground_truth_measurement"
