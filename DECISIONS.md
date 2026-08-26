# DECISIONS

## D001 — Canonical repo reconstruction
**Decision:** v0.8 is reconstructed from v0.4 + v0.7 persisted artifacts instead of continuing the reduced v0.7 fork.
**Reason:** v0.5–v0.7 lost v0.4 capabilities and continuity.
**Rollback:** source artifacts remain untouched under /mnt/data.

## D002 — Weight realignment
**Decision:** global creative quality weight rises to 45%; engineering falls to 15%.
**Reason:** visual output is the dominant bottleneck.

## D003 — Release authority
**Decision:** no heuristic/mechanical score can release a master.
**Reason:** v0.7 proves metric optimization can coexist with visibly poor output.
