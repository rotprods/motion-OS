# Structural Repair Operator v2

## Problem
RC07/RC08 showed that additive overlays can improve local polish while failing to create a materially better composition. This is a local optimum.

## New repair search space
A candidate branch may change, within its affected subgraph:

1. layout topology and safe-area allocation;
2. hero asset identity, crop, scale, perspective and depth treatment;
3. camera transform / 2.5D staging;
4. typography hierarchy and line breaking;
5. motion primitive family, not just parameters;
6. transition mechanism;
7. foreground/background interaction;
8. beat duration allocation;
9. lighting/material treatment;
10. audio-event alignment.

## Diversity constraint
For a 4-branch tournament, at least 3 branches must use different primitive families and at least 2 must use different layout topology. Parameter-only mutations do not count as distinct branches.

## Promotion gate
Do not promote based on mechanical metrics alone. Require:
- regression invariance outside affected region;
- technical integrity;
- visual inspection showing material improvement;
- semantic/creative critic evidence when authoritative provider is available.

## Anti-cosmetic rule
If all candidate contact sheets remain recognizably the same composition with added labels/rules, reject the tournament and expand search radius.
