-- MOTION.OS Phase07 coordination functions
-- Apply after phase07_coordination_kernel.sql.

create table if not exists resource_fencing_generations (
  project_id text not null,
  resource_uri text not null,
  generation bigint not null default 0,
  updated_at timestamptz not null default now(),
  primary key(project_id, resource_uri)
);

alter table resource_fencing_generations enable row level security;

-- Exact-resource atomic lease acquisition. Hierarchical/tree scope overlap MUST be
-- resolved to canonical lock keys before calling this function. This prevents a
-- misleading assumption that SQL string-prefix overlap is a transactional lock.
create or replace function acquire_resource_lease(
  p_project_id text,
  p_resource_uri text,
  p_scope text,
  p_agent_id text,
  p_session_id text,
  p_ttl_seconds int,
  p_expected_revision text default null
)
returns resource_leases
language plpgsql
security invoker
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_token bigint;
  v_lease resource_leases;
begin
  if p_scope not in ('READ','WRITE','EXCLUSIVE_WRITE') then
    raise exception 'invalid lease scope: %', p_scope using errcode='22023';
  end if;
  if p_ttl_seconds <= 0 then
    raise exception 'ttl must be > 0' using errcode='22023';
  end if;

  -- Serialize acquisition per canonical resource key.
  perform pg_advisory_xact_lock(hashtextextended(p_project_id || E'\n' || p_resource_uri, 0));

  update resource_leases
     set status='EXPIRED', released_at=v_now
   where project_id=p_project_id
     and resource_uri=p_resource_uri
     and status='ACTIVE'
     and expires_at <= v_now;

  if p_scope = 'EXCLUSIVE_WRITE' then
    if exists (
      select 1 from resource_leases
       where project_id=p_project_id and resource_uri=p_resource_uri and status='ACTIVE'
    ) then
      raise exception 'resource already leased: %', p_resource_uri using errcode='55P03';
    end if;
  elsif p_scope = 'WRITE' then
    if exists (
      select 1 from resource_leases
       where project_id=p_project_id and resource_uri=p_resource_uri and status='ACTIVE'
         and scope in ('WRITE','EXCLUSIVE_WRITE')
    ) then
      raise exception 'resource already has active writer: %', p_resource_uri using errcode='55P03';
    end if;
  else
    if exists (
      select 1 from resource_leases
       where project_id=p_project_id and resource_uri=p_resource_uri and status='ACTIVE'
         and scope='EXCLUSIVE_WRITE'
    ) then
      raise exception 'resource exclusively leased: %', p_resource_uri using errcode='55P03';
    end if;
  end if;

  insert into resource_fencing_generations(project_id, resource_uri, generation, updated_at)
  values(p_project_id, p_resource_uri, 1, v_now)
  on conflict(project_id, resource_uri)
  do update set generation = resource_fencing_generations.generation + 1, updated_at=v_now
  returning generation into v_token;

  insert into resource_leases(
    project_id, resource_uri, scope, agent_id, session_id, fencing_token,
    expected_revision, acquired_at, expires_at, heartbeat_at, status
  ) values (
    p_project_id, p_resource_uri, p_scope, p_agent_id, p_session_id, v_token,
    p_expected_revision, v_now, v_now + make_interval(secs => p_ttl_seconds), v_now, 'ACTIVE'
  ) returning * into v_lease;

  return v_lease;
end;
$$;

create or replace function heartbeat_resource_lease(
  p_lease_id uuid,
  p_fencing_token bigint,
  p_ttl_seconds int
)
returns resource_leases
language plpgsql
security invoker
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_lease resource_leases;
begin
  if p_ttl_seconds <= 0 then
    raise exception 'ttl must be > 0' using errcode='22023';
  end if;

  update resource_leases
     set heartbeat_at=v_now,
         expires_at=v_now + make_interval(secs => p_ttl_seconds)
   where lease_id=p_lease_id
     and fencing_token=p_fencing_token
     and status='ACTIVE'
     and expires_at > v_now
  returning * into v_lease;

  if v_lease.lease_id is null then
    raise exception 'stale or expired lease' using errcode='40001';
  end if;
  return v_lease;
end;
$$;

create or replace function release_resource_lease(
  p_lease_id uuid,
  p_fencing_token bigint
)
returns resource_leases
language plpgsql
security invoker
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_lease resource_leases;
begin
  update resource_leases
     set status='RELEASED', released_at=v_now, expires_at=v_now, heartbeat_at=v_now
   where lease_id=p_lease_id
     and fencing_token=p_fencing_token
     and status='ACTIVE'
  returning * into v_lease;

  if v_lease.lease_id is null then
    raise exception 'stale or inactive lease' using errcode='40001';
  end if;
  return v_lease;
end;
$$;

create or replace function assert_active_write_lease(
  p_project_id text,
  p_resource_uri text,
  p_lease_id uuid,
  p_fencing_token bigint
)
returns boolean
language plpgsql
security invoker
as $$
declare
  v_now timestamptz := clock_timestamp();
begin
  if not exists (
    select 1 from resource_leases
     where lease_id=p_lease_id
       and project_id=p_project_id
       and resource_uri=p_resource_uri
       and fencing_token=p_fencing_token
       and status='ACTIVE'
       and scope in ('WRITE','EXCLUSIVE_WRITE')
       and expires_at > v_now
  ) then
    raise exception 'write rejected: stale/missing fencing authority' using errcode='40001';
  end if;
  return true;
end;
$$;

-- Append an immutable event and its outbox record in one transaction boundary.
-- Idempotency is keyed by (project_id, provenance_hash).
create or replace function append_coordination_event(
  p_event_id uuid,
  p_schema_version int,
  p_event_type text,
  p_aggregate_type text,
  p_aggregate_id text,
  p_project_id text,
  p_run_id text,
  p_session_id text,
  p_agent_id text,
  p_causation_id uuid,
  p_correlation_id text,
  p_expected_revision text,
  p_occurred_at timestamptz,
  p_payload jsonb,
  p_evidence_refs jsonb,
  p_git_meta jsonb,
  p_provenance_hash text,
  p_sensitivity text,
  p_topic text default 'motion.coordination'
)
returns table(event_id uuid, duplicate boolean)
language plpgsql
security invoker
as $$
declare
  v_event_id uuid;
  v_inserted boolean := false;
begin
  insert into coordination_events(
    event_id, schema_version, event_type, aggregate_type, aggregate_id, project_id,
    run_id, session_id, agent_id, causation_id, correlation_id, expected_revision,
    occurred_at, payload, evidence_refs, git_meta, provenance_hash, sensitivity
  ) values (
    p_event_id, p_schema_version, p_event_type, p_aggregate_type, p_aggregate_id, p_project_id,
    p_run_id, p_session_id, p_agent_id, p_causation_id, p_correlation_id, p_expected_revision,
    p_occurred_at, coalesce(p_payload,'{}'::jsonb), coalesce(p_evidence_refs,'[]'::jsonb),
    p_git_meta, p_provenance_hash, p_sensitivity
  )
  on conflict(project_id, provenance_hash) do nothing
  returning coordination_events.event_id into v_event_id;

  if v_event_id is not null then
    v_inserted := true;
  else
    select ce.event_id into v_event_id
      from coordination_events ce
     where ce.project_id=p_project_id and ce.provenance_hash=p_provenance_hash;
  end if;

  insert into coordination_outbox(event_id, topic)
  values(v_event_id, p_topic)
  on conflict(event_id, topic) do nothing;

  return query select v_event_id, not v_inserted;
end;
$$;

-- Consumer acknowledgement is monotonic and cannot rewind.
create or replace function acknowledge_coordination_consumer(
  p_consumer_id text,
  p_project_id text,
  p_recorded_at timestamptz,
  p_event_id uuid
)
returns coordination_consumers
language plpgsql
security invoker
as $$
declare
  v_current coordination_consumers;
  v_result coordination_consumers;
begin
  select * into v_current from coordination_consumers
   where consumer_id=p_consumer_id
   for update;

  if v_current.consumer_id is not null and v_current.project_id <> p_project_id then
    raise exception 'consumer project mismatch' using errcode='22023';
  end if;

  if v_current.consumer_id is not null and v_current.last_event_recorded_at is not null then
    if (p_recorded_at, p_event_id) < (v_current.last_event_recorded_at, v_current.last_event_id) then
      raise exception 'consumer offset rewind forbidden' using errcode='40001';
    end if;
  end if;

  insert into coordination_consumers(consumer_id, project_id, last_event_recorded_at, last_event_id, updated_at)
  values(p_consumer_id, p_project_id, p_recorded_at, p_event_id, now())
  on conflict(consumer_id) do update
    set last_event_recorded_at=excluded.last_event_recorded_at,
        last_event_id=excluded.last_event_id,
        updated_at=now()
  returning * into v_result;

  return v_result;
end;
$$;
