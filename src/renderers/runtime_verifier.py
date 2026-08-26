from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import IntEnum
from pathlib import Path
from typing import Any
import hashlib
import json
import shutil
import subprocess


class RuntimeAuthority(IntEnum):
    UNAVAILABLE = 0
    CONTRACT_ONLY = 1
    COMPILER_READY = 2
    RENDERER_EXECUTED = 3
    AUTHORITATIVE = 4


@dataclass(frozen=True)
class RuntimeEvidence:
    renderer: str
    authority: str
    available: bool
    executable: str | None
    version: str | None
    probes: dict[str, Any]
    artifact: dict[str, Any] | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _which(*commands: str) -> str | None:
    for command in commands:
        value = shutil.which(command)
        if value:
            return value
    return None


def _probe(command: list[str], timeout: int = 12) -> dict[str, Any]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        output = (result.stdout or result.stderr or '').strip()
        return {'ok': result.returncode == 0, 'returncode': result.returncode, 'output': output[:1000]}
    except Exception as exc:  # capability boundary: error is evidence, never success
        return {'ok': False, 'error': str(exc)}


def capability_snapshot() -> dict[str, RuntimeEvidence]:
    ffmpeg = _which('ffmpeg')
    ffprobe = _which('ffprobe')
    chromium = _which('chromium', 'chromium-browser', 'google-chrome')
    node = _which('node')
    npm = _which('npm')
    remotion = _which('remotion')
    hyperframes = _which('hyperframes')

    common = {
        'node': _probe([node, '--version']) if node else {'ok': False},
        'npm': _probe([npm, '--version']) if npm else {'ok': False},
        'ffmpeg': _probe([ffmpeg, '-version']) if ffmpeg else {'ok': False},
        'ffprobe': _probe([ffprobe, '-version']) if ffprobe else {'ok': False},
        'chromium': _probe([chromium, '--version']) if chromium else {'ok': False},
    }

    result: dict[str, RuntimeEvidence] = {}
    result['ffmpeg'] = RuntimeEvidence(
        'ffmpeg',
        'renderer_executed' if ffmpeg and ffprobe else 'unavailable',
        bool(ffmpeg and ffprobe),
        ffmpeg,
        common['ffmpeg'].get('output'),
        {'ffmpeg': common['ffmpeg'], 'ffprobe': common['ffprobe']},
        reason=None if ffmpeg and ffprobe else 'ffmpeg/ffprobe missing',
    )
    result['chromium_web'] = RuntimeEvidence(
        'chromium_web',
        'renderer_executed' if chromium else 'unavailable',
        bool(chromium),
        chromium,
        common['chromium'].get('output'),
        {'chromium': common['chromium'], 'ffmpeg': common['ffmpeg']},
        reason=None if chromium else 'Chromium missing',
    )
    result['remotion'] = RuntimeEvidence(
        'remotion',
        'renderer_executed' if remotion else 'compiler_ready',
        bool(remotion),
        remotion,
        _probe([remotion, '--version']).get('output') if remotion else None,
        {'node': common['node'], 'npm': common['npm'], 'cli_available': bool(remotion)},
        reason=None if remotion else 'Remotion CLI unavailable; compiler contract may still be valid.',
    )
    result['hyperframes'] = RuntimeEvidence(
        'hyperframes',
        'renderer_executed' if hyperframes else 'compiler_ready',
        bool(hyperframes),
        hyperframes,
        _probe([hyperframes, '--version']).get('output') if hyperframes else None,
        {'node': common['node'], 'npm': common['npm'], 'cli_available': bool(hyperframes)},
        reason=None if hyperframes else 'HyperFrames CLI unavailable; compiler contract may still be valid.',
    )
    return result


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def probe_media(path: str | Path) -> dict[str, Any]:
    ffprobe = _which('ffprobe')
    if not ffprobe:
        raise RuntimeError('ffprobe unavailable')
    result = subprocess.run([
        ffprobe, '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration',
        '-of', 'json', str(path),
    ], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    stream = payload['streams'][0]
    return {
        'codec': stream.get('codec_name'),
        'width': int(stream['width']),
        'height': int(stream['height']),
        'fps': stream.get('r_frame_rate'),
        'frames': int(stream.get('nb_frames') or 0),
        'duration_s': float(payload['format']['duration']),
        'sha256': sha256_file(path),
        'bytes': Path(path).stat().st_size,
    }


def verify_render_artifact(
    renderer: str,
    path: str | Path,
    *,
    expected_width: int,
    expected_height: int,
    expected_fps: int,
    expected_duration_s: float,
    duration_tolerance_s: float = 1 / 30,
) -> RuntimeEvidence:
    media = probe_media(path)
    errors: list[str] = []
    if media['width'] != expected_width or media['height'] != expected_height:
        errors.append('resolution_mismatch')
    if media['fps'] != f'{expected_fps}/1':
        errors.append('fps_mismatch')
    if abs(media['duration_s'] - expected_duration_s) > duration_tolerance_s:
        errors.append('duration_mismatch')
    authority = 'renderer_executed' if not errors else 'compiler_ready'
    return RuntimeEvidence(
        renderer=renderer,
        authority=authority,
        available=not errors,
        executable=None,
        version=None,
        probes={'artifact_integrity_errors': errors},
        artifact=media,
        reason=';'.join(errors) if errors else None,
    )


def write_snapshot(path: str | Path) -> dict[str, Any]:
    snapshot = {name: evidence.to_dict() for name, evidence in capability_snapshot().items()}
    Path(path).write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding='utf-8')
    return snapshot
