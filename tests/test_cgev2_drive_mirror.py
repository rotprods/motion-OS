from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "state/cgev2/death_resilience_drive_mirror_2026-09-01.json"


def test_cgev2_drive_mirror_is_durable_pointer_not_authority():
    payload = json.loads(MIRROR.read_text(encoding="utf-8"))
    drive = payload["google_drive"]
    assert payload["authority"] == "DURABLE_RECOVERY_MIRROR_NOT_PROJECT_TRUTH"
    assert payload["project_done"] is False
    assert payload["source_pr"] == 127
    assert payload["source_snapshot_fingerprint_sha256"] == "123651820c2976de8e266fcbb56c1c3cabb0da7878d14e86cc37d16a5c50bc99"
    assert drive["upload_status"] == "SUCCEEDED"
    assert drive["file_id"].startswith("external-gdrive:file:")
    assert drive["directory_id"].startswith("external-gdrive:folder:")
    assert drive["destination_path"].startswith("/Google Drive/08_INFRA_BACKUPS_EXPORTS/")
    assert "VERIFY LIVE TRUTH" not in payload.get("authority", "")
    assert "refresh live main" in payload["required_bootstrap"]
