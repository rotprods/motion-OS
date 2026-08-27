# MOTION.OS Agent Coordination Protocol

Status: REQUIRED WHEN PHASE07 MERGES

## Session start
Every agent must:
1. Read AGENTS.md, GOAL.md, STATE.md, TASKS.md, HANDOFF.md.
2. Read `coordination/ACTIVE_AGENTS.yaml`.
3. Read the latest coordination bus checkpoint.
4. Inspect relevant PRs, contracts and active leases.
5. Register a session identity.
6. Declare intended scope before changing files.
7. Acquire a lease for mutable shared scope when the durable kernel is available.
8. Compile/record the ContextPack hash used for the session.

## Structured bus messages
Use this envelope in the interim GitHub Coordination Bus:

```yaml
kind: HELLO|CLAIM|HEARTBEAT|BLOCKED|DECISION|RELEASE|CHECKPOINT|CONFLICT
agent_id: motion://agent/<id>
session_id: motion://session/<id>
timestamp: <ISO8601>
branch: <branch>
pr: <number|null>
correlation_id: <stable work id>
causation_id: <prior event/comment id|null>
scope:
  - <resource URI>
expected_revision: <git sha / contract revision / null>
summary: <one paragraph>
evidence:
  - <url/hash/ref>
next:
  - <next action>
```

## Collision policy
- Never infer ownership from branch names alone.
- Read/read requires no exclusive lease.
- Write intent must be declared.
- Write/write overlap must be resolved before authoritative mutation.
- If a conflicting active claim exists, split scope, wait, or explicitly hand off.
- A stale session may continue local analysis but cannot make an authoritative write after its expected revision or lease token is stale.

## Checkpoint discipline
A checkpoint is required when:
- session ends;
- task becomes blocked;
- a contract/schema changes;
- a PR becomes ready/merged;
- control transfers to another agent;
- a long task reaches a recoverable boundary.

Checkpoint must include:
- what was attempted;
- exact branch/PR/SHA;
- files/contracts touched;
- tests/evidence run;
- state: PROPOSED|IMPLEMENTED|EXECUTED|VERIFIED;
- unresolved risks;
- active lease releases;
- next exact action.

## Completion semantics
`COMPLETED` is forbidden when a critical downstream gate failed, evidence is absent, or a required handoff is missing. Use `BLOCKED`, `IMPLEMENTED_UNVERIFIED`, or `PARTIAL` instead.

## Contract change protocol
Before changing a shared schema/API/manifest/entrypoint:
1. publish CLAIM with `contract:<name>` scope;
2. query/inspect dependent PRs/tasks;
3. record expected old revision;
4. make additive/backward-compatible changes where possible;
5. emit DECISION describing migration/compatibility;
6. invalidate stale ContextPacks;
7. release contract lease after evidence.

## Cross-PR rule
PR #34, #35 and #37 are concurrent workstreams, not isolated universes. Any change affecting renderer contracts, Studio handoff, content manifests, provenance roots, replay fingerprints, beat identity or authority semantics must be announced on the coordination bus before merge.
