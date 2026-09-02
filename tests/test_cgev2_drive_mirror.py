from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "state/cgev2/death_resilience_drive_mirror_2026-09-01.json"


def test_cgev2_drive_mirror_is_durable_pointer_not_authority():
    payload = json.loads(MIRROR.read_text(encoding="utf-8"))
    drive = payload["google_drive"]
    assert payload["schema"] == "motion-os.cgev2-drive-mirror/v2"
    assert payload["authority"] == "DURABLE_RECOVERY_MIRROR_NOT_PROJECT_TRUTH"
    assert payload["project_done"] is False
    assert payload["source_pr"] == 127
    assert len(payload["source_authority_anchor_fingerprint_sha256"]) == 64
    assert drive["upload_status"] == "SUCCEEDED"
    assert drive["file_id"] == "external-gdrive:file:1udVfyb6IS6KgfaxXu78knGQqYvcN-r8J"
    assert drive["directory_id"] == "external-gdrive:folder:1EeF_juiXk8rmMrUHhN0HBPy1m2NhDOyb"
    assert drive["directory_name"] == "00_AGENT_HANDOFF"
    assert drive["destination_path"].startswith("/Google Drive/00_AGENT_HANDOFF/")
    assert drive["content_sha256"] == "967d35487e592412880dc2077f3c006b0456cdb5a22c9761e36f6ccaa1deeaa4"
    assert drive["content_bytes"] == 4333
    assert "refresh live main" in payload["required_bootstrap"]
