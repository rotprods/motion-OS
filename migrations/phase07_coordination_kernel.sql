-- MOTION.OS Phase07 durable coordination kernel
-- Target: PostgreSQL / Supabase. Apply only after explicit environment selection.

create extension if not exists pgcrypto;

create table if not exists coordination_events (
  event_id uuid primary key default gen_random_uuid(),
  schema_version int not null check (schema_version > 0),
  event_type text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  project_id text not null,
  run_id text,
  session_id text not null,
  agent_id text not null,
  causation_id uuid,
  correlation_id text not null,
  expected_revision text,
  occurred_at timestamptz not null,
  recorded_at timestamptz not null default now(),
  payload jsonb not null default '{}'::jsonb,
  evidence_refs jsonb not null default '[]'::jsonb,
  git_meta jsonb,
  provenance_hash text not null check (provenance_hash ~ '^[0-9a-fA-F]{64}$'),
  sensitivity text not null default 'INTERNAL',
  unique (project_id, provenance_hash)
);

create index if not exists coordination_events_project_recorded_idx on coordination_events(project_id, recorded_at, event_id);
create index if not exists coordination_events_aggregate_idx on coordination_events(project_id, aggregate_type, aggregate_id, recorded_at);
create index if not exists coordination_events_correlation_idx on coordination_events(project_id, correlation_id, recorded_at);

create table if not exists coordination_outbox (
  outbox_id bigserial primary key,
  event_id uuid not null references coordination_events(event_id) on delete restrict,
  topic text not null,
  created_at timestamptz not null default now(),
  published_at timestamptz,
  attempts int not null default 0,
  last_error text,
  unique(event_id, topic)
);

create table if not exists coordination_consumers (
  consumer_id text primary key,
  project_id text not null,
  last_event_recorded_at timestamptz,
  last_event_id uuid,
  updated_at timestamptz not null default now()
);

create table if not exists agent_sessions (
  session_id text primary key,
  agent_id text not null,
  project_id text not null,
  runtime text not null,
  branch text,
  pr_number int,
  context_pack_hash text,
  authority_level text not null default 'SHADOW',
  status text not null default 'ACTIVE',
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  revision bigint not null default 1
);

create table if not exists resource_leases (
  lease_id uuid primary key default gen_random_uuid(),
  project_id text not null,
  resource_uri text not null,
  scope text not null check (scope in ('READ','WRITE','EXCLUSIVE_WRITE')),
  agent_id text not null,
  session_id text not null references agent_sessions(session_id),
  fencing_token bigint not null,
  expected_revision text,
  acquired_at timestamptz not null default now(),
  expires_at timestamptz not null,
  heartbeat_at timestamptz not null default now(),
  released_at timestamptz,
  status text not null check (status in ('ACTIVE','RELEASED','EXPIRED','REVOKED')),
  unique(project_id, resource_uri, fencing_token)
);

create unique index if not exists resource_leases_one_active_writer_idx
on resource_leases(project_id, resource_uri)
where status='ACTIVE' and scope in ('WRITE','EXCLUSIVE_WRITE');

create table if not exists work_items (
  work_id text primary key,
  project_id text not null,
  title text not null,
  status text not null,
  priority text not null,
  owner_agent_id text,
  branch text,
  pr_number int,
  revision bigint not null default 1,
  metadata jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists work_dependencies (
  work_id text not null references work_items(work_id),
  depends_on_work_id text not null references work_items(work_id),
  relation text not null default 'DEPENDS_ON',
  primary key(work_id, depends_on_work_id, relation)
);

create table if not exists decisions (
  decision_id text primary key,
  project_id text not null,
  status text not null,
  title text not null,
  body text not null,
  governs_uri text,
  proposed_by text not null,
  accepted_by text,
  revision bigint not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists conflicts (
  conflict_id uuid primary key default gen_random_uuid(),
  project_id text not null,
  resource_uri text not null,
  kind text not null,
  status text not null default 'OPEN',
  agents jsonb not null,
  details jsonb not null,
  detected_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table if not exists checkpoints (
  checkpoint_id text primary key,
  project_id text not null,
  agent_id text not null,
  session_id text not null,
  branch text,
  git_sha text,
  pr_number int,
  state text not null,
  summary text not null,
  evidence_refs jsonb not null default '[]'::jsonb,
  next_actions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists context_packs (
  context_pack_id text primary key,
  project_id text not null,
  agent_id text not null,
  session_id text not null,
  generated_at timestamptz not null,
  stale_after timestamptz not null,
  main_sha text not null,
  projection_version bigint not null,
  projection_hash text not null,
  pack jsonb not null,
  seal_sha256 text not null,
  invalidated_at timestamptz
);

create table if not exists graph_projection_versions (
  project_id text not null,
  projection_version bigint not null,
  projection_hash text not null,
  source_event_count bigint not null,
  last_event_id uuid,
  built_at timestamptz not null default now(),
  status text not null,
  primary key(project_id, projection_version)
);

-- RLS must be enabled and policies defined before production authority.
alter table coordination_events enable row level security;
alter table coordination_outbox enable row level security;
alter table coordination_consumers enable row level security;
alter table agent_sessions enable row level security;
alter table resource_leases enable row level security;
alter table work_items enable row level security;
alter table work_dependencies enable row level security;
alter table decisions enable row level security;
alter table conflicts enable row level security;
alter table checkpoints enable row level security;
alter table context_packs enable row level security;
alter table graph_projection_versions enable row level security;

-- No permissive policies are included intentionally. Default-deny until runtime identities are designed.
