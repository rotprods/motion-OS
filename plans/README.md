# MOTION.OS Plans

`/plans` is the living implementation layer between raw knowledge and code.

## Required lifecycle for every phase

```text
copy_pastes/phase_N_source
        ↓
source digest / conflicts
        ↓
plans/phase_N_*.md
        ↓
architecture graph delta
        ↓
schema / config / code tasks
        ↓
implementation evidence
        ↓
QA / benchmark
        ↓
learning update
        ↺
```

## Invariants
1. Raw source in `/copy_pastes` is immutable evidence.
2. Plans are living documents and may improve after every interaction.
3. A plan change must record: source interaction, changed assumptions, graph delta, task delta, gate delta, expected measurable impact.
4. New knowledge may contradict old knowledge. Do not average contradictions; resolve them explicitly or represent modes/branches.
5. No plan is considered complete without `Definition of Done`, tests/QA, rollback/failure criteria and downstream dependencies.
6. Architecture expansion is rejected unless it improves measured output, fidelity, reliability or continuity.

## Phase map
- Phase 01 — Motion grammar, brand energy, Apple premium, hyper-commercial gamified/audio.
- Phase 02 — Professional motion-production system from references → locked system → QA.
- Phase 03 — Exact frame reconstruction to SVG/SVG+JS/hybrid.
- Phase 04 — Deterministic feature extraction → Visual DNA normalization → MotionStyle2JSON → compiler targets → reusable knowledge system.

See `PLAN_EVOLUTION_PROTOCOL.md` for continuous-learning rules.
