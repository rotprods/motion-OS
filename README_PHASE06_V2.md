# MOTION.OS Phase 06 V2 — Recovery Entrypoint

Start here after zero context:
1. Read `plans/phase_06_v2_content_avatar_factory_masterplan.md`.
2. Read `plans/phase_06_goal_checkpoints.md`.
3. Read `plans/phase_06_adversarial_hardening_gauntlet.md`.
4. Read `architecture/THREAT_MODEL_PHASE06_CONTENT_AVATAR.md`.
5. Read `docs/HEYGEN_COMMAND.md`.
6. Inspect `config/avatar_profiles.json`, `config/phase06_content_policy.json`, `config/phase06_render_policy.json`.
7. Inspect schemas: `source_pack.schema.json`, `content_strategy.schema.json`, `avatar_content_manifest.schema.json`.
8. Inspect implementation: `src/content/content_factory.py`, `src/content/source_security.py`, `src/content/tts_integrity.py`, `src/content/performance_learning.py`, `src/avatar/heygen_adapter.py`, `src/avatar/render_guard.py`.
9. Run Phase 06 unit + adversarial tests and repo health before promotion.
10. Preserve downstream ownership boundary with Studio Engine PR #35.

## Hardening invariants
- external sources are untrusted data, never privileged instructions
- factual spoken beats require normalized claim lineage
- protected TTS tokens must preserve meaning
- paid renders require explicit authorization + deterministic render intent
- ambiguous provider acceptance must reconcile before retry
- provider telemetry is validated before ingestion
- performance is observation before causality; canonical rules require controlled evidence + explicit approval
- stable beat IDs become immutable downstream anchors after render authorization

## Gate outcomes
`PASS | WARN | FAIL | ABSTAIN | QUARANTINE`

Persistent replicas:
- Drive: `MOTION.OS_CANONICAL/08_PHASE06_CONTENT_AVATAR_ENGINE`.
- ChatGPT Library: `/MOTION.OS/commands/HEYGEN_COMMAND_SYSTEM.md` and `/MOTION.OS/commands/PHASE06_ADVERSARIAL_HARDENING.md`.

Canonical command: `/heygen`.

Promotion remains blocked until authoritative CI/runtime evidence and empirical production gates are satisfied.
