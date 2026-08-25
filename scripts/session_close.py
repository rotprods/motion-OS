from pathlib import Path
import argparse, subprocess, json, datetime
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
steps=[]
def run(name,cmd,required=True):
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    steps.append({"name":name,"rc":r.returncode,"stdout":r.stdout[-4000:],"stderr":r.stderr[-2000:]})
    if required and r.returncode: raise SystemExit(json.dumps({"failed":name,"steps":steps},indent=2))
run("tests",["python","-m","pytest","-q"])
run("reconcile",["python","scripts/reconcile_planes.py"])
head=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True).stdout.strip()
state=json.loads((ROOT/"state/project_state.json").read_text())
reg=json.loads((ROOT/"registry/artifact_registry.json").read_text())
for a in reg.get("artifacts",[]): a["git_sha"]=head
manifest={"closed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"git_sha":head,"working_master":state.get("working_master"),"release_status":state.get("release_status"),"artifacts":[{"artifact_id":a["artifact_id"],"sha256":a.get("sha256"),"drive_file_id":a.get("drive_file_id")} for a in reg.get("artifacts",[])],"dry_run":args.dry_run,"steps":steps}
if not args.dry_run: (ROOT/"state/session_close_manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
