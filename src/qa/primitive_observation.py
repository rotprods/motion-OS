from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import hashlib
import json
import tempfile

from src.extraction.providers import (
    change_scores_from_records,
    extract_frames_ffmpeg,
    fx_material_heuristics,
    ocr_tesseract,
    optical_flow_opencv,
)
from src.renderers.runtime_verifier import probe_media
from src.qa.primitive_fixture_runner import FixtureSpec


@dataclass(frozen=True)
class PrimitiveObservationPack:
    schema: str
    fixture_id: str
    fixture_sha256: str
    primitive_id: str
    renderer: str
    artifact_sha256: str
    media: dict[str, Any]
    frame_evidence: tuple[dict[str, Any], ...]
    frame_change: dict[str, Any]
    optical_flow: dict[str, Any]
    ocr: dict[str, Any]
    fx: dict[str, Any]
    materials: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        return asdict(self)

    def content_hash(self) -> str:
        raw = json.dumps(self.payload(), sort_keys=True, separators=(',', ':')).encode()
        return hashlib.sha256(raw).hexdigest()


def _change_summary(scores: list[float]) -> dict[str, Any]:
    if not scores:
        return {
            'authority': 'measured',
            'pairs': 0,
            'mean': 0.0,
            'max': 0.0,
            'active_pair_ratio': 0.0,
        }
    active = sum(score >= 0.01 for score in scores)
    return {
        'authority': 'measured',
        'pairs': len(scores),
        'mean': round(sum(scores) / len(scores), 6),
        'max': round(max(scores), 6),
        'active_pair_ratio': round(active / len(scores), 6),
    }


def observe_fixture_artifact(
    spec: FixtureSpec,
    artifact_path: str | Path,
    *,
    sample_fps: float = 15.0,
    scale_width: int = 540,
    ocr_every_n: int = 15,
) -> PrimitiveObservationPack:
    path = Path(artifact_path)
    media = probe_media(path)
    if media['sha256'] == spec.sha256():
        # Improbable but protects against confusing the fixture JSON identity with media identity.
        raise ValueError('artifact SHA must be distinct from fixture SHA')

    with tempfile.TemporaryDirectory(prefix='motion-os-primitive-observe-') as tmp:
        frames = extract_frames_ffmpeg(path, tmp, fps=sample_fps, scale_width=scale_width)
        changes = change_scores_from_records(frames)
        flow = optical_flow_opencv(frames)
        ocr = ocr_tesseract(frames, every_n=ocr_every_n)
        fx, materials = fx_material_heuristics(frames)
        frame_evidence = tuple({
            'frame': int(item['frame']),
            'sha256': item['sha256'],
        } for item in frames)

    return PrimitiveObservationPack(
        schema='motion-os.primitive-observation/v1',
        fixture_id=spec.fixture_id,
        fixture_sha256=spec.sha256(),
        primitive_id=spec.primitive_id,
        renderer=spec.renderer,
        artifact_sha256=media['sha256'],
        media={
            'codec': media.get('codec'),
            'width': media['width'],
            'height': media['height'],
            'fps': media['fps'],
            'frames': media['frames'],
            'duration_s': media['duration_s'],
            'bytes': media['bytes'],
        },
        frame_evidence=frame_evidence,
        frame_change=_change_summary(changes),
        optical_flow=flow,
        ocr=ocr,
        fx=fx,
        materials=materials,
    )


def verify_observation_binding(spec: FixtureSpec, pack: PrimitiveObservationPack, artifact_path: str | Path) -> tuple[bool, tuple[str, ...]]:
    findings: list[str] = []
    media = probe_media(artifact_path)
    if pack.fixture_id != spec.fixture_id or pack.fixture_sha256 != spec.sha256():
        findings.append('fixture_binding_mismatch')
    if pack.primitive_id != spec.primitive_id:
        findings.append('primitive_binding_mismatch')
    if pack.renderer != spec.renderer:
        findings.append('renderer_binding_mismatch')
    if pack.artifact_sha256 != media['sha256']:
        findings.append('artifact_binding_mismatch')
    if not pack.frame_evidence:
        findings.append('frame_evidence_missing')
    if pack.frame_change.get('authority') != 'measured':
        findings.append('frame_change_not_measured')
    return not findings, tuple(findings)
