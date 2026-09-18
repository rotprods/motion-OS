# T08 Cross-Scene Qualification Defect Graph

Authority: append-only adversarial ledger. A closed implementation/test defect does not imply a closed source-fidelity dimension.

## T08-DEF-ARCH-001 — observable fidelity conflated with original authoring identity

- domain: `QUALIFICATION ARCHITECTURE / AUTHORITY`
- severity: `P1 false-negative / wrong-objective risk`
- discovered after: first physically executed T08 v1 qualification artifact `9837991323`, exact head `b39e91e3ccdf46c0173e2056b52ae9554d9e4da1`.
- v1 result: only `temporal` fully qualified; 9 P1 + 11 P2 blockers; diagnostic claim coverage 0.375.
- escaped design flaw: several required 9D claims asked for hidden original authoring identity rather than observable output fidelity. Examples: original Graph Editor curve identity, original AE effect stack, hidden unique z-order without observable overlap, pre-grade tokens, isolated original stem identity.
- why this is wrong: the mission is to reconstruct an output-equivalent editing system in After Effects/Remotion/HyperFrames. Exact visible behavior can be reproduced without proving which original plugin, precomp, hidden z-order or stem the source editor used. Requiring hidden authoring identity makes output fidelity impossible to promote even when the rendered result could be pixel/temporal/audio equivalent.
- rejected repair: weaken the v1 gates or simply re-label hidden identity claims as QUALIFIED.
- architecture repair:
  1. separate `OUTPUT_FIDELITY_9D` from `AUTHORING_PROVENANCE`;
  2. only observable/reconstructable output properties may veto `OUTPUT_FIDELITY_9D`;
  3. original plugin/precomp/stem/font-file/hidden-authoring identity remains explicit `UNKNOWN/BLOCKED` provenance without laundering into output authority;
  4. an equivalent implementation may use different primitives if frame/audio/depth/temporal output meets the qualified contract;
  5. `RECONSTRUCT_EXACT` may still source-lock original pixels/audio/assets when provenance permits, but source-lock is not proof of original authoring graph.
- permanent invariants to add:
  - hidden authoring provenance must never be a required output-fidelity claim;
  - output-equivalent visible glyph outlines may qualify typography without identifying the font file;
  - output FX signature may qualify without identifying the original AE plugin/effect stack;
  - unobservable relative z-order is an equivalence class, not an output defect;
  - mixed/master audio output fidelity and SFX grammar are distinct from original stem identity;
  - psychological/editor intent is not required for output retention fidelity; observable stimulus choreography is.
- historical evidence preserved in Drive:
  - `GOLDEN_9D/02_COMPILED_GRAPH/current_qualification_v1_pre_authority_split.json`
  - `GOLDEN_9D/02_COMPILED_GRAPH/reverse-engineering-golden-9d-proof-v1.zip`
- status: `OPEN / V2 AUTHORITY SPLIT IN PROGRESS`

```text
OUTPUT_FIDELITY
  -> MEASURES -> OBSERVABLE RENDERED BEHAVIOR
  -> MAY_BE_IMPLEMENTED_BY -> MULTIPLE AUTHORING GRAPHS

AUTHORING_PROVENANCE
  -> ASKS -> WHICH ORIGINAL ASSET/PLUGIN/PRECOMP/STEM/GRAPH WAS USED
  -> MAY_REMAIN -> UNKNOWN
  -> MUST_NOT_VETO -> OUTPUT_FIDELITY_9D

CONFLATION
  -> CAUSES -> PERMANENT_FALSE_NEGATIVE
  -> ENCOURAGES -> UNRECOVERABLE_HIDDEN_STATE_CHASING
  -> REDUCES -> REPLICATION_UTILITY
```
