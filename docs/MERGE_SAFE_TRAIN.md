# MOTION.OS — Local-First CI + Merge-Safe Train

## Objective
Keep `main` continuously releasable without paying GitHub Actions to repeat work that agents can prove locally.

## Authority model
1. **Local verification is the default execution surface.** Agents run the relevant profile before pushing.
2. **GitHub Actions is merge authority, not the primary test workstation.** Cloud CI proves reproducibility on a clean runner.
3. **`MERGE_SAFE` is the single required merge check.** It always runs a cheap Python 3.12 contract gate and selectively runs expensive analysis/Remotion/security gates only when affected paths change.
4. **Merge queue / merge-group is the final train.** A merge-group run forces Python 3.11 compatibility plus analysis, Remotion and dependency security regardless of path classification.
5. Existing legacy workflows remain manual/scheduled escape hatches and must not be configured as required PR checks after `MERGE_SAFE` is active.

## One-time local bootstrap

```bash
python -m pip install -e '.[dev,analysis]'
pip install pip-audit
cd runtime/remotion && npm install --no-audit --no-fund && cd ../..
python scripts/install_git_hooks.py
```

The installer configures `core.hooksPath=.githooks`. The tracked `pre-push` hook runs `quick` on every push and automatically escalates to analysis, Remotion or dependency security when the changed paths require them. This is the preferred default: agents should not need to remember which test suite to run manually.

## Local commands
The hook is authoritative for normal push-time local checks; these commands remain available for explicit execution:

```bash
# Most changes
python scripts/local_verify.py quick

# Extraction / normalization / media changes
python scripts/local_verify.py analysis

# Remotion/compiler/runtime changes
python scripts/local_verify.py remotion

# Dependency/security changes
python scripts/local_verify.py security

# Before marking a risky PR ready
python scripts/local_verify.py merge
```

`merge` deliberately exercises all locally available gates. If `pip-audit` is not installed it warns rather than fabricating a pass; the pre-push hook is stricter and blocks dependency/security-sensitive pushes until `pip-audit` exists.

## Cost policy
- Do not use cloud CI as an interactive debugger.
- Push only after the relevant local profile passes; install the pre-push hook in every working checkout/agent workspace.
- `cancel-in-progress: true` cancels obsolete cloud runs after a new commit.
- Python 3.11 compatibility is deferred to the merge train instead of every PR commit.
- Physical analysis runs only for extraction/normalization/media dependency changes, except merge train where it is mandatory.
- Physical Remotion rendering runs only for runtime/compiler changes, except merge train where it is mandatory.
- Dependency audit runs on relevant dependency/workflow changes, at merge train, and weekly scheduled baseline.
- Runtime evidence artifacts retain 7 days in PR CI; manual proof retains 14 days.
- Legacy `CI`, `Repo Health`, `Runtime Smoke` and `Remotion Runtime` workflows are manual-only after consolidation; they exist for diagnostics, not every commit.

## Merge train protocol
Repository settings should require **only** the `Merge Safe / MERGE_SAFE` status for `main` and enable GitHub Merge Queue if the plan supports it.

Train lifecycle:

```text
pre-push local hook PASS
  -> PR
  -> MERGE_SAFE selective clean-runner proof
  -> code/security review
  -> Ready
  -> merge queue
  -> merge_group full gate (3.11 + 3.12 + analysis + Remotion + security)
  -> merge to main
  -> agent emits pr.merged / main.verified event
```

If GitHub Merge Queue is unavailable on the account/repository plan, serialize merges manually: update each candidate against current `main`, wait for `MERGE_SAFE` on the resulting synthetic merge, merge exactly one PR, then revalidate the next candidate. Do not batch blind merges.

## Agent event bus
The durable bus is **one immutable JSON file per event** under:

`state/agent_events/YYYY-MM-DD/<event_id>.json`

This is intentionally not one shared JSONL file: separate immutable files minimize merge conflicts between concurrent agents.

Emit at minimum:

```bash
python scripts/agent_event.py emit work.started --agent-id <agent> --summary "..." --authority IMPLEMENTED
python scripts/agent_event.py emit work.completed --agent-id <agent> --summary "..." --authority VERIFIED
```

For PR lifecycle emit `pr.opened`, `pr.ready`, `pr.merged`, and after canonical reconciliation emit `main.verified`.

CI validates the entire bus schema and duplicate event IDs. Events are facts/evidence; they do not silently mutate canonical `STATE.md`, `TASKS.md`, plans, or release state.

## Branch ownership / collision control
- One workstream = one branch.
- Before editing, read `AGENTS.md`, `state/project_state.json`, `STATE.md`, `GOAL.md`, `TASKS.md`, relevant plans, and the latest event-bus entries for affected paths.
- Emit `work.started` with affected paths before substantial work.
- Never force-update another active agent's branch.
- If a branch becomes stale against `main`, reconcile before promotion; do not overwrite concurrent work.

## Main hygiene
`main` must contain only verified/canonical code and documentation. Historical branches/PRs may remain as evidence but should be closed as superseded rather than merged wholesale when their valid capabilities are already represented in `main`.

## Required repository-setting change
The GitHub connector cannot mutate branch-protection/ruleset configuration in this environment. A repository admin must configure `main` once:

- require pull request before merge;
- require `Merge Safe / MERGE_SAFE`;
- require branch to be up to date / enable merge queue when available;
- disallow force pushes and deletion of `main`;
- dismiss stale approvals when new commits are pushed if human approval is required;
- do **not** require the legacy manual workflows.

Until that setting is confirmed, agents must treat the merge train as an operating rule rather than assuming GitHub enforces it.
