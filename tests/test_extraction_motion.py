from src.extraction.motion import analyze_trajectory, separate_camera_local_motion


def test_motion_direction_and_easing():
    track = analyze_trajectory([(0,0),(0.1,0),(0.35,0),(0.7,0),(0.9,0),(1.0,0)], fps=30)
    assert track.direction == "left_to_right"
    assert track.displacement == 1.0
    assert track.easing_guess in {"ease_in_out", "other"}


def test_camera_local_separation():
    assert separate_camera_local_motion([(2,0),(2,0)], [(0.2,0),(0.1,0)])["classification"] == "camera_dominant"
    assert separate_camera_local_motion([(0.1,0)], [(2,0),(2,0)])["classification"] == "object_dominant"
