
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

@dataclass
class Critique:
    provider: str
    authoritative: bool
    score: float
    dimensions: dict[str,float]
    defects: list[dict[str,Any]]
    evidence: list[dict[str,Any]]
    recommendation: str

class MultimodalCritic:
    """
    Contract only. A real provider must inspect rendered frames/video.
    FixtureProvider is explicitly non-authoritative and can never release production.
    """
    def evaluate(self, media_path: str|Path, context: dict[str,Any]) -> Critique:
        raise NotImplementedError

class FixtureProvider(MultimodalCritic):
    def __init__(self, score=8.6): self.score=score
    def evaluate(self, media_path, context):
        dims={"composition":8.6,"motion_choreography":8.7,"transition_quality":8.7,"asset_realism":8.2,"typography":8.8,"style_coherence":8.7,"narrative_clarity":8.6,"final_frame_memorability":8.4}
        return Critique(provider="fixture_non_authoritative",authoritative=False,score=self.score,dimensions=dims,defects=[],evidence=[{"type":"fixture","note":"No real vision inference performed."}],recommendation="ITERATE")
