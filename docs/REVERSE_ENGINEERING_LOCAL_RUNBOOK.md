# MOTION.OS Reverse Engineering — Local Runbook

## Inputs

- reference video with provenance/rights context;
- exact repo head and active agent claim;
- `RECONSTRUCT_EXACT`, `STRUCTURAL_TEMPLATE`, or `STYLE_TRANSFER` mode.

## Local evidence run

```bash
python scripts/reverse_engineer_video.py reference.mp4 \
  --out .artifacts/reverse/<video_id> \
  --mode structural \
  --flow-stride 1 \
  --keep-frames
```

## Atomic-action gauntlet

After human/vision-assisted annotation produces `action_inventory.json`:

```bash
python scripts/reverse_engineering_gauntlet.py \
  --inventory forensics/references/<video_id>/action_inventory.json \
  --frame-metrics .artifacts/reverse/<video_id>/frame_metrics.json \
  --out .artifacts/reverse/<video_id>/gauntlet_report.json
```

Exit non-zero means observable-action closure has not been reached.

## Repository checks

```bash
python scripts/local_verify.py quick
python scripts/agent_event.py validate
```

## Physical reconstruction

Do not consult the source for new creative decisions after the reconstruction spec is frozen. Render golden scenes, compare to source, convert mismatch into defects, repair canonical actions, and repeat.

## Authority language

Allowed:
- `OBSERVABLE_ACTION_CLOSED`
- `RENDER_VALIDATED`
- `FIDELITY_VALIDATED`

Forbidden without evidence:
- “exact original AE project recovered”
- “100% original editor operations recovered”
