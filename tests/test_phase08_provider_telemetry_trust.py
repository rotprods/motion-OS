import pytest

from src.avatar.heygen_adapter import ingest_render_telemetry, validate_provider_result


def test_nan_nonfinite_and_boolean_duration_fail_closed():
    for value in (float("nan"), float("inf"), float("-inf"), "nan", "inf", True, False):
        errors = validate_provider_result({"status": "completed", "duration": value})
        assert any("duration" in error for error in errors)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/video.mp4",
        "file:///tmp/video.mp4",
        "https://localhost/video.mp4",
        "https://api.localhost/video.mp4",
        "https://127.0.0.1/video.mp4",
        "https://10.0.0.1/video.mp4",
        "https://192.168.1.10/video.mp4",
        "https://169.254.169.254/latest/meta-data/",
        "https://[::1]/video.mp4",
        "https://host.local/video.mp4",
        "https://user:secret@example.com/video.mp4",
        "https://[::1/video.mp4",
        "https://example.com:99999/video.mp4",
    ],
)
def test_provider_asset_urls_reject_non_https_credentials_local_networks_and_malformed_urls(url):
    errors = validate_provider_result({"status": "completed", "video_url": url})
    assert any("video_url" in error for error in errors)


def test_public_https_provider_urls_remain_valid():
    errors = validate_provider_result({
        "status": "completed",
        "duration": 12.5,
        "id": "job_123",
        "video_url": "https://cdn.example.com/video.mp4",
        "thumbnail_url": "https://assets.example.org/thumb.jpg",
    })
    assert errors == []


def test_failure_message_cannot_persist_secret_like_material():
    payload = {
        "status": "failed",
        "failure_code": "provider_error",
        "failure_message": "upstream token sk-abcdefghijklmnopqrstuvwxyz0123456789 leaked",
    }
    errors = validate_provider_result(payload)
    assert any("secret-like" in error for error in errors)
    with pytest.raises(ValueError, match="secret-like"):
        ingest_render_telemetry({}, payload)


def test_failure_fields_are_bounded_and_structured():
    assert validate_provider_result({"status": "failed", "failure_code": "provider.timeout:v2", "failure_message": "temporary failure"}) == []
    assert any("failure_code" in error for error in validate_provider_result({"status": "failed", "failure_code": "bad code with spaces"}))
    assert any("failure_code" in error for error in validate_provider_result({"status": "failed", "failure_code": "x" * 129}))
    assert any("failure_message" in error for error in validate_provider_result({"status": "failed", "failure_message": "x" * 2001}))
    assert any("control" in error for error in validate_provider_result({"status": "failed", "failure_message": "bad\x00message"}))


def test_job_id_whitespace_and_controls_fail_closed():
    assert any("job id" in error for error in validate_provider_result({"status": "pending", "id": "   "}))
    assert any("job id" in error for error in validate_provider_result({"status": "pending", "id": "job\x00x"}))


def test_non_object_provider_telemetry_fails_closed():
    assert validate_provider_result(None) == ["provider telemetry must be an object"]
    assert validate_provider_result(["completed"]) == ["provider telemetry must be an object"]


def test_ingest_preserves_only_validated_provider_fields():
    manifest = {"render": {"status": "pending"}}
    payload = {
        "status": "completed",
        "duration": 7.25,
        "id": "job_7",
        "video_url": "https://cdn.example.com/video.mp4",
        "thumbnail_url": "https://cdn.example.com/thumb.jpg",
    }
    out = ingest_render_telemetry(manifest, payload)
    assert out["render"]["status"] == "completed"
    assert out["render"]["provider_job_id"] == "job_7"
    assert out["render"]["actual_duration_s"] == 7.25
    assert out["render"]["asset_ref"] == "https://cdn.example.com/video.mp4"
