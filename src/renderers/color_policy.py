from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping
import hashlib
import json


_ALLOWED_PRIMARIES = {"bt709", "smpte432"}
_ALLOWED_TRANSFERS = {"bt709", "iec61966-2-1"}
_ALLOWED_MATRICES = {"bt709", "rgb"}
_ALLOWED_RANGES = {"limited", "full"}


@dataclass(frozen=True)
class ColorProfile:
    profile_id: str
    primaries: str
    transfer: str
    matrix: str
    range: str
    hdr: bool = False
    evidence: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("color profile requires profile_id")
        if self.primaries not in _ALLOWED_PRIMARIES:
            raise ValueError(f"unsupported_primaries:{self.primaries}")
        if self.transfer not in _ALLOWED_TRANSFERS:
            raise ValueError(f"unsupported_transfer:{self.transfer}")
        if self.matrix not in _ALLOWED_MATRICES:
            raise ValueError(f"unsupported_matrix:{self.matrix}")
        if self.range not in _ALLOWED_RANGES:
            raise ValueError(f"unsupported_range:{self.range}")
        if not self.evidence:
            raise ValueError(f"missing_color_evidence:{self.profile_id}")


BT709_SDR_LIMITED = ColorProfile(
    profile_id="bt709_sdr_limited",
    primaries="bt709",
    transfer="bt709",
    matrix="bt709",
    range="limited",
    evidence=("canonical_working_space",),
)

SRGB_FULL = ColorProfile(
    profile_id="srgb_full",
    primaries="bt709",
    transfer="iec61966-2-1",
    matrix="rgb",
    range="full",
    evidence=("declared_browser_ui_space",),
)

DISPLAY_P3_SRGB_FULL = ColorProfile(
    profile_id="display_p3_srgb_full",
    primaries="smpte432",
    transfer="iec61966-2-1",
    matrix="rgb",
    range="full",
    evidence=("declared_display_p3_space",),
)


@dataclass(frozen=True)
class ArtifactColorBinding:
    artifact_id: str
    source: ColorProfile
    preserve_alpha: bool = False

    def validate(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact color binding requires artifact_id")
        self.source.validate()


@dataclass(frozen=True)
class ColorNormalizationPlan:
    target: ColorProfile
    bindings: tuple[ArtifactColorBinding, ...]
    backend: str
    tone_map_policy: str
    authority: str
    plan_hash: str


def _canonical_payload(*, target: ColorProfile, bindings: tuple[ArtifactColorBinding, ...], backend: str, tone_map_policy: str, authority: str) -> dict[str, Any]:
    return {
        "target": asdict(target),
        "bindings": [
            {
                "artifact_id": binding.artifact_id,
                "source": asdict(binding.source),
                "preserve_alpha": binding.preserve_alpha,
            }
            for binding in sorted(bindings, key=lambda item: item.artifact_id)
        ],
        "backend": backend,
        "tone_map_policy": tone_map_policy,
        "authority": authority,
    }


def build_color_normalization_plan(
    artifact_ids: list[str] | tuple[str, ...],
    source_profiles: Mapping[str, ColorProfile],
    *,
    alpha_artifacts: set[str] | frozenset[str] = frozenset(),
    target: ColorProfile = BT709_SDR_LIMITED,
    backend: str = "zscale",
    tone_map_policy: str = "reject_hdr",
) -> ColorNormalizationPlan:
    if not artifact_ids:
        raise ValueError("no_artifacts")
    if len(set(artifact_ids)) != len(artifact_ids):
        raise ValueError("duplicate_artifact_id")
    if backend != "zscale":
        raise ValueError(f"unsupported_color_backend:{backend}")
    if tone_map_policy != "reject_hdr":
        raise ValueError(f"unsupported_tone_map_policy:{tone_map_policy}")
    target.validate()
    if target.hdr:
        raise ValueError("hdr_target_not_supported")

    extra_profiles = set(source_profiles) - set(artifact_ids)
    if extra_profiles:
        raise ValueError("unbound_color_profiles:" + ",".join(sorted(extra_profiles)))

    bindings: list[ArtifactColorBinding] = []
    for artifact_id in artifact_ids:
        profile = source_profiles.get(artifact_id)
        if profile is None:
            raise ValueError(f"missing_color_profile:{artifact_id}")
        profile.validate()
        if profile.hdr:
            raise ValueError(f"hdr_requires_explicit_tone_map:{artifact_id}")
        binding = ArtifactColorBinding(
            artifact_id=artifact_id,
            source=profile,
            preserve_alpha=artifact_id in alpha_artifacts,
        )
        binding.validate()
        bindings.append(binding)

    authority = "contract_verified"
    payload = _canonical_payload(
        target=target,
        bindings=tuple(bindings),
        backend=backend,
        tone_map_policy=tone_map_policy,
        authority=authority,
    )
    plan_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return ColorNormalizationPlan(
        target=target,
        bindings=tuple(sorted(bindings, key=lambda item: item.artifact_id)),
        backend=backend,
        tone_map_policy=tone_map_policy,
        authority=authority,
        plan_hash=plan_hash,
    )


def ffmpeg_color_filter(binding: ArtifactColorBinding, target: ColorProfile, *, input_label: str, output_label: str) -> str:
    binding.validate()
    target.validate()
    source = binding.source
    if source.hdr or target.hdr:
        raise ValueError("hdr_color_conversion_not_qualified")
    if not input_label or not output_label:
        raise ValueError("color filter requires labels")

    zscale = (
        "zscale="
        f"primariesin={source.primaries}:transferin={source.transfer}:"
        f"matrixin={source.matrix}:rangein={source.range}:"
        f"primaries={target.primaries}:transfer={target.transfer}:"
        f"matrix={target.matrix}:range={target.range}"
    )
    pixel_format = "yuva444p10le" if binding.preserve_alpha else "yuv444p10le"
    return f"[{input_label}]{zscale},format={pixel_format}[{output_label}]"


def ffmpeg_output_color_args(target: ColorProfile = BT709_SDR_LIMITED) -> list[str]:
    target.validate()
    if target.hdr:
        raise ValueError("hdr_output_not_qualified")
    range_token = "tv" if target.range == "limited" else "pc"
    return [
        "-color_primaries", target.primaries,
        "-color_trc", target.transfer,
        "-colorspace", target.matrix,
        "-color_range", range_token,
    ]


def validate_color_plan(plan: ColorNormalizationPlan, artifact_ids: list[str] | tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    expected = set(artifact_ids)
    actual = {binding.artifact_id for binding in plan.bindings}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            errors.append("missing_bindings:" + ",".join(missing))
        if extra:
            errors.append("extra_bindings:" + ",".join(extra))
    try:
        plan.target.validate()
        for binding in plan.bindings:
            binding.validate()
    except ValueError as exc:
        errors.append(str(exc))

    payload = _canonical_payload(
        target=plan.target,
        bindings=plan.bindings,
        backend=plan.backend,
        tone_map_policy=plan.tone_map_policy,
        authority=plan.authority,
    )
    observed_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if observed_hash != plan.plan_hash:
        errors.append("plan_hash_mismatch")
    return errors
