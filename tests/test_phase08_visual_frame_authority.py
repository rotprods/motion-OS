from types import SimpleNamespace

import pytest

from scripts import assemble_heterogeneous_master as master


def test_counted_frames_are_preferred_and_must_agree_with_container_count():
    assert master.authoritative_frame_count({"nb_read_frames": "90", "nb_frames": "90"}) == 90
    assert master.authoritative_frame_count({"nb_read_frames": "90"}) == 90
    assert master.authoritative_frame_count({"nb_frames": "90"}) == 90
    with pytest.raises(ValueError, match="disagrees"):
        master.authoritative_frame_count({"nb_read_frames": "90", "nb_frames": "89"})


@pytest.mark.parametrize(
    "stream",
    [
        {},
        {"nb_read_frames": None, "nb_frames": None},
        {"nb_read_frames": "N/A"},
        {"nb_read_frames": "0"},
        {"nb_read_frames": "-1"},
        {"nb_read_frames": "90.0"},
        {"nb_read_frames": True},
        {"nb_frames": "garbage"},
        {"nb_frames": "090"},
    ],
)
def test_missing_or_non_exact_frame_authority_fails_closed(stream):
    with pytest.raises(ValueError):
        master.authoritative_frame_count(stream)


def test_probe_requests_real_decoded_frame_count(monkeypatch, tmp_path):
    observed = {}

    def fake_run(args, **kwargs):
        observed["args"] = list(args)
        return SimpleNamespace(stdout='{"streams": [], "format": {}}')

    monkeypatch.setattr(master.subprocess, "run", fake_run)
    master.probe(tmp_path / "artifact.mp4")
    assert "-count_frames" in observed["args"]
    assert "-show_streams" in observed["args"]


def test_mux_duration_is_not_a_substitute_for_missing_frames():
    # A perfectly plausible container duration does not create visual authority.
    stream = {"avg_frame_rate": "30/1"}
    with pytest.raises(ValueError, match="frame evidence missing"):
        master.authoritative_frame_count(stream)
