"""Upstream content intelligence and avatar-script contracts for MOTION.OS."""

from .avatar_script_engine import (
    ValidationIssue,
    apply_pronunciation_overrides,
    assert_manifest,
    build_avatar_request,
    deserialize_manifest,
    estimate_duration_s,
    get_profile,
    ingest_render_telemetry,
    load_profiles,
    schema_validate,
    serialize_manifest,
    validate_manifest,
    word_count,
)

__all__ = [
    "ValidationIssue",
    "apply_pronunciation_overrides",
    "assert_manifest",
    "build_avatar_request",
    "deserialize_manifest",
    "estimate_duration_s",
    "get_profile",
    "ingest_render_telemetry",
    "load_profiles",
    "schema_validate",
    "serialize_manifest",
    "validate_manifest",
    "word_count",
]
