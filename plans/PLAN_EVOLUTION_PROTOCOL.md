# PLAN_EVOLUTION_PROTOCOL.md

## Objective
Make every new expert interaction improve MOTION.OS without silently corrupting prior truth.

## Interaction ingestion contract
For every new knowledge payload:
1. Preserve source in `/copy_pastes`.
2. Assign `interaction_id` and affected phase(s).
3. Extract propositions into `OBSERVED_SOURCE`, `PROPOSED_RULE`, `EXAMPLE`, `MODEL_CAPABILITY_CLAIM`, `TAXONOMY_TERM`, `IMPLEMENTATION_IDEA`.
4. Compare against canonical configs/schemas/plans.
5. Classify each proposition:
   - ADDITIVE
   - REFINEMENT
   - CONFLICT
   - DEPRECATION
   - TIME_SENSITIVE_CAPABILITY
   - EXAMPLE_ONLY
6. Update affected plan(s).
7. Emit graph delta.
8. Emit task/gate delta.
9. Implement only validated portions.
10. Run relevant QA/CI.
11. Record learning outcome.

## Required plan changelog entry
```yaml
interaction_id:
source_paths: []
phase:
changes:
  assumptions: []
  graph: []
  tasks: []
  gates: []
  schemas: []
  configs: []
expected_impact:
evidence_required:
rollback_condition:
```

## Conflict resolution
Never average contradictory design systems.
Use one of:
- separate execution modes
- separate style/grammar families
- dominance by scene/shot
- capability routing
- explicit deprecated rule

Example:
`minimal_orbit` and `portal_glass` are not blended 50/50 by default. They become compatible modes connected by controlled transition grammar.

## Evidence hierarchy
1. Measured source feature / frame / timestamp.
2. Repeated high-confidence reference pattern.
3. Explicit user expert rule.
4. Model inference.
5. Aesthetic speculation.

Lower levels may not overwrite higher levels without a contradiction record.

## Model/tool capability claims
Claims such as max duration, model text consistency or supported resolution are stored as capability metadata with verification timestamp. They must never become timeless design laws.

## Learning loop
```text
SOURCE
 ↓
EXTRACT PROPOSITIONS
 ↓
COMPARE CANON
 ↓
PLAN DELTA
 ↓
GRAPH DELTA
 ↓
IMPLEMENT / EXPERIMENT
 ↓
QA
 ↓
PROMOTE / QUARANTINE / ROLLBACK
 ↓
FAILURE + SUCCESS MEMORY
 ↺
```

## Success criterion
A future agent can answer: “Which user interaction caused this rule, where is the source, what changed, what evidence promoted it, and what would invalidate it?”
