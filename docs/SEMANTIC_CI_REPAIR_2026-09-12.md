# Semantic qualification repair checkpoint — 2026-09-12

State: IMPLEMENTED_LOCAL_VERIFIED; full-corpus quality remains FAILED_UNQUALIFIED.

- Agent: motion://agent/ci-remediation-motion-20260912
- Session: motion://session/ci-remediation-motion-20260912
- Correlation: motion://work/semantic-evaluation-integrity-20260912
- Isolated branch: fix/semantic-evaluation-integrity-20260912
- Starting revision: PR #128 at 92524aa622ebc6fcf0b77b7ba0e91fd0d852ec03
- Context: AGENTS, state, tasks, Phase08 plan, merge-safe train, active-agent
  registry, immutable semantic events, and bus #39 through comment 5634673734.

## Observed failure

[Full MOTION qualification run 34602538206](https://github.com/rotprods/motion-OS/actions/runs/34602538206)
ran a real runner, indexed the corpus, graphified it and created a snapshot.
Its final assertion correctly rejected retrieval quality:

| Metric | Observed | Required |
| --- | ---: | ---: |
| Hit rate at 10 | 0.900000 | 0.92 |
| Mean recall at 10 | 0.733333 | 0.75 |
| MRR | 0.500000 | 0.72 |
| NDCG at 10 (old evaluator) | 0.694956 | 0.75 |

This failure is separate from the private-repository runner capacity blocker.
All 64 open PR heads had successful MERGE_SAFE checks when audited; #128 had
the only failing head check. Recent main Security Baseline run 34111523897
also succeeded.

## Bounded corrections

1. NDCG previously counted every matching file as relevant while normalizing
   against the number of target groups. Repeated matches against one glob
   produced impossible values such as 1.626156. DCG now rewards first discovery
   of a target group only. Overlapping groups cannot add multiple rewards at
   one rank. Reports retain both matched and newly discovered target indices.
2. The frozen benchmark JSON was indexed and appeared at rank 1 or 3 in
   evaluation results. The corpus manifest now excludes semantic retrieval
   answer datasets and generated semantic evidence directories. Source files
   and the evaluation dataset itself are preserved.
3. Evaluation unit tests now write their temporary dataset outside the
   repository so future indexing cannot ingest their generated fixture.

No query, expected label, quality threshold, workflow gate, or owner branch
was changed. Old and repaired NDCG values have different counting semantics
and must not be compared as an improvement claim.

## Validation and next action

- Targeted evaluation/corpus/index suite: 18 passed.
- Mandatory local_verify.py quick: 325 passed; compile/import/repo health PASS.
- Historical full-corpus qualification remains failed. This patch cannot
  certify retrieval quality through unit tests.
- Before promotion, rebuild a versioned projection from the corrected corpus
  manifest, graphify and rerun the frozen labeled evaluation and live benchmark;
  retain the snapshot, exact commit IDs, query results and service receipts.
- Inspect the missed targets and ranking errors and improve retrieval only
  against a held-out validation set. Do not lower thresholds or rewrite labels
  to make the existing candidate pass.
- AVE must apply the corresponding corpus/evaluator correction if it owns a
  duplicate implementation; full dual-repository qualification remains pending.
- Ownership: isolated branch scope released at this checkpoint; PR #128 source
  branch is untouched. No merge, release or main authority is claimed.
