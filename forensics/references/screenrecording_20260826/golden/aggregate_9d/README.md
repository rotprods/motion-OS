# Aggregate Golden 9D Qualification

This directory is a renderer-neutral projection over the four T07 golden-scene workstreams.

It does not copy renderer implementations and it is not a second editing source of truth.

Canonical inputs are exact scene revisions plus durable source-bound evidence:

- S04 / PR #96 / `8ec35a259399d7b196b40627d782315a019e65e2`
- S11 / PR #107 / `988e91893cb498f720b9c2656b3d6d85f2d56300`
- S14 / PR #124 / `12592bd8f8149767fafcb0ad0aa6036250ce540c`
- S16 / PR #125 / `8e6fcb79d0d7958c0f023f128297059c97a7e674`

`golden_evidence_manifest.json` is the machine-readable claim/evidence contract.
`cross_scene_output_equivalence.json` is a physically measured provenance bridge for S11/S14 old qualified artifacts to their exact final scene heads.

Generated qualification results must be reproducible from these inputs and must remain `CROSS_SCENE_PARTIAL_QUALIFICATION` while any required 9D claim is not independently qualified.
