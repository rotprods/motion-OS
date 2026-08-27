from src.coordination.evidence import EvidenceArtifact, EvidenceManifest


def artifact(revision="r1", digest="a" * 64):
    return EvidenceArtifact(
        artifact_id="motion://artifact/demo",
        provider="gdrive",
        provider_file_id="file-1",
        revision=revision,
        sha256=digest,
        mime_type="application/pdf",
    )


def test_manifest_is_deterministic_and_revision_pinned():
    first = EvidenceManifest.build([artifact()])
    second = EvidenceManifest.build([artifact()])
    assert first.manifest_hash == second.manifest_hash
    assert first.verify_hash()
    assert first.source_refs()[0].revision == "r1"


def test_revision_or_content_change_is_detected():
    first = EvidenceManifest.build([artifact()])
    revised = EvidenceManifest.build([artifact(revision="r2", digest="b" * 64)])
    assert revised.changed_since(first) == ("motion://artifact/demo",)
    assert revised.manifest_hash != first.manifest_hash


def test_duplicate_artifact_identity_fails_closed():
    try:
        EvidenceManifest.build([artifact(), artifact()])
    except ValueError as exc:
        assert "duplicate artifact_id" in str(exc)
    else:
        raise AssertionError("expected duplicate artifact rejection")
