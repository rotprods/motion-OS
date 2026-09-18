from __future__ import annotations

from array import array
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable
import json
import math
import shutil
import subprocess


Runner = Callable[..., Any]


@dataclass(frozen=True)
class MasterAudioIntegrityEvidence:
    ok: bool
    errors: tuple[str, ...]
    audio_stream_count: int
    codec: str | None
    sample_rate: int | None
    channels: int | None
    duration_s: float | None
    expected_duration_s: float
    window_rms_dbfs: tuple[float, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finite_positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number=float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def _run(runner: Runner, argv: list[str], *, timeout: int, text: bool):
    return runner(argv, capture_output=True, text=text, timeout=timeout, check=False)


def _decode_rms_dbfs(
    media_path: str,
    *,
    start_s: float,
    duration_s: float,
    ffmpeg_bin: str,
    runner: Runner,
    timeout: int,
) -> float:
    if start_s < 0 or duration_s <= 0 or not math.isfinite(start_s) or not math.isfinite(duration_s):
        raise ValueError("invalid speech window")
    result=_run(
        runner,
        [
            ffmpeg_bin,"-v","error","-ss",f"{start_s:.3f}","-t",f"{duration_s:.3f}",
            "-i",media_path,"-map","0:a:0","-ac","1","-ar","16000","-f","s16le","-",
        ],
        timeout=timeout,
        text=False,
    )
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError("audio decode failed")
    samples=array("h")
    samples.frombytes(result.stdout)
    if not samples:
        raise RuntimeError("audio decode produced no samples")
    mean_square=sum(int(sample)*int(sample) for sample in samples)/len(samples)
    rms=math.sqrt(mean_square)/32768.0
    return 20*math.log10(max(rms,1e-12))


def verify_master_audio_integrity(
    media_path: str | Path,
    *,
    expected_duration_s: float,
    expected_sample_rate: int=48000,
    expected_channels: int=2,
    duration_tolerance_s: float=1/30,
    speech_windows: tuple[tuple[float,float], ...]=(),
    silence_floor_dbfs: float=-65.0,
    ffprobe_bin: str | None=None,
    ffmpeg_bin: str | None=None,
    runner: Runner=subprocess.run,
    timeout: int=12,
) -> MasterAudioIntegrityEvidence:
    """Verify the final encoded bytes preserve the single master-audio contract.

    Structural proof (one audio stream, sample rate, channel count, duration) is
    mandatory. Optional ``speech_windows`` add physical decoded-energy evidence so
    a present-but-silent stream cannot masquerade as a successful master.
    """
    path=str(media_path)
    errors: list[str]=[]
    if not path.strip():
        raise ValueError("media_path must be non-empty")
    expected_duration=_finite_positive_number(expected_duration_s)
    if expected_duration is None:
        raise ValueError("expected_duration_s must be finite and positive")
    if isinstance(expected_sample_rate, bool) or not isinstance(expected_sample_rate, int) or expected_sample_rate <= 0:
        raise ValueError("expected_sample_rate must be a positive integer")
    if isinstance(expected_channels, bool) or not isinstance(expected_channels, int) or expected_channels <= 0:
        raise ValueError("expected_channels must be a positive integer")
    if (
        isinstance(duration_tolerance_s, bool)
        or not isinstance(duration_tolerance_s, (int, float))
        or not math.isfinite(float(duration_tolerance_s))
        or float(duration_tolerance_s) < 0
    ):
        raise ValueError("duration_tolerance_s must be finite and non-negative")
    duration_tolerance_s = float(duration_tolerance_s)
    if (
        isinstance(silence_floor_dbfs, bool)
        or not isinstance(silence_floor_dbfs, (int, float))
        or not math.isfinite(float(silence_floor_dbfs))
    ):
        raise ValueError("silence_floor_dbfs must be finite")
    silence_floor_dbfs = float(silence_floor_dbfs)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise ValueError("timeout must be a positive integer")
    if not isinstance(speech_windows, tuple):
        raise ValueError("speech_windows must be a tuple of (start_s, duration_s) pairs")
    for index, window in enumerate(speech_windows):
        if not isinstance(window, tuple) or len(window) != 2:
            raise ValueError(f"speech_windows[{index}] must be a two-item tuple")
        start_s, window_duration_s = window
        if (
            isinstance(start_s, bool) or isinstance(window_duration_s, bool)
            or not isinstance(start_s, (int, float)) or not isinstance(window_duration_s, (int, float))
            or not math.isfinite(float(start_s)) or not math.isfinite(float(window_duration_s))
            or float(start_s) < 0 or float(window_duration_s) <= 0
        ):
            raise ValueError(f"speech_windows[{index}] must contain finite non-negative start and positive duration")

    probe_bin=ffprobe_bin or shutil.which("ffprobe")
    if not probe_bin:
        raise RuntimeError("ffprobe unavailable")
    result=_run(
        runner,
        [
            probe_bin,"-v","error",
            "-show_entries","stream=index,codec_type,codec_name,sample_rate,channels,duration:format=duration",
            "-of","json",path,
        ],
        timeout=timeout,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("ffprobe failed")
    try:
        payload=json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("invalid ffprobe JSON") from exc
    if not isinstance(payload,dict) or not isinstance(payload.get("streams"),list):
        raise RuntimeError("invalid ffprobe structure")

    audio_streams=[s for s in payload["streams"] if isinstance(s,dict) and s.get("codec_type")=="audio"]
    if len(audio_streams) != 1:
        errors.append(f"audio_stream_count:{len(audio_streams)}")
    stream=audio_streams[0] if len(audio_streams)==1 else None
    codec=None
    sample_rate=None
    channels=None
    duration=None
    if stream is not None:
        codec=stream.get("codec_name") if isinstance(stream.get("codec_name"),str) else None
        if not codec or not codec.strip():
            errors.append("missing_audio_codec")
        try:
            sample_rate=int(stream.get("sample_rate"))
        except (TypeError,ValueError):
            sample_rate=None
        if sample_rate != expected_sample_rate:
            errors.append(f"sample_rate_mismatch:{sample_rate}")
        try:
            channels=int(stream.get("channels"))
        except (TypeError,ValueError):
            channels=None
        if channels != expected_channels:
            errors.append(f"channel_mismatch:{channels}")
        # Container duration is not proof of audio-stream duration. Falling
        # back to format.duration could let a truncated audio stream inherit the
        # video's full duration and falsely qualify.
        duration=_finite_positive_number(stream.get("duration"))
        if duration is None:
            errors.append("missing_audio_stream_duration")
        elif abs(duration-expected_duration) > duration_tolerance_s:
            errors.append(f"audio_duration_mismatch:{duration:.6f}")

    rms_values: list[float]=[]
    if speech_windows and stream is not None and not errors:
        decoder=ffmpeg_bin or shutil.which("ffmpeg")
        if not decoder:
            raise RuntimeError("ffmpeg unavailable for speech-window verification")
        for start_s,window_duration_s in speech_windows:
            rms=_decode_rms_dbfs(
                path,start_s=start_s,duration_s=window_duration_s,
                ffmpeg_bin=decoder,runner=runner,timeout=timeout,
            )
            rms_values.append(rms)
            if rms <= silence_floor_dbfs:
                errors.append(f"silent_speech_window:{start_s:.3f}")

    return MasterAudioIntegrityEvidence(
        ok=not errors,
        errors=tuple(errors),
        audio_stream_count=len(audio_streams),
        codec=codec,
        sample_rate=sample_rate,
        channels=channels,
        duration_s=duration,
        expected_duration_s=expected_duration,
        window_rms_dbfs=tuple(rms_values),
    )
