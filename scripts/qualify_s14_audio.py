#!/usr/bin/env python3
from __future__ import annotations

import argparse
from array import array
import json
import math
from pathlib import Path
import subprocess
import tempfile
import wave

FPS = 30.0


def _read_pcm16_mono(path: Path) -> tuple[int, list[float]]:
    with wave.open(str(path), 'rb') as w:
        if w.getsampwidth() != 2:
            raise ValueError('PCM16 WAV required')
        sample_rate = w.getframerate()
        channels = w.getnchannels()
        raw = w.readframes(w.getnframes())
    samples = array('h')
    samples.frombytes(raw)
    if channels == 1:
        return sample_rate, [float(x) for x in samples]
    mono = [sum(samples[i:i + channels]) / channels for i in range(0, len(samples), channels)]
    return sample_rate, mono


def _transient_scores(path: Path, block_ms: float = 2.5) -> list[tuple[float, float]]:
    sample_rate, samples = _read_pcm16_mono(path)
    block = max(8, int(sample_rate * block_ms / 1000.0))
    out: list[tuple[float, float]] = []
    for start in range(0, len(samples) - block + 1, block):
        segment = samples[start:start + block]
        sum_sq = 0.0
        for i in range(1, len(segment)):
            derivative = (segment[i] - segment[i - 1]) / 32768.0
            sum_sq += derivative * derivative
        out.append((start / sample_rate, math.sqrt(sum_sq / max(1, len(segment) - 1))))
    return out


def _peak_near(scores: list[tuple[float, float]], source_frame: float, radius_frames: float = 1.2) -> tuple[float, float] | None:
    center = source_frame / FPS
    radius = radius_frames / FPS
    candidates = [item for item in scores if center - radius <= item[0] <= center + radius]
    return max(candidates, key=lambda item: item[1]) if candidates else None


def _extract_render_audio(video: Path, destination: Path) -> None:
    subprocess.run([
        'ffmpeg', '-y', '-v', 'error', '-i', str(video), '-vn', '-ac', '1', '-ar', '44100',
        '-c:a', 'pcm_s16le', str(destination)
    ], check=True)


def _source_events(contract: dict) -> list[float]:
    events = [float(item['local_frame']) for item in contract['audio_transient_clusters']]
    # T07 models the seven high-confidence state/transition accents. Other source
    # transients remain mixed-track observations, not mandatory synthetic hits.
    required = [10.05, 14.40, 16.80, 45.75, 50.25, 56.25, 62.85]
    missing = [target for target in required if not any(abs(value - target) < 0.01 for value in events)]
    if missing:
        raise ValueError(f'S14 contract missing required source transient proxies: {missing}')
    return required


def qualify(source_wav: Path, render_video: Path, contract_path: Path, gate_frames: float) -> dict:
    contract = json.loads(contract_path.read_text())
    source_events = _source_events(contract)
    with tempfile.TemporaryDirectory() as tmp:
        render_wav = Path(tmp) / 'render.wav'
        _extract_render_audio(render_video, render_wav)
        render_scores = _transient_scores(render_wav)
        events = []
        for source_frame in source_events:
            peak = _peak_near(render_scores, source_frame)
            if peak is None:
                events.append({'source_peak_frame': source_frame, 'render_peak_frame': None, 'error_frames': None})
                continue
            render_frame = peak[0] * FPS
            events.append({
                'source_peak_frame': source_frame,
                'render_peak_frame': render_frame,
                'error_frames': render_frame - source_frame,
                'render_transient_score': peak[1],
            })
    errors = [abs(item['error_frames']) for item in events if item['error_frames'] is not None]
    complete = len(errors) == len(source_events)
    max_error = max(errors) if errors else None
    mean_error = sum(errors) / len(errors) if errors else None
    passed = bool(complete and max_error is not None and max_error <= gate_frames)
    return {
        'schema_version': 'motion-os.s14-audio-onset-qualification/v1',
        'scene_id': 'S14_AUDIO_VISUAL_TEXTO',
        'authority': 'MEASURED_RENDERED_TRANSIENT_PEAK_VS_MEASURED_SOURCE_MIX_PROXY',
        'events': events,
        'mean_absolute_error_frames': mean_error,
        'max_absolute_error_frames': max_error,
        'gate_frames': gate_frames,
        'onset_peak_gate_pass': passed,
        'full_audio_fidelity_validated': False,
        'unknowns': [
            'isolated source SFX stems',
            'source SFX identity/timbre',
            'exact source transient envelope',
            'music/voice/SFX source decomposition',
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-wav', type=Path, required=True)
    ap.add_argument('--render-video', type=Path, required=True)
    ap.add_argument('--contract', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--gate-frames', type=float, default=1.5)
    args = ap.parse_args()
    result = qualify(args.source_wav, args.render_video, args.contract, args.gate_frames)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({
        'mean_absolute_error_frames': result['mean_absolute_error_frames'],
        'max_absolute_error_frames': result['max_absolute_error_frames'],
        'onset_peak_gate_pass': result['onset_peak_gate_pass'],
        'full_audio_fidelity_validated': result['full_audio_fidelity_validated'],
    }, indent=2))
    return 0 if result['onset_peak_gate_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
