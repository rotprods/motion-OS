from src.coordination.recovery_bundle import RecoveryBundleCompiler, RecoverySource


H = "a" * 64
H2 = "b" * 64


def build_bundle():
    return RecoveryBundleCompiler().compile(
        project_id="motion://project/MOTION.OS",
        main_sha="abcdef1234567890",
        event_watermark=42,
        state_hash=H,
        coordination_graph_hash=H2,
        unified_graph_hash=H,
        cos_bundle_hash=H2,
        context_pack_sha256=H,
        sources=(
            RecoverySource("github://rotprods/motion-OS/main", "abcdef1234567890", H),
            RecoverySource("event://watermark/42", "42", H2),
        ),
    )


def test_recovery_bundle_is_sealed_and_deterministic():
    a = build_bundle()
    b = build_bundle()
    assert a.verify()
    assert a == b
    assert a.bundle_sha256 == b.bundle_sha256


def test_recovery_bundle_detects_missing_revision_and_hash_drift_fail_closed():
    bundle = build_bundle()
    findings = bundle.validate_current_sources({
        "github://rotprods/motion-OS/main": ("different", H2),
    })
    assert "MISSING:event://watermark/42" in findings
    assert "REVISION_DRIFT:github://rotprods/motion-OS/main" in findings
    assert "HASH_DRIFT:github://rotprods/motion-OS/main" in findings


def test_optional_recovery_source_may_be_absent_without_blocking_recovery():
    bundle = RecoveryBundleCompiler().compile(
        project_id="motion://project/MOTION.OS",
        main_sha="abcdef1234567890",
        event_watermark=1,
        state_hash=H,
        coordination_graph_hash=H,
        unified_graph_hash=H,
        cos_bundle_hash=H,
        context_pack_sha256=H,
        sources=(RecoverySource("drive://evidence", "r1", H, required=False),),
    )
    assert bundle.validate_current_sources({}) == ()


def test_duplicate_source_uri_is_rejected():
    compiler = RecoveryBundleCompiler()
    try:
        compiler.compile(
            project_id="motion://project/MOTION.OS",
            main_sha="abcdef1234567890",
            event_watermark=1,
            state_hash=H,
            coordination_graph_hash=H,
            unified_graph_hash=H,
            cos_bundle_hash=H,
            context_pack_sha256=H,
            sources=(RecoverySource("github://x", "r1", H), RecoverySource("github://x", "r2", H2)),
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
