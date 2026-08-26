-- MOTION.OS Agentic Event Kernel — target Postgres/Supabase contract
-- DESIGN CONTRACT ONLY in this PR. Do not apply to an unrelated project.

create extension if not exists pgcrypto;

create table if not exists motion_agent_events (
  sequence_id bigint generated always as identity primary key,
  event_id uuid not null default gen_random_uuid(),
  schema_version text not null,
  project_id text not null,
  actor_id text not null,
  session_id text,
  event_type text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  aggregate_revision bigint not null check (aggregate_revision >= 0),
  expected_revision bigint,
  causation_id uuid,
  correlation_id uuid not null,
  workstream_id text,
  resource_scope jsonb not null default '[]'::jsonb,
  git_ref jsonb,
  observed_at timestamptz,
  recorded_at timestamptz not null default now(),
  idempotency_key text not null,
  payload_hash text not null check (payload_hash ~ '^[0-9a-f]{64}$'),
  payload jsonb not null,
  provenance jsonb not null,
  sensitivity text not null default 'INTERNAL' check (sensitivity in ('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED')),
  evidence jsonb not null default '[]'::jsonb,
  unique(project_id, event_id),
  unique(project_id, idempotency_key),
  unique(project_id, aggregate_type, aggregate_id, aggregate_revision)
);

create index if not exists idx_motion_events_project_sequence
  on motion_agent_events(project_id, sequence_id);
create index if not exists idx_motion_events_correlation
  on motion_agent_events(project_id, correlation_id, sequence_id);
create index if not exists idx_motion_events_aggregate
  on motion_agent_events(project_id, aggregate_type, aggregate_id, aggregate_revision);
create index if not exists idx_motion_events_workstream
  on motion_agent_events(project_id, workstream_id, sequence_id) where workstream_id is not null;

create table if not exists motion_aggregate_heads (
  project_id text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  revision bigint not null check (revision >= 0),
  last_event_id uuid not null,
  updated_at timestamptz not null default now(),
  primary key(project_id, aggregate_type, aggregate_id)
);

create table if not exists motion_agent_sessions (
  project_id text not null,
  session_id text not null,
  actor_id text not null,
  workstream_id text,
  branch text,
  base_sha text,
  started_at timestamptz not null default now(),
  heartbeat_at timestamptz,
  ended_at timestamptz,
  state text not null check (state in ('ACTIVE','HANDED_OFF','ENDED','ABANDONED')),
  context_pack_hash text,
  event_watermark bigint,
  primary key(project_id, session_id)
);

create table if not exists motion_resource_leases (
  project_id text not null,
  resource_key text not null,
  lease_id uuid not null default gen_random_uuid(),
  owner_agent_id text not null,
  session_id text not null,
  workstream_id text not null,
  branch text,
  pr_number integer,
  generation bigint not null check (generation >= 1),
  expected_state_version bigint,
  semantic_scope jsonb not null default '[]'::jsonb,
  path_scope jsonb not null default '[]'::jsonb,
  acquired_at timestamptz not null default now(),
  heartbeat_at timestamptz,
  expires_at timestamptz not null,
  released_at timestamptz,
  state text not null check (state in ('ACTIVE','RELEASED','EXPIRED','REVOKED')),
  primary key(project_id, resource_key),
  unique(project_id, lease_id)
);

create index if not exists idx_motion_leases_active_expiry
  on motion_resource_leases(project_id, expires_at)
  where state = 'ACTIVE';

create table if not exists motion_consumer_offsets (
  project_id text not null,
  consumer_id text not null,
  last_sequence_id bigint not null default 0,
  updated_at timestamptz not null default now(),
  primary key(project_id, consumer_id)
);

create table if not exists motion_inbox (
  project_id text not null,
  consumer_id text not null,
  event_id uuid not null,
  processed_at timestamptz not null default now(),
  effect_hash text,
  primary key(project_id, consumer_id, event_id)
);

create table if not exists motion_outbox (
  outbox_id bigint generated always as identity primary key,
  project_id text not null,
  event_id uuid not null,
  topic text not null,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  delivered_at timestamptz,
  attempts integer not null default 0,
  last_error text,
  unique(project_id, event_id, topic)
);

create table if not exists motion_state_snapshots (
  project_id text not null,
  snapshot_id uuid not null default gen_random_uuid(),
  event_watermark bigint not null,
  state_hash text not null check (state_hash ~ '^[0-9a-f]{64}$'),
  schema_versions jsonb not null,
  snapshot jsonb not null,
  created_at timestamptz not null default now(),
  primary key(project_id, snapshot_id),
  unique(project_id, event_watermark)
);

create table if not exists motion_graph_projection_checkpoints (
  project_id text not null,
  projection_name text not null,
  projection_version text not null,
  event_watermark bigint not null,
  projection_hash text not null check (projection_hash ~ '^[0-9a-f]{64}$'),
  projected_at timestamptz not null default now(),
  primary key(project_id, projection_name)
);

-- Reference lease acquisition transaction:
-- 1. BEGIN;
-- 2. SELECT existing lease FOR UPDATE by (project_id, resource_key).
-- 3. If ACTIVE and expires_at > now(): reject.
-- 4. generation := COALESCE(old.generation, 0) + 1.
-- 5. UPSERT ACTIVE lease with new generation/owner/session/expiry.
-- 6. append WORK_CLAIMED event + outbox row in the SAME transaction.
-- 7. COMMIT.
-- Protected writes must compare lease generation and expected aggregate revision.
-- A stale generation fails closed even if the former worker later reports success.

-- Reference event append transaction:
-- lock aggregate head; verify expected_revision; allocate next revision;
-- insert immutable event; update aggregate head; insert outbox; commit.
-- Any idempotency-key replay returns the previously committed logical result.

-- RLS/policy is intentionally not hard-coded here until the designated project,
-- auth model and service roles are selected. Production promotion requires RLS,
-- least-privilege service identities and security-advisor review.
