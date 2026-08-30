from src.benchmarks.fixtures import STYLE_FAMILIES, fixture_by_id, fixture_manifest, smoke_fixtures


def test_smoke_batch_contains_five_unique_style_families():
    fixtures = smoke_fixtures()
    assert len(fixtures) == 5
    assert tuple(f.style_family for f in fixtures) == STYLE_FAMILIES
    assert len({f.brief_id for f in fixtures}) == 5


def test_every_fixture_is_three_seconds_at_30fps():
    for fixture in smoke_fixtures():
        project = fixture.runtime_spec["project"]
        assert project == {"fps": 30, "width": 640, "height": 360, "duration_frames": 90}
        assert sum(scene["durationInFrames"] for scene in fixture.runtime_spec["scenes"]) == 90
        assert fixture.runtime_spec["scenes"][0]["from"] == 0
        assert fixture.runtime_spec["scenes"][-1]["from"] == 60


def test_fixture_manifest_is_deterministic_and_hash_bound():
    a = fixture_manifest()
    b = fixture_manifest(reversed(smoke_fixtures()))
    assert a == fixture_manifest()
    assert {x["brief_id"] for x in a} == {x["brief_id"] for x in b}
    for row in a:
        assert len(row["brief_sha256"]) == 64
        assert len(row["runtime_spec_sha256"]) == 64


def test_fixture_lookup_fails_for_unknown_id():
    try:
        fixture_by_id("does-not-exist")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown fixture must fail closed")
