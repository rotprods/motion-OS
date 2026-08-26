from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


AUTHORITY_RANK = {
    'fixture': 0,
    'evidence_only': 1,
    'inferred': 2,
    'measured': 3,
    'ground_truth': 4,
    'authoritative': 5,
}


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    version: str
    inputs: tuple[dict, ...] = ()
    outputs: tuple[dict, ...] = ()
    requires: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    providers: tuple[str, ...] = ()
    authority: str = 'inferred'
    deterministic: bool = False
    cost_class: str = 'low'
    latency_class: str = 'seconds'
    failure_modes: tuple[str, ...] = ()
    fallbacks: tuple[str, ...] = ()
    qa: tuple[str, ...] = ()
    graph_effects: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'SkillSpec':
        return cls(
            skill_id=data['skill_id'],
            version=data['version'],
            inputs=tuple(data.get('inputs', [])),
            outputs=tuple(data.get('outputs', [])),
            requires=tuple(data.get('requires', [])),
            tools=tuple(data.get('tools', [])),
            providers=tuple(data.get('providers', [])),
            authority=data.get('authority', 'inferred'),
            deterministic=bool(data.get('deterministic', False)),
            cost_class=data.get('cost_class', 'low'),
            latency_class=data.get('latency_class', 'seconds'),
            failure_modes=tuple(data.get('failure_modes', [])),
            fallbacks=tuple(data.get('fallbacks', [])),
            qa=tuple(data.get('qa', [])),
            graph_effects=dict(data.get('graph_effects', {})),
        )


@dataclass(frozen=True)
class CapabilityInventory:
    capabilities: frozenset[str] = frozenset()
    tools: frozenset[str] = frozenset()
    providers: frozenset[str] = frozenset()

    @classmethod
    def from_iterables(cls, *, capabilities: Iterable[str] = (), tools: Iterable[str] = (), providers: Iterable[str] = ()):
        return cls(frozenset(capabilities), frozenset(tools), frozenset(providers))


@dataclass(frozen=True)
class SkillResolution:
    requested_skill_id: str
    selected_skill_id: str | None
    ready: bool
    fallback_chain: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    missing_tools: tuple[str, ...]
    missing_providers: tuple[str, ...]
    reason: str


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, SkillSpec] = {}

    def register(self, spec: SkillSpec) -> None:
        if spec.skill_id in self._skills:
            raise ValueError(f'duplicate skill: {spec.skill_id}')
        if spec.authority not in AUTHORITY_RANK:
            raise ValueError(f'unknown authority: {spec.authority}')
        self._skills[spec.skill_id] = spec

    def get(self, skill_id: str) -> SkillSpec:
        try:
            return self._skills[skill_id]
        except KeyError:
            raise KeyError(f'unknown skill: {skill_id}') from None

    def all(self) -> tuple[SkillSpec, ...]:
        return tuple(self._skills[key] for key in sorted(self._skills))

    def resolve(
        self,
        skill_id: str,
        inventory: CapabilityInventory,
        *,
        min_authority: str | None = None,
    ) -> SkillResolution:
        if min_authority is not None and min_authority not in AUTHORITY_RANK:
            raise ValueError(f'unknown min_authority: {min_authority}')
        visited: list[str] = []

        def attempt(current_id: str):
            if current_id in visited:
                return None, (), (), (), f'fallback_cycle:{current_id}'
            visited.append(current_id)
            spec = self.get(current_id)
            missing_cap = tuple(sorted(set(spec.requires) - set(inventory.capabilities)))
            missing_tools = tuple(sorted(set(spec.tools) - set(inventory.tools)))
            missing_providers = tuple(sorted(set(spec.providers) - set(inventory.providers)))
            authority_ok = min_authority is None or AUTHORITY_RANK[spec.authority] >= AUTHORITY_RANK[min_authority]
            if not missing_cap and not missing_tools and not missing_providers and authority_ok:
                return spec, (), (), (), 'ready'
            for fallback_id in spec.fallbacks:
                fallback, fc, ft, fp, reason = attempt(fallback_id)
                if fallback is not None:
                    return fallback, fc, ft, fp, f'fallback_from:{current_id}'
            reason = 'requirements_unavailable'
            if not authority_ok:
                reason = f'authority_below:{min_authority}'
            return None, missing_cap, missing_tools, missing_providers, reason

        selected, missing_cap, missing_tools, missing_providers, reason = attempt(skill_id)
        return SkillResolution(
            requested_skill_id=skill_id,
            selected_skill_id=selected.skill_id if selected else None,
            ready=selected is not None,
            fallback_chain=tuple(visited),
            missing_capabilities=missing_cap,
            missing_tools=missing_tools,
            missing_providers=missing_providers,
            reason=reason,
        )
