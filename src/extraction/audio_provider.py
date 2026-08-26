from __future__ import annotations

from array import array
from pathlib import Path
from typing import Any
import math
import shutil
import subprocess
import tempfile
import wave


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def extract_audio_pcm(video_path: str | Path, output_wav: str | Path, *, sample_rate: int = 16000) -> Path:
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        raise RuntimeError("required binary unavailable: ffmpeg")
    out = Path(output_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(out)
    ], check=True)
    return out


def analyze_audio_envelope(video_path: str | Path, *, window_ms: int = 25, hop_ms: int = 10, onset_z: float = 2.2) -> dict[str, Any]:
    """Decode audio with FFmpeg and measure RMS/onsets using stdlib only.

    This is an executable fallback when librosa/Whisper are absent. It does not claim music-beat semantics;
    detected timestamps are transient/onset candidates backed by PCM energy deltas.
    """
    if not _ffmpeg():
        return {"available": False, "authority": "unavailable", "reason": "ffmpeg missing", "onsets_ms": [], "envelope": [], "transcript": []}
    with tempfile.TemporaryDirectory(prefix="motion_os_audio_") as td:
        wav_path = extract_audio_pcm(video_path, Path(td) / "mono.wav")
        with wave.open(str(wav_path), "rb") as wf:
            sr = wf.getframerate()
            frames = wf.getnframes()
            raw = wf.readframes(frames)
        samples = array("h")
        samples.frombytes(raw)
        if not samples:
            return {"available": True, "authority": "measured", "method": "pcm_rms_v1", "sample_rate": sr, "onsets_ms": [], "envelope": [], "transcript": [], "warning": "audio stream empty"}
        win = max(1, round(sr * window_ms / 1000))
        hop = max(1, round(sr * hop_ms / 1000))
        env: list[tuple[int, float]] = []
        for start in range(0, max(1, len(samples) - win + 1), hop):
            chunk = samples[start:start + win]
            if not chunk:
                continue
            rms = math.sqrt(sum(float(s) * float(s) for s in chunk) / len(chunk)) / 32768.0
            env.append((round(start * 1000 / sr), rms))
        if len(env) < 3:
            return {"available": True, "authority": "measured", "method": "pcm_rms_v1", "sample_rate": sr, "onsets_ms": [], "envelope": [{"at_ms": t, "rms": round(v, 6)} for t, v in env], "transcript": []}
        deltas = [max(0.0, env[i][1] - env[i - 1][1]) for i in range(1, len(env))]
        mean = sum(deltas) / len(deltas)
        var = sum((d - mean) ** 2 for d in deltas) / len(deltas)
        std = math.sqrt(var)
        threshold = mean + onset_z * std
        onsets: list[int] = []
        last = -10_000
        for i, delta in enumerate(deltas, start=1):
            if delta >= threshold and env[i][0] - last >= 80:
                onsets.append(env[i][0])
                last = env[i][0]
        return {
            "available": True,
            "authority": "measured",
            "method": "ffmpeg_pcm_rms_onset_v1",
            "sample_rate": sr,
            "window_ms": window_ms,
            "hop_ms": hop_ms,
            "onset_threshold": round(threshold, 8),
            "onsets_ms": onsets,
            "envelope": [{"at_ms": t, "rms": round(v, 6)} for t, v in env[::max(1, len(env)//240)]],
            "transcript": [],
            "transcript_authority": "unavailable_without_transcript_provider",
        }


def transcribe_whisper_optional(video_path: str | Path, *, model_name: str = "tiny") -> dict[str, Any]:
    """Optional local Whisper provider; explicit unavailable state if dependency/model is absent."""
    try:
        import whisper  # type: ignore
    except Exception as exc:
        return {"available": False, "authority": "unavailable", "reason": f"whisper:{type(exc).__name__}", "segments": []}
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(str(video_path), verbose=False)
    except Exception as exc:
        return {"available": False, "authority": "failed", "reason": f"whisper_runtime:{type(exc).__name__}:{exc}", "segments": []}
    segments = [
        {"start_ms": round(float(s["start"]) * 1000), "end_ms": round(float(s["end"]) * 1000), "text": str(s["text"]).strip()}
        for s in result.get("segments", [])
    ]
    return {"available": True, "authority": "measured_model", "method": f"openai_whisper_{model_name}", "segments": segments}
