from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


STYLE_FAMILIES = (
    "industrial_white_product",
    "motorsport_broadcast",
    "japanese_techno_editorial",
    "space_mission_control",
    "dark_editorial_system",
)


@dataclass(frozen=True)
class BenchmarkFixture:
    brief_id: str
    style_family: str
    brief: str
    runtime_spec: dict

    def brief_sha256(self) -> str:
        return hashlib.sha256(self.brief.encode()).hexdigest()

    def spec_sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.runtime_spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def smoke_fixtures() -> tuple[BenchmarkFixture, ...]:
    brief = "Launch an autonomous AI browser that can browse, reason and act without a human driver."
    fixtures: list[BenchmarkFixture] = []
    for idx, style in enumerate(STYLE_FAMILIES):
        prefix = style.upper().replace("_", "-")
        scenes = []
        for scene_idx in range(3):
            start = scene_idx * 30
            scenes.append({
                "id": f"{prefix}-{scene_idx + 1:02d}",
                "from": start,
                "durationInFrames": 30,
                "camera": {"motion": ("static", "push", "orbit")[(idx + scene_idx) % 3]},
                "depth": {"layers_z": [0, 1, 2]},
                "transition": {"type": ("cut", "wipe", "match_motion")[(idx + scene_idx) % 3], "at_ms_global": start * 1000 // 30},
                "events": [{"id": f"pulse-{scene_idx}", "at_frame": start + 15, "action": "accent_pulse"}],
            })
        fixtures.append(BenchmarkFixture(
            brief_id=f"browser-launch-{idx + 1:02d}",
            style_family=style,
            brief=brief,
            runtime_spec={
                "project": {"fps": 30, "width": 640, "height": 360, "duration_frames": 90},
                "zOrder": ["ui", "subject", "background"],
                "scenes": scenes,
            },
        ))
    return tuple(fixtures)


def fixture_by_id(brief_id: str) -> BenchmarkFixture:
    matches = [fixture for fixture in smoke_fixtures() if fixture.brief_id == brief_id]
    if len(matches) != 1:
        raise KeyError(brief_id)
    return matches[0]


def fixture_manifest(fixtures: Iterable[BenchmarkFixture] | None = None) -> list[dict]:
    return [
        {
            "brief_id": fixture.brief_id,
            "style_family": fixture.style_family,
            "brief_sha256": fixture.brief_sha256(),
            "runtime_spec_sha256": fixture.spec_sha256(),
        }
        for fixture in (tuple(fixtures) if fixtures is not None else smoke_fixtures())
    ]
