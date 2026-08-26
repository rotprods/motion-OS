# Phase 04A — User Copy-Paste: Deterministic Visual-DNA Extraction Pipeline

> Source: user-supplied knowledge, captured 2026-08-26. Formatting normalized to Markdown; technical content preserved.

## Two-layer architecture

For robustness and scale, the system must have two layers.

### A) Extraction layer — deterministic / low-level ML
Converts video → measurable signals:
- cuts / scenes / shots
- keyframes
- motion: camera / objects
- palettes and gradients
- typography and hierarchy
- layout and grids
- effects: glow, blur, noise, grain
- 2D / 3D elements and primitives
- on-screen text via OCR
- audio → transcript + timestamps

Candidate tools: FFmpeg, PySceneDetect, OpenCV, Whisper, OCR, CLIP / SigLIP embeddings, etc.

### B) LLM layer — normalization + classification + system generation
The LLM should not be the primary measurement instrument. It receives structured features, maps them to a controlled taxonomy, and produces the final schema-valid JSON.

## Recommended repeatable analysis pipeline

### Step 0 — Ingest
Input: `video.mp4`.
Output technical metadata:
- fps
- resolution
- duration
- aspect ratio
- codec
- bitrate

### Step 1 — Shot detection
Output:
- shots with `start_ms`, `end_ms`
- representative keyframe per shot

### Step 2 — Keyframes + thumbnails
Generate 1–3 frames per shot: start / middle / end.

### Step 3 — On-screen text + tracking
Per frame/shot:
- text blocks with bounding boxes
- textual content
- approximate font class / weight / relative size
- text colors and contrast

### Step 4 — Color system
Output:
- global dominant + accent palette
- palette per shot
- linear/radial gradient detection with approximate stops
- color mood: warm/cold, saturation, contrast

### Step 5 — Layout system
Output:
- probable grid: 12-col, 8pt baseline, centered, etc.
- dominant margins and alignments
- composition patterns: centered hero, split, card UI, full-bleed, etc.

### Step 6 — Motion primitives — highest-value extraction
Per shot extract motion grammar:
- transition type: cut, fade, wipe, slide, zoom, match cut
- probable easing: linear, ease-in-out, spring
- dominant direction
- timing: duration, delays, stagger
- camera: pan, tilt, zoom, parallax
- effects: glow pulse, blur-in, motion blur, grain, bloom
- UI kinematics: card enters, hover, scroll, cursor, highlight

Use optical flow + heuristics, then normalize using the LLM.

### Step 7 — 2D / 3D asset typing
Classify recurring elements:
- shapes: sphere, cube, ribbon, wire, blob, concentric circle
- materials: glass, matte, metallic, plastic, clay
- lighting: softbox, rim light, soft AO
- background: neutral studio, pastel gradient, black + glow, etc.

### Step 8 — Audio / VO / rhythm
Output:
- timestamped transcript
- beat / impact / whoosh events
- cut-density vs audio synchronization

### Step 9 — Feature Pack
Intermediate object fed to the LLM:

```json
{
  "video_meta": {},
  "shots": [],
  "ocr": [],
  "color_stats": {},
  "layout_stats": {},
  "motion_stats": {},
  "asset_stats": {},
  "audio_stats": {}
}
```

## Knowledge-system / database layer

### Controlled ontology
Closed catalogs should normalize outputs:
- `style_family`: neon_dark, editorial_minimal, eco_handdrawn, ui_saas_glow, 3d_soft_pastel, kinetic_type, etc.
- `typography`: grotesk_modern, serif_editorial, mono_tech, handwritten_marker
- `motion_primitives`: fade_in, slide_in, scale_pop, smear, reveal_mask, glow_trace, camera_dolly
- `materials`: glass, matte_plastic, brushed_metal, paper, clay
- `transitions`: cut, fade, cross_dissolve, match_move, whip_pan, wipe

### Hybrid storage proposal from source
- Relational / Postgres for clean entities: styles, tokens, rules.
- Vector DB for similarity retrieval:
  - keyframe embeddings
  - LLM-description embeddings
  - style-pack embeddings

### Store per analyzed video
- `style_signature`
- evidence with timestamps/examples
- confidence scores per label

Enables queries such as:
- videos similar to this
- references with `glow_trace`
- generate a spot with this extracted system

## Example final contract summary

```json
{
  "schema_version": "1.0",
  "video": {
    "duration_ms": 0,
    "fps": 0,
    "resolution": {"w": 0, "h": 0},
    "aspect_ratio": "16:9"
  },
  "style_system": {
    "style_family": [{"id": "ui_saas_glow", "confidence": 0.92}],
    "color": {
      "background": ["#0B0B10"],
      "primary": ["#7C4DFF"],
      "accent": ["#FF8A00", "#00D1C1"],
      "gradients": [
        {"type": "linear", "stops": [{"hex":"#FF8A00","pos":0},{"hex":"#7C4DFF","pos":1}]}
      ]
    },
    "typography": {
      "families": [{"name_guess":"Inter/Neue Haas Grotesk-like","role":"primary_ui","confidence":0.7}],
      "treatments": ["bold_headlines", "outlined_shadow_type", "kinetic_type"]
    },
    "composition": {
      "grid": {"type":"12-col","margin_pct":8},
      "patterns": ["centered_hero", "floating_cards", "safe_area_large"]
    },
    "motion": {
      "tempo": {"avg_shot_ms": 900, "energy":"high"},
      "easing": ["easeOutCubic", "spring_soft"],
      "transitions": [{"type":"glow_wipe","confidence":0.6},{"type":"cut","confidence":0.9}],
      "primitives": ["slide_in", "scale_pop", "stagger", "glow_trace", "blur_in"]
    },
    "materials_3d": ["glass", "matte_plastic"],
    "fx": ["bloom", "grain_subtle", "soft_shadow", "neon_glow"]
  },
  "shots": [
    {
      "id": "S01",
      "start_ms": 0,
      "end_ms": 1200,
      "on_screen_text": [{"text":"The future of B2B sales is here","bbox":[]}],
      "dominant_palette": ["#0B0B10","#7C4DFF","#FF8A00"],
      "motion_notes": ["headline fades in + glow underline left-to-right"]
    }
  ],
  "evidence": {
    "keyframes": [{"shot_id":"S01","frame_path":"..."}],
    "timestamps": [{"tag":"glow_trace","at_ms":420}]
  }
}
```
