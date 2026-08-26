from src.extraction.segmentation import detect_shots_from_change_scores, validate_shot_coverage, plan_keyframes


def test_shot_detection_is_complete_non_overlapping():
    scores = [0.02] * 29
    scores[9] = 0.9
    scores[19] = 0.8
    shots = detect_shots_from_change_scores(scores, fps=10, threshold=0.4, min_shot_frames=3)
    assert [(s.start_frame, s.end_frame) for s in shots] == [(0, 10), (10, 20), (20, 30)]
    assert validate_shot_coverage(shots, 30) == []
    assert shots[1].start_ms == 1000


def test_keyframe_plan_start_mid_end_plus_adaptive():
    shot = detect_shots_from_change_scores([0.01] * 9, fps=10)[0]
    assert plan_keyframes(shot) == [0, 4, 9]
    assert plan_keyframes(shot, include_adaptive=True, motion_peak_frame=7) == [0, 4, 7, 9]
