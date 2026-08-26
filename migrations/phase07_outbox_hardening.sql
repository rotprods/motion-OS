-- MOTION.OS Phase07 multi-dispatcher outbox hardening
-- Apply after phase07_coordination_kernel.sql.

alter table coordination_outbox
  add column if not exists lock_owner text,
  add column if not exists locked_until timestamptz;

create index if not exists coordination_outbox_pending_idx
on coordination_outbox(created_at, outbox_id)
where published_at is null;

create or replace function claim_coordination_outbox(
  p_worker_id text,
  p_limit int default 100,
  p_lease_seconds int default 30
)
returns setof coordination_outbox
language plpgsql
security invoker
as $$
declare
  v_now timestamptz := clock_timestamp();
begin
  if p_worker_id is null or length(p_worker_id)=0 then
    raise exception 'worker id required' using errcode='22023';
  end if;
  if p_limit <= 0 or p_limit > 1000 then
    raise exception 'limit out of bounds' using errcode='22023';
  end if;
  if p_lease_seconds <= 0 or p_lease_seconds > 300 then
    raise exception 'lease seconds out of bounds' using errcode='22023';
  end if;

  return query
  with candidates as (
    select o.outbox_id
      from coordination_outbox o
     where o.published_at is null
       and (o.locked_until is null or o.locked_until <= v_now)
     order by o.created_at, o.outbox_id
     for update skip locked
     limit p_limit
  )
  update coordination_outbox o
     set lock_owner=p_worker_id,
         locked_until=v_now + make_interval(secs => p_lease_seconds),
         attempts=o.attempts + 1
    from candidates c
   where o.outbox_id=c.outbox_id
  returning o.*;
end;
$$;

create or replace function mark_coordination_outbox_published(
  p_worker_id text,
  p_outbox_id bigint
)
returns coordination_outbox
language plpgsql
security invoker
as $$
declare
  v_row coordination_outbox;
begin
  update coordination_outbox
     set published_at=clock_timestamp(),
         lock_owner=null,
         locked_until=null,
         last_error=null
   where outbox_id=p_outbox_id
     and published_at is null
     and lock_owner=p_worker_id
     and locked_until > clock_timestamp()
  returning * into v_row;

  if v_row.outbox_id is null then
    raise exception 'outbox publish acknowledgement rejected: stale/missing dispatch lease' using errcode='40001';
  end if;
  return v_row;
end;
$$;

create or replace function mark_coordination_outbox_failed(
  p_worker_id text,
  p_outbox_id bigint,
  p_error text
)
returns coordination_outbox
language plpgsql
security invoker
as $$
declare
  v_row coordination_outbox;
begin
  update coordination_outbox
     set last_error=left(coalesce(p_error,'unknown'), 4000),
         lock_owner=null,
         locked_until=null
   where outbox_id=p_outbox_id
     and published_at is null
     and lock_owner=p_worker_id
  returning * into v_row;

  if v_row.outbox_id is null then
    raise exception 'outbox failure acknowledgement rejected' using errcode='40001';
  end if;
  return v_row;
end;
$$;
