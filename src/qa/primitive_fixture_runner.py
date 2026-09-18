from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterable
import hashlib
import json

from src.primitives.registry import Primitive, build_registry
from src.qa.primitive_qualification import (
    PrimitiveEvidence,
    PrimitiveFixtureCase,
    PrimitiveQualificationError,
    PrimitiveQualificationLedger,
    build_fixture_matrix,
)
from src.renderers.runtime_verifier import probe_media, sha256_file


@dataclass(frozen=True)
class FixtureSpec:
    schema: str
    fixture_id: str
    primitive_id: str
    family: str
    renderer: str
    width: int
    height: int
    fps: int
    duration_s: float
    assertions: tuple[str, ...]
    primitive_contract: dict

    def canonical_payload(self) -> dict:
        payload = asdict(self)
        payload['assertions'] = list(self.assertions)
        return payload

    def canonical_json(self) -> str:
        return json.dumps(self.canonical_payload(), sort_keys=True, separators=(',', ':'))

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


@dataclass(frozen=True)
class IdentityVerification:
    passed: bool
    assertions: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.passed and not self.assertions:
            raise PrimitiveQualificationError('passing identity verification requires explicit assertions')
        if not self.passed and not self.findings:
            raise PrimitiveQualificationError('failing identity verification requires explicit findings')


@dataclass(frozen=True)
class FixtureExecutionResult:
    fixture: FixtureSpec
    evidence: PrimitiveEvidence
    artifact_path: str | None
    findings: tuple[str, ...]


RendererExecutor = Callable[[FixtureSpec, Path], str | Path | None]
ArtifactIdentityVerifier = Callable[[FixtureSpec, Path], IdentityVerification]


DEFAULT_ASSERTIONS = (
    'artifact_decodes',
    'resolution_matches_fixture',
    'frame_count_matches_global_clock',
    'visual_duration_matches_frame_count_over_fps',
)


def _primitive_map(registry: Iterable[Primitive]) -> dict[str, Primitive]:
    primitives = tuple(registry)
    by_id = {primitive.id: primitive for primitive in primitives}
    if len(by_id) != len(primitives):
        raise PrimitiveQualificationError('primitive registry IDs must be unique')
    return by_id


def fixture_spec(case: PrimitiveFixtureCase, registry: Iterable[Primitive] | None = None) -> FixtureSpec:
    primitives = tuple(registry or build_registry())
    primitive = _primitive_map(primitives).get(case.primitive_id)
    if primitive is None:
        raise PrimitiveQualificationError(f'unknown primitive_id: {case.primitive_id}')
    if case.renderer not in primitive.renderer_support:
        raise PrimitiveQualificationError(f'undeclared renderer {case.renderer} for {case.primitive_id}')
    expected_fixture_id = f'primitive:{case.primitive_id}:renderer:{case.renderer}:v1'
    if case.fixture_id != expected_fixture_id:
        raise PrimitiveQualificationError('non-canonical fixture case')
    contract = {
        'semantic_intents': list(primitive.semantic_intents),
        'attention_roles': list(primitive.attention_roles),
        'channels': list(primitive.channels),
        'physics_profile': primitive.physics_profile,
        'easing_presets': list(primitive.easing_presets),
        'forbidden_combinations': list(primitive.forbidden_combinations),
        'qa': primitive.qa,
    }
    return FixtureSpec(
        schema='motion-os.primitive-fixture/v1',
        fixture_id=case.fixture_id,
        primitive_id=case.primitive_id,
        family=case.family,
        renderer=case.renderer,
        width=1080,
        height=1920,
        fps=30,
        duration_s=2.0,
        assertions=DEFAULT_ASSERTIONS,
        primitive_contract=contract,
    )


def build_fixture_specs(registry: Iterable[Primitive] | None = None) -> tuple[FixtureSpec, ...]:
    primitives = tuple(registry or build_registry())
    return tuple(fixture_spec(case, primitives) for case in build_fixture_matrix(primitives))


def write_fixture_specs(out_dir: str | Path, registry: Iterable[Primitive] | None = None) -> tuple[Path, ...]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for spec in build_fixture_specs(registry):
        path = root / spec.renderer / f'{spec.primitive_id}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spec.canonical_payload(), indent=2, sort_keys=True), encoding='utf-8')
        paths.append(path)
    return tuple(paths)


def contract_evidence(spec: FixtureSpec, *, test_run_id: str, passed: bool = True, findings: tuple[str, ...] = ()) -> PrimitiveEvidence:
    assertions = ('fixture_schema_valid', 'primitive_contract_bound', 'renderer_declared') if passed else findings
    return PrimitiveEvidence(
        evidence_id=f'contract:{test_run_id}:{spec.primitive_id}:{spec.renderer}',
        primitive_id=spec.primitive_id,
        renderer=spec.renderer,
        fixture_id=spec.fixture_id,
        test_run_id=test_run_id,
        evidence_kind='CONTRACT',
        passed=passed,
        fixture_sha256=spec.sha256(),
        assertions=tuple(assertions),
    )


def execute_physical_fixture(
    spec: FixtureSpec,
    *,
    test_run_id: str,
    output_dir: str | Path,
    executor: RendererExecutor,
    identity_verifier: ArtifactIdentityVerifier | None = None,
) -> FixtureExecutionResult:
    root = Path(output_dir) / spec.renderer / spec.primitive_id
    root.mkdir(parents=True, exist_ok=True)
    findings: list[str] = []
    artifact_path: Path | None = None
    try:
        produced = executor(spec, root)
        if produced:
            artifact_path = Path(produced)
    except Exception as exc:
        findings.append(f'renderer_exception:{type(exc).__name__}:{exc}')

    if artifact_path is None or not artifact_path.exists():
        findings.append('artifact_missing')
        evidence = PrimitiveEvidence(
            evidence_id=f'physical:{test_run_id}:{spec.primitive_id}:{spec.renderer}',
            primitive_id=spec.primitive_id,
            renderer=spec.renderer,
            fixture_id=spec.fixture_id,
            test_run_id=test_run_id,
            evidence_kind='PHYSICAL_RENDER',
            passed=False,
            fixture_sha256=spec.sha256(),
            assertions=tuple(findings),
        )
        return FixtureExecutionResult(spec, evidence, None, tuple(findings))

    try:
        media = probe_media(artifact_path)
    except Exception as exc:
        findings.append(f'probe_failed:{type(exc).__name__}:{exc}')
        evidence = PrimitiveEvidence(
            evidence_id=f'physical:{test_run_id}:{spec.primitive_id}:{spec.renderer}',
            primitive_id=spec.primitive_id,
            renderer=spec.renderer,
            fixture_id=spec.fixture_id,
            test_run_id=test_run_id,
            evidence_kind='PHYSICAL_RENDER',
            passed=False,
            fixture_sha256=spec.sha256(),
            artifact_sha256=sha256_file(artifact_path),
            assertions=tuple(findings),
        )
        return FixtureExecutionResult(spec, evidence, str(artifact_path), tuple(findings))

    expected_frames = round(spec.duration_s * spec.fps)
    if media['width'] != spec.width or media['height'] != spec.height:
        findings.append('resolution_mismatch')
    if media['fps'] != f'{spec.fps}/1':
        findings.append('fps_mismatch')
    if media['frames'] != expected_frames:
        findings.append('frame_count_mismatch')

    identity_assertions: tuple[str, ...] = ()
    if identity_verifier is None:
        findings.append('primitive_identity_unverified')
    else:
        try:
            identity = identity_verifier(spec, artifact_path)
            if identity.passed:
                identity_assertions = identity.assertions
            else:
                findings.extend(identity.findings)
        except Exception as exc:
            findings.append(f'identity_verifier_exception:{type(exc).__name__}:{exc}')

    passed = not findings
    visual_duration_ms = round(media['frames'] / spec.fps * 1000) if media['frames'] > 0 else None
    success_assertions = tuple(spec.assertions) + tuple(identity_assertions)
    evidence = PrimitiveEvidence(
        evidence_id=f'physical:{test_run_id}:{spec.primitive_id}:{spec.renderer}',
        primitive_id=spec.primitive_id,
        renderer=spec.renderer,
        fixture_id=spec.fixture_id,
        test_run_id=test_run_id,
        evidence_kind='PHYSICAL_RENDER',
        passed=passed,
        fixture_sha256=spec.sha256(),
        artifact_sha256=media['sha256'],
        frame_count=media['frames'] if media['frames'] > 0 else None,
        fps=float(spec.fps) if media['frames'] > 0 else None,
        visual_duration_ms=visual_duration_ms,
        assertions=success_assertions if passed else tuple(findings),
    )
    return FixtureExecutionResult(spec, evidence, str(artifact_path), tuple(findings))


def qualification_plan() -> dict:
    specs = build_fixture_specs()
    renderers = sorted(set(spec.renderer for spec in specs))
    return {
        'schema': 'motion-os.primitive-qualification-plan/v1',
        'registered_primitives': len(set(spec.primitive_id for spec in specs)),
        'renderer_cases': len(specs),
        'renderers': renderers,
        'cases_by_renderer': {renderer: sum(spec.renderer == renderer for spec in specs) for renderer in renderers},
        'authority_rule': 'primitive PHYSICALLY_VERIFIED only when every declared renderer has passing physical evidence plus fixture-specific identity verification',
    }


def ledger_from_results(results: Iterable[FixtureExecutionResult]) -> PrimitiveQualificationLedger:
    return PrimitiveQualificationLedger(evidence=(result.evidence for result in results))
