# copy_pastes

This directory preserves user-supplied source knowledge before normalization.

## Policy
- Preserve source meaning and technical detail.
- Never silently replace a source artifact with normalized knowledge.
- New user-supplied phases are captured here first, then transformed into `/plans`, schemas/config, graph deltas, implementation tasks, and learning updates.
- If whitespace or formatting is normalized for Markdown, mark it explicitly.
- Normalized knowledge must cite the originating phase/copy-paste path in its plan.

## Current phase index
- Phase 01 — motion grammar / Apple premium / hyper-commercial brand examples (normalized in knowledge/config; source backfill pending full transcript export).
- Phase 02 — professional motion-system production method (normalized in knowledge; source backfill pending full transcript export).
- Phase 03 — exact SVG/frame reconstruction canon (normalized in knowledge/schema; source backfill pending full transcript export).
- Phase 04 — deterministic visual-DNA extraction + MotionStyle2JSON + compiler targets + style-system examples (captured from the current user source in this branch).

## Invariant
`COPY_PASTE != CANONICAL_RULE`.
Raw source is evidence. A plan decides what becomes canonical after conflict checks, validation, tests and QA.
