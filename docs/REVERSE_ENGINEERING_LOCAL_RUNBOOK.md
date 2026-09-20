# MOTION.OS Reverse Engineering — Local Runbook v2

## Inputs

- reference video with provenance/rights context;
- exact repo head and active agent claim;
- `RECONSTRUCT_EXACT`, `STRUCTURAL_TEMPLATE`, or `STYLE_TRANSFER` mode.

## 1. Physical evidence run

```bash
python scripts/reverse_engineer_video.py reference.mp4 \
  --out .artifacts/reverse/<video_id> \
  --mode structural \
  --flow-stride 1 \
  --keep-frames
```

Preserve source SHA, decoded frame count, FPS, frame timeline and provider authority.

## 2. Annotate atomic actions

Produce the full evidence-plane `action_inventory.json` from frame/scene/caption/depth/audio inspection.

Rules:
- every action has AE/Remotion/HyperFrames mappings;
- `staggered` parents expose `subevents[]`;
- `continuous` actions do not fabricate internal keyframes;
- `source_native`/`mixed` motion is separated from editorial motion;
- literal source UI/media stays source-locked when appropriate.

## 3. Run the nine-loop gauntlet

```bash
python scripts/reverse_engineering_gauntlet.py \
  --inventory <action_inventory.json> \
  --frame-metrics <frame_metrics.json> \
  --out <gauntlet_report.json>
```

The runner requires P90 coverage and performs deep P80/P75 residual adjudication. During template calibration, also inspect P70/P65/P60 until lower thresholds stop discovering meaningful editor operations.

Every residual must resolve as:
- `anchored`
- `continuous`
- `source_native`
- `unexplained` → FAIL

## 4. Persist canonical surfaces

GitHub:
- schemas/validators/scripts/tests;
- canonical template/ontology/gauntlet docs;
- lightweight specimen indexes and coverage state.

Drive:
- source video;
- frame metrics/evidence;
- full action/subevent inventory;
- decision-operation projection;
- gauntlet details;
- physical reconstruction/diff artifacts;
- generalization runs.

Event Bus:
- HELLO/CLAIM/checkpoints/authority lifecycle.

## 5. Repository gates

```bash
python scripts/local_verify.py quick
python scripts/agent_event.py validate
```

Do not merge while a canonical regression/promotion barrier is active.

## 6. Physical reconstruction gate

Freeze the graph first. Then reconstruct the selected golden scenes without looking back at the reference to make new creative decisions.

Compare reference vs render for:
- timing/cut boundaries;
- typography geometry and emphasis;
- transforms/easing/settle;
- z-order/occlusion/depth;
- color/FX;
- audio-event alignment.

Convert every mismatch into a graph-native Defect/RepairCandidate. Repair canonical operations, then recompile all renderers.

## 7. Generalization gate

Run at least three substituted-content packs. The structural template fails if literal source content leaks or edit identity collapses.

## Authority language

Allowed with matching evidence:
- `OBSERVABLE_ACTION_CLOSED`
- `RENDER_VALIDATED`
- `FIDELITY_VALIDATED`
- `GENERALIZATION_VALIDATED`

Forbidden without evidence:
- “exact original AE project recovered”
- “100% original editor operations recovered”
- “canonical template” before physical fidelity + generalization.
