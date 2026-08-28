#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.qa.alignment import validate_canonical_truth

errors = []
warnings = []
required = [
    'AGENTS.md', 'GOAL.md', 'STATE.md', 'HANDOFF.md', 'TASKS.md', 'DECISIONS.md',
    'state/project_state.json', 'state/checkpoints.json', 'state/github_sync.json',
    'state/drive_sync.json', 'registry/artifact_registry.json', 'src/graph/model.py',
    'tests/test_graph.py'
]
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f'missing:{rel}')

if not errors:
    state = json.loads((ROOT / 'state/project_state.json').read_text())
    registry = json.loads((ROOT / 'registry/artifact_registry.json').read_text())
    gh = json.loads((ROOT / 'state/github_sync.json').read_text())

    if state.get('release_status') not in {'BLOCKED', 'READY', 'RELEASED'}:
        errors.append('invalid_release_status')
    if registry.get('schema_version') != '2.0':
        errors.append('artifact_registry_not_v2')
    if any(not a.get('drive_file_id') for a in registry.get('artifacts', [])):
        errors.append('artifact_without_drive_id')
    if not gh.get('full_source_import_complete'):
        warnings.append('github_full_source_import_flag_false')
    if gh.get('main_contains_full_source') is False:
        warnings.append('main_not_yet_promoted')

    truth = validate_canonical_truth(
        ROOT / 'state/project_state.json',
        ROOT / 'state/checkpoints.json',
        ROOT / 'STATE.md',
        ROOT / 'TASKS.md',
        ROOT / 'HANDOFF.md',
    )
    errors.extend(f'canonical_truth:{item}' for item in truth['errors'])

print(json.dumps({'ok': not errors, 'errors': errors, 'warnings': warnings}, indent=2))
sys.exit(1 if errors else 0)
