# Semantic provider response integrity — bounded repair

Base candidate: `cd8239e8a58d89ebb6e3f03276967b15131f4f53`, PR163.
Session: `motion://session/dod-response-integrity-20260912`.

## Observed failure and scope

Full-corpus workflow [34708673857](https://github.com/rotprods/motion-OS/actions/runs/34708673857)
executed indexing, graphification, evaluation and snapshot creation. Its final
qualification failed the frozen retrieval thresholds. This is a real quality
blocker, not a zero-step account failure. It remains open after this repair.

Adjacent provider-boundary review reproduced three incorrect success paths:

1. A candidate without its native vector reused its coarse routing score as a
   semantic score. Zero/nonfinite/nonnumeric vectors were also accepted.
2. Malformed or short query batches became empty results and could overwrite
   existing graph neighborhoods with empty/corrupt derived edges.
3. Collection compatibility checked dimensions but not the required distance.

The repair requires finite nonzero native vectors, exact result cardinality,
valid point identities, finite numeric scores, object payloads and Cosine
distance. Valid empty result sets and numeric zero identities/scores still work.
It does not alter embedding inputs, ranking law, thresholds, frozen labels,
workflow triggers, main, or promotion authority.

## Evidence

- Initial negative regression: 28 failed, one valid-empty control passed.
- Independent review found the additional corrupt-point bypass; eleven
  graphification negatives now prove zero writes for a corrupt batch, including
  a valid first result followed by a corrupt second result.
- Focused suite: 52 passed.
- Required local `scripts/local_verify.py quick`: 366 passed, import smoke,
  compileall and repository health pass.
- Independent re-review: no further blocker found in this bounded repair.

## Remaining DoD and handoff

`IMPLEMENTED_AND_LOCALLY_VERIFIED`, not project completion or promotion.
The parser validates a complete response batch before returning it; this does
not provide a transaction over multiple graphification batches. Payload shape
validation does not establish full semantic provenance. Real Ollama/Qdrant were
unavailable locally; only prior hosted execution and synthetic boundary tests
are claimed here. Full-corpus relevance remains below all four required gates.

Reconstruct current PR163/PR128 heads and the immutable event bus before work.
Use the frozen benchmark and a qualified local/clean runner to investigate the
retrieval ranking, preserving native-cosine semantics and evidence provenance.
Do not change labels, exclude legitimate code/docs, lower thresholds, or promote
the branch to manufacture qualification. Main/release barriers remain in force.
