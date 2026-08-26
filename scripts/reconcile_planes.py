from pathlib import Path
import json, subprocess, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]; errors=[]; warnings=[]
required=['AGENTS.md','GOAL.md','STATE.md','HANDOFF.md','TASKS.md','DECISIONS.md','state/project_state.json','registry/artifact_registry.json']
for r in required:
    if not (ROOT/r).exists(): errors.append(f'missing:{r}')
state=json.loads((ROOT/'state/project_state.json').read_text()); reg=json.loads((ROOT/'registry/artifact_registry.json').read_text()); wm=state.get('working_master')
if wm and not (ROOT/wm).exists(): errors.append(f'working_master_missing:{wm}')
if reg.get('schema_version')!='2.0': warnings.append('registry_schema_not_v2')
git=lambda *a: subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)
if git('rev-parse','--is-inside-work-tree').returncode!=0: errors.append('not_git_repo')
else:
    if git('status','--porcelain').stdout.strip(): warnings.append('dirty_worktree')
    remote=git('remote','get-url','origin')
    if remote.returncode!=0 or 'github.com/rotprods/motion-OS' not in remote.stdout: warnings.append('origin_not_github')
def sha(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()
for a in reg['artifacts']:
    p=ROOT/a['local_path']
    if p.exists() and sha(p)!=a['sha256']: errors.append(f"hash_mismatch:{a['artifact_id']}")
ghsync=ROOT/'state/github_sync.json'
if ghsync.exists():
    gh=json.loads(ghsync.read_text())
    if not gh.get('full_source_import_complete'): warnings.append('github_full_source_import_incomplete')
else: warnings.append('github_sync_state_missing')
if not (ROOT/'state/drive_sync.json').exists(): warnings.append('drive_sync_state_missing')
print(json.dumps({'ok':not errors,'errors':errors,'warnings':warnings},indent=2)); sys.exit(1 if errors else 0)
