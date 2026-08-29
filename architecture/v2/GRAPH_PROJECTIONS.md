# MOTION.OS V2 — Required Graph Projections

Authority: `PROPOSED_V2_CANDIDATE`
Source: shared IDs in `hypergraph.snapshot.json`, `state/v2/tasks.json`, live GitHub/event evidence.

These are **projections of shared canonical IDs**, not independent truth stores. They can be materialized in COS/GraphRAG/UI later; the semantic model must remain rebuildable from authority.

## 1. System Graph

```mermaid
flowchart LR
  Brief --> Content --> Studio --> Renderer --> TemporalQA --> Empirical --> Release
  AuthorityKernel --> Content
  AuthorityKernel --> Studio
  AuthorityKernel --> Renderer
  AuthorityKernel --> TemporalQA
  EventFabric --> AuthorityKernel
  Evidence --> AuthorityKernel
  AuthorityKernel --> COS
```

## 2. Dependency Graph

```mermaid
flowchart LR
  Truth[#56 truth] --> Event[#58 Event Fabric]
  Event --> Auto[#68 autonomy]
  QA[#59 QA history] --> Critic[#65 temporal critic]
  Frame[#64 decoded frame authority] --> Critic
  HFX[#62 HyperFrames provenance] --> Critic
  Audio[#61 master audio] --> Composite[final assembly]
  Alpha[#63 semantic alpha] --> Composite
  Color[#69 color normalization] --> Composite
  Composite --> Critic --> Bench[#75 empirical benchmark] --> Release
```

## 3. Execution Graph

```mermaid
flowchart TD
  Goal[North Star] --> M0[V2 truth/graph]
  M0 --> M1[Authority core]
  M1 --> M2[Render/repair truth]
  M2 --> M3[Temporal intelligence]
  M3 --> M4[Empirical authority]
  M4 --> M5[Security/recovery]
  M5 --> M6[Migration/production]
  M6 --> CP14[Production Authority]
```

## 4. Agent Graph

```mermaid
flowchart LR
  Project --> Agent
  Agent --> Session
  Session --> Workstream
  Session --> Claim
  Claim --> Scope
  Session --> Checkpoint
  Session --> Handoff
  Handoff --> NextSession
  EventFabric --> Session
```

## 5. Session Graph

```mermaid
flowchart LR
  ProjectID --> AgentID --> SessionID --> WorkstreamID --> ObjectiveID --> CorrelationID
  SessionID --> ContextPack
  ContextPack --> MainSHA
  ContextPack --> EventWatermark
  SessionID --> Event
  Event --> Evidence
  Event --> NextSafeAction
```

## 6. Knowledge Graph

```mermaid
flowchart LR
  Source --> Fact
  Source --> Claim
  Claim --> Evidence
  Claim --> Assumption
  Assumption --> Risk
  Claim --> Decision
  Decision --> Contract
  Contract --> Module
  Decision --> Alternative
  Decision --> Consequence
```

## 7. Decision Graph

```mermaid
flowchart LR
  Problem --> Decision
  Constraint --> Decision
  AlternativeA --> Decision
  AlternativeB --> Decision
  Evidence --> Decision
  Decision --> SelectedOption
  Decision --> Tradeoff
  Decision --> Risk
  Risk --> Mitigation
  Trigger --> ReconsiderDecision
```

## 8. Risk Graph

```mermaid
flowchart LR
  TruthDrift --> FalseAuthority --> BadPromotion
  MainUnprotected --> BadPromotion
  EvidenceMismatch --> BadPromotion
  FrameAmbiguity --> TemporalError --> BadPromotion
  GenericCreativeOutput --> NorthStarFailure
  NonReproducibleNode --> RendererDrift --> BadPromotion
  BadPromotion --> ReleaseRisk
```

## 9. Test Graph

```mermaid
flowchart LR
  Invariant --> Unit
  Invariant --> Contract
  Invariant --> Property
  Invariant --> Mutation
  Invariant --> Integration
  Invariant --> E2E
  Invariant --> Security
  Invariant --> Recovery
  HistoricalBug --> RegressionTest
  RegressionTest --> FailureFamily
  FailureFamily --> Property
```

## 10. Evidence Graph

```mermaid
flowchart LR
  SourceRevision --> EvidenceEnvelope
  SpecHash --> EvidenceEnvelope
  RuntimeVersion --> EvidenceEnvelope
  RunID --> EvidenceEnvelope
  ArtifactHash --> EvidenceEnvelope
  ProviderRun --> EvidenceEnvelope
  EvidenceEnvelope --> Verification
  Verification --> AuthorityState
  AuthorityState --> ReleaseDecision
```

## 11. Artifact Graph

```mermaid
flowchart LR
  SourcePack --> Script --> AvatarArtifact
  SceneSpec --> RendererArtifact
  AvatarArtifact --> Assembly
  RendererArtifact --> Assembly
  MasterAudio --> Assembly
  Assembly --> MasterMedia
  MasterMedia --> TemporalEvidence
  MasterMedia --> ReleaseManifest
  MasterMedia --> RollbackArtifact
```

## 12. Workflow Graph

```mermaid
flowchart LR
  Observe --> ProjectState --> SelectTask --> Claim --> Implement --> LocalVerify --> AdversarialVerify --> Review --> Checkpoint --> Reconcile
  Reconcile -->|safe work remains| SelectTask
  Reconcile -->|irreversible| Preflight
  Preflight -->|fresh + conflict-free + evidence| Promote
  Preflight -->|stale/conflict| Block
```

## 13. State Graph

```mermaid
stateDiagram-v2
  [*] --> PROPOSED
  PROPOSED --> IMPLEMENTED
  IMPLEMENTED --> EXECUTED
  EXECUTED --> VERIFIED
  VERIFIED --> EMPIRICALLY_QUALIFIED
  PROPOSED --> BLOCKED
  IMPLEMENTED --> BLOCKED
  EXECUTED --> BLOCKED
  VERIFIED --> BLOCKED
  BLOCKED --> IMPLEMENTED: blocker resolved
  VERIFIED --> SUPERSEDED
  EMPIRICALLY_QUALIFIED --> SUPERSEDED
  EXECUTED --> DEGRADED_EXTERNAL
  DEGRADED_EXTERNAL --> EXECUTED: dependency restored
```

## 14. Recovery Graph

```mermaid
flowchart LR
  GitHistory --> Replay
  ImmutableEvents --> Replay
  DomainState --> Replay
  EvidenceManifests --> Replay
  Replay --> StateSnapshot
  Replay --> CoordinationGraph
  Replay --> COSGraph
  StateSnapshot --> NewContextPack
  LiveGitHub --> ReconcileRecovery
  NewContextPack --> ReconcileRecovery
  ReconcileRecovery --> NextSafeAction
  MissingDrive --> DegradedExternal
```

## 15. Security Graph

```mermaid
flowchart LR
  ExternalInput --> TrustBoundary --> Validator --> Domain
  ProviderResponse --> TrustBoundary
  URL --> SSRFBoundary --> Fetcher
  AgentEvent --> AuthorityBoundary --> EventFabric
  Artifact --> HashBoundary --> EvidenceEnvelope
  SpendRequest --> SpendBoundary --> Provider
  Secret --> Redaction
  SupplyChain --> LockAndAudit
  Attack --> Detection --> Block --> Recovery
```

## 16. Architecture Graph

```mermaid
flowchart TB
  AuthorityKernel --> ContentIntelligence
  AuthorityKernel --> StudioRuntime
  AuthorityKernel --> RendererFabric
  AuthorityKernel --> TemporalQA
  AuthorityKernel --> AgentRuntime
  ContentIntelligence --> StudioRuntime
  StudioRuntime --> RendererFabric
  RendererFabric --> TemporalQA
  TemporalQA --> EmpiricalQualification
  AgentRuntime --> EventFabric
  EventFabric --> AuthorityKernel
  EvidencePlane --> AuthorityKernel
  AuthorityKernel --> DerivedCOS
```

## 17. Historical Graph

```mermaid
flowchart LR
  Bootstrap --> RC06 --> CreativeConvergence
  Bootstrap --> RemotionExperiment --> PR42VerifiedRemotion
  CreativeConvergence --> Phase06ContentAvatar --> PR37
  Phase06ContentAvatar --> Phase07Coordination --> PR44
  PR44 --> MergeSafeEventBus --> PR46
  PR46 --> CombinedHeadInvariant --> PR47
  PR47 --> EventFabricRefine --> PR58
  PR58 --> V2AuthorityModel --> PR90
  HistoricalBugCorpus --> V2AuthorityModel
```

## 18. Roadmap Graph

```mermaid
flowchart LR
  CP0 --> CP1 --> CP2 --> CP3 --> CP4 --> CP5 --> CP6 --> CP7 --> CP8 --> CP9 --> CP10 --> CP11 --> CP12 --> CP13 --> CP14
  Truth --> EventFabric --> QAFrameTemporal --> RendererConvergence --> RealMaster --> CreativeTournament --> EmpiricalSuite --> SecurityRecovery --> Migration --> Production
```

## 19. Product / Creative Quality Graph — domain L17

```mermaid
flowchart LR
  Brief --> NarrativeIntent --> VisualDNA --> Composition --> MotionFunction --> AudioFunction --> TemporalPacing --> CreativeCritic --> Repair --> Master
  Master --> SemanticScore
  Master --> CreativeDirectorScore
  Master --> StyleFidelity
  SemanticScore --> ProductNorthStar
  CreativeDirectorScore --> ProductNorthStar
  StyleFidelity --> ProductNorthStar
```

## 20. Empirical Learning Graph — domain L18

```mermaid
flowchart LR
  Publication --> Observation --> PerformanceEvidence --> LearningCandidate
  LearningCandidate --> ControlledExperiment
  ControlledExperiment -->|supported| PromotedRule
  ControlledExperiment -->|not supported| RejectedRule
  PromotedRule --> FutureStrategy
  FutureStrategy --> Publication
```

## 21. Release Authority Graph — domain L19

```mermaid
flowchart LR
  MainFresh --> Gate
  EventFresh --> Gate
  SecurityPass --> Gate
  RecoveryPass --> Gate
  RendererEvidence --> Gate
  TemporalEvidence --> Gate
  CreativeEvidence --> Gate
  EmpiricalEvidence --> Gate
  ProvenanceComplete --> Gate
  AdminGovernance --> Gate
  Gate -->|ALL| ProductionAuthority
  Gate -->|ANY missing| Blocked
```

## Projection law

Every projection is invalidated when any of its source revisions/watermarks change. Similarity, GraphRAG, dashboards and graph traversal may help discover relationships but cannot invent authority. A projection that cannot be deterministically rebuilt from its declared source set is a V2 defect.