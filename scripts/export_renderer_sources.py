#!/usr/bin/env python3
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.agents.pipeline import normalize_brief,choose_style,storyboard
from src.renderers.source_generators import generate_hyperframes_project,generate_remotion_project
raw=json.loads((ROOT/'examples/benchmark_brief.json').read_text()); brief=normalize_brief(raw); style=choose_style(brief); beats=storyboard(brief,style)
out=ROOT/'generated'/'renderer_sources';generate_hyperframes_project(out/'hyperframes',brief,style,beats);generate_remotion_project(out/'remotion',brief,style,beats);print(out)
