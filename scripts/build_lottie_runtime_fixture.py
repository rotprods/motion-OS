from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.compilers.lottie import compile_vector_subgraph_to_lottie, player_roundtrip_contract

OUT = ROOT / "runtime" / "lottie"


def _ring_shapes() -> list[dict]:
    """One visible animated ring using canonical Lottie shape primitives."""
    return [
        {
            "ty": "gr",
            "nm": "Animated Ring",
            "it": [
                {
                    "d": 1,
                    "ty": "el",
                    "s": {"a": 0, "k": [180, 180]},
                    "p": {"a": 0, "k": [0, 0]},
                    "nm": "Ellipse Path 1",
                },
                {
                    "ty": "st",
                    "c": {"a": 0, "k": [1.0, 0.26, 0.08, 1.0]},
                    "o": {"a": 0, "k": 100},
                    "w": {"a": 0, "k": 18},
                    "lc": 2,
                    "lj": 2,
                    "ml": 4,
                    "bm": 0,
                    "nm": "Stroke 1",
                },
                {
                    "ty": "tm",
                    "s": {"a": 0, "k": 0},
                    "e": {
                        "a": 1,
                        "k": [
                            {
                                "i": {"x": [0.667], "y": [1.0]},
                                "o": {"x": [0.333], "y": [0.0]},
                                "t": 0,
                                "s": [5],
                                "e": [100],
                            },
                            {"t": 59, "s": [100]},
                        ],
                    },
                    "o": {"a": 0, "k": 0},
                    "m": 1,
                    "nm": "Trim Paths 1",
                },
                {
                    "ty": "tr",
                    "p": {"a": 0, "k": [0, 0]},
                    "a": {"a": 0, "k": [0, 0]},
                    "s": {"a": 0, "k": [100, 100]},
                    "r": {"a": 0, "k": 0},
                    "o": {"a": 0, "k": 100},
                    "sk": {"a": 0, "k": 0},
                    "sa": {"a": 0, "k": 0},
                    "nm": "Transform",
                },
            ],
        }
    ]


def _html() -> str:
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#090909}
#stage{width:640px;height:360px}
</style>
</head>
<body>
<div id="stage"></div>
<script src="./lottie.min.js"></script>
<script>
(async () => {
  const params = new URLSearchParams(window.location.search);
  const requestedFrame = Number(params.get('frame') || '0');
  const data = await fetch('./animation.json').then((response) => {
    if (!response.ok) throw new Error('animation fetch failed');
    return response.json();
  });
  const animation = lottie.loadAnimation({
    container: document.getElementById('stage'),
    renderer: 'svg',
    loop: false,
    autoplay: false,
    animationData: JSON.parse(JSON.stringify(data)),
  });
  animation.addEventListener('DOMLoaded', () => {
    animation.goToAndStop(requestedFrame, true);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      document.documentElement.dataset.ready = 'true';
      document.documentElement.dataset.requestedFrame = String(requestedFrame);
      document.documentElement.dataset.currentFrame = String(Math.round(animation.currentFrame));
      document.documentElement.dataset.totalFrames = String(Math.round(animation.totalFrames));
      document.documentElement.dataset.svgCount = String(document.querySelectorAll('#stage svg').length);
    }));
  });
})().catch((error) => {
  document.documentElement.dataset.ready = 'error';
  document.documentElement.dataset.errorType = error && error.name ? error.name : 'Error';
});
</script>
</body>
</html>
"""


def build_fixture(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    doc = compile_vector_subgraph_to_lottie(
        [
            {
                "id": "runtime_ring",
                "type": "shape",
                "features": ["transform", "stroke", "trim_path"],
                "data": {
                    "transform": {"position": [320, 180, 0]},
                    "shapes": _ring_shapes(),
                },
            }
        ],
        width=640,
        height=360,
        fps=30,
        in_frame=0,
        out_frame=60,
        markers=[{"tm": 0, "cm": "start", "dr": 0}, {"tm": 59, "cm": "end", "dr": 0}],
    )
    contract = player_roundtrip_contract(doc, player="lottie-web")
    animation_json = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    animation_bytes = animation_json.encode("utf-8")
    (out / "animation.json").write_bytes(animation_bytes)
    (out / "player_contract.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "index.html").write_text(_html(), encoding="utf-8")
    evidence = {
        "schema": "motion-os.lottie-compiler-fixture/v1",
        "document_sha256": contract["document_sha256"],
        "animation_file_sha256": hashlib.sha256(animation_bytes).hexdigest(),
        "expected_frame_count": contract["expected_frame_count"],
        "stable_layer_ids": contract["stable_layer_ids"],
        "authority": "compiler_ready",
    }
    (out / "compiler_evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    evidence = build_fixture(OUT)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
