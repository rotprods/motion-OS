# MOTION.OS Multi-Agent Coordination — Adversarial Gauntlet

Purpose: try to break the coordination system before authority promotion.

## A. Identity / session attacks
1. Can two agents accidentally register the same display name but different canonical identities?
2. Can a dead session impersonate a new session?
3. Can an unknown runtime become authoritative without a capability/policy record?
4. Can a session reuse an old ContextPack after main changes?
5. Can a session reuse another agent's lease ID/token?

## B. Lease / fencing races
6. Two hosts request WRITE on the same canonical resource at the same millisecond. Can both succeed?
7. Host A's lease expires; B takes over; A wakes up and writes. Is A fenced?
8. A heartbeat arrives after takeover. Can it resurrect the old lease?
9. EXCLUSIVE_WRITE exists; can a new READ sneak in?
10. WRITE exists; can another WRITE enter through an alias resource URI?
11. Can `tree:` and `file:` aliases evade exact-resource DB locking?
12. Can resource canonicalization differences (`src/a`, `src//a`, case, symlink semantics) create split locks?

## C. Event integrity
13. Same event delivered twice: can side effects duplicate?
14. Same event_id with different payload: does system fail closed?
15. Same provenance hash with different event_id: is it deduplicated consistently?
16. Events arrive out of occurrence order: can read models remain deterministic?
17. Causation references a missing event: quarantine or tolerate?
18. Event schema version unknown: fail/upgrade/quarantine?
19. Event append succeeds but dispatcher crashes before publish: recover?
20. Dispatcher publishes but crashes before mark-published: duplicate publish safe?

## D. Outbox / consumer attacks
21. Two dispatchers claim the same outbox batch: does leased SKIP LOCKED behavior isolate them?
22. Dispatcher lease expires mid-publish: can stale worker mark published?
23. Consumer processes event then crashes before ack: retry side effect safe?
24. Consumer tries to rewind offset: rejected?
25. Consumer offset points to deleted/missing event: impossible under append-only policy?

## E. Context corruption
26. Graph is two seconds behind DB; ContextPack compiles anyway. Is lag exposed/gated?
27. GitHub PR merges after pack compile. Is pack invalidated?
28. Drive artifact revision changes. Is pack invalidated?
29. A sensitive node leaks into a lower-sensitivity agent pack. Fail closed?
30. Graph returns a dependency but source revision hash differs. Which wins?
31. Context budget truncation removes a critical blocker. Does compiler preserve mandatory invariants first?

## F. Graph correctness
32. Rebuild from identical event sequence twice: identical hash?
33. Rebuild after duplicate events: identical logical projection?
34. Reverse traversal returns a different dependency set than forward edge inversion?
35. COS loses state/restarts: can complete projection rebuild recover without authority loss?
36. COS unavailable: can coordination continue safely without graph-assisted writes?
37. COS returns stale projection hash: authoritative ContextPack rejected?

## G. Git / PR concurrency
38. #34 merges while #35 is active. Does #35 become stale before next authoritative change?
39. #37 changes avatar-handoff contract without touching any #35 file. Is semantic collision still detected?
40. Two branches change different files but the same schema semantics. Does contract governance catch it?
41. Agent sees mergeable=true and assumes verified. Is merge gated by evidence?
42. A PR is closed but not merged. Does graph distinguish those states?
43. One agent rebases and silently drops another contract fix. Can lineage/evidence expose it?

## H. Drive / artifact failures
44. Artifact ref exists but file is deleted. Does checkpoint completion remain valid?
45. Same artifact title points to different IDs. Does canonical ID prevent ambiguity?
46. Drive mirror is newer than GitHub canonical command. Does reconciliation fail closed rather than merge blindly?
47. Heavy artifact hash differs from registry hash. Is it quarantined?

## I. Security / policy
48. Can anonymous/public client append coordination events?
49. Can agent A read CONFIDENTIAL events for agent B/project B?
50. Can user-provided source inject a fake coordination command into privileged prompts?
51. Can event payload contain provider credentials and become graph/context data?
52. Can SQL functions bypass RLS through SECURITY DEFINER accidentally?
53. Are unknown policy operators denied?
54. Can a malicious resource URI cause lock collision/DoS via advisory hash abuse?

## J. Partial failures / recovery
55. DB transaction commits state+event but API response is lost. Retry idempotent?
56. DB is available, realtime is down. Correctness preserved?
57. Realtime available, DB transaction failed. No phantom event?
58. Agent crashes with active leases. Takeover after TTL works?
59. Agent completes code but fails checkpoint publication. Work remains non-complete?
60. Projection build fails halfway. Previous projection remains active?
61. Schema migration partially applies. Startup qualification detects mismatch?

## K. Human/operator failures
62. Human manually edits ACTIVE_AGENTS.yaml after DB authority exists. Is it treated as replica, not truth?
63. Human marks task complete without evidence. Gate rejects authority promotion?
64. Two humans intentionally override a conflict. Is decision/provenance recorded?
65. Emergency force-unlock occurs. Is blast radius/audit trail explicit?

## Qualification campaign
Minimum before `COORDINATION_AUTHORITY`:
- deterministic unit/property tests for A–F;
- real PostgreSQL integration tests for B–D/J;
- GitHub connector integration for G;
- Drive reconciliation tests for H;
- negative auth/RLS tests for I;
- 3-agent zero-context live drill for K + end-to-end.

Every failed case becomes a tracked issue or explicit accepted-risk decision. No silent waiver.
