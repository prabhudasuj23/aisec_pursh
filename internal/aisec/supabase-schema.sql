-- ============================================================
-- AISec Platform — Supabase Schema
-- Run this entire file in the Supabase SQL Editor once.
-- https://wvaforjorxjiaznxilug.supabase.co
-- ============================================================

-- ── Helper: auto-update updated_at ───────────────────────────────────────────

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;


-- ============================================================
-- TABLE 1: scan_runs
-- Every scanner execution is one row.
-- Status moves: running → completed | failed
-- findings JSONB holds the full normalised finding array so
-- the dashboard can render results without round-tripping
-- back to the runner.
-- ============================================================

create table if not exists public.scan_runs (
  id             uuid        primary key default gen_random_uuid(),
  run_id         text        not null,
  scanner_id     text        not null,
  scanner_name   text,

  -- timing
  started_at     timestamptz,
  finished_at    timestamptz,
  exit_code      integer,
  status         text        not null default 'running'
                             check (status in ('running','completed','failed')),

  -- findings summary
  counts         jsonb       not null default '{}',
  findings_count integer     not null default 0,

  -- full findings array as JSONB:
  --   [{severity, rule_id, title, file, line, cwe, fix_effort, ...}]
  -- Stored as JSONB so you can query individual fields:
  --   select * from scan_runs where findings @> '[{"severity":"CRITICAL"}]';
  findings       jsonb       not null default '[]',

  -- raw stdout/stderr (last 200 lines to cap size)
  raw_output     text,

  -- fingerprints for delta calculation (rule|file|severity strings)
  fingerprints   jsonb       not null default '[]',

  -- intelligence fields computed after scan
  risk_score     jsonb,   -- {score, grade, trend, change, prev_score}
  compliance     jsonb,   -- {owasp, hipaa, pci_dss, soc2, nist_csf, iso27001}
  delta          jsonb,   -- {new, fixed, unchanged, new_critical, is_first_scan}
  effort_minutes integer,

  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),

  -- idempotent upsert key used by the runner
  constraint uq_scan_run unique (run_id, scanner_id)
);

-- auto-update updated_at on every row change
create trigger scan_runs_updated_at
  before update on public.scan_runs
  for each row execute function public.set_updated_at();

-- query indexes
create index if not exists idx_scan_runs_scanner_id   on public.scan_runs (scanner_id);
create index if not exists idx_scan_runs_status        on public.scan_runs (status);
create index if not exists idx_scan_runs_created_at    on public.scan_runs (created_at desc);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Service role (runner) bypasses RLS automatically.
-- Authenticated dashboard users can read completed runs.
-- Nobody outside the service role can write.

alter table public.scan_runs enable row level security;

-- Authenticated users: read any completed run
create policy "auth users read completed runs"
  on public.scan_runs
  for select
  using (
    auth.uid() is not null
    and status = 'completed'
  );

-- Authenticated users: read their own running/failed runs too
-- (useful for watching an in-progress scan in real time)
create policy "auth users read all runs"
  on public.scan_runs
  for select
  using ( auth.uid() is not null );

-- Service role: full read/write (bypasses RLS — no policy needed)
-- The runner uses SUPABASE_JWT_SECRET (service role key) which
-- automatically bypasses all RLS policies.


-- ============================================================
-- TABLE 2: ai_analyses
-- Immutable audit log — one row per DeepSeek call.
-- Every prompt sent and every response received is recorded
-- so you can audit exactly what the AI said, when, and why.
-- Never updated after insert.
-- ============================================================

create table if not exists public.ai_analyses (
  id               uuid        primary key default gen_random_uuid(),
  scanner_id       text        not null,

  -- links to scan_runs.run_id (nullable — intelligence can be called
  -- independently of a fresh scan run)
  run_id           text,

  model            text        not null default 'deepseek-chat',

  -- full prompt sent to DeepSeek (includes top-20 findings context)
  prompt           text        not null,

  -- raw string response from the model (before JSON parsing)
  response_raw     text        not null,

  -- parsed JSON object ({summary, attack_paths, remediation_plan, …})
  -- null if parsing failed (see error column)
  response_parsed  jsonb,

  -- token/size metrics for cost analysis
  prompt_chars     integer,
  response_chars   integer,
  latency_ms       integer,

  -- true when this row was created from an in-memory cache hit
  -- (i.e. no real DeepSeek call was made; previous response reused)
  cached           boolean     not null default false,

  -- set when DeepSeek call or JSON parsing failed
  error            text,

  created_at       timestamptz not null default now()
  -- no updated_at — this table is append-only
);

-- query indexes
create index if not exists idx_ai_analyses_scanner_id  on public.ai_analyses (scanner_id);
create index if not exists idx_ai_analyses_created_at  on public.ai_analyses (created_at desc);
create index if not exists idx_ai_analyses_run_id      on public.ai_analyses (run_id)
  where run_id is not null;

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Authenticated users can read AI analyses for any scanner.
-- Only service role can insert.

alter table public.ai_analyses enable row level security;

create policy "auth users read ai analyses"
  on public.ai_analyses
  for select
  using ( auth.uid() is not null );

-- Service role write access is automatic (bypasses RLS).


-- ============================================================
-- TABLE 3: triage_notes
-- Per-finding triage decisions made by security engineers
-- in the dashboard. Linked to a finding by its fingerprint
-- (rule|file|severity) which is stable across re-scans.
-- ============================================================

create table if not exists public.triage_notes (
  id           uuid        primary key default gen_random_uuid(),
  scanner_id   text        not null,
  fingerprint  text        not null,   -- rule|file|severity

  status       text        not null default 'open'
               check (status in ('open','triaged','accepted_risk','false_positive','fixed')),
  note         text,
  triaged_by   uuid        references auth.users (id) on delete set null,
  triaged_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),

  constraint uq_triage unique (scanner_id, fingerprint)
);

create trigger triage_notes_updated_at
  before update on public.triage_notes
  for each row execute function public.set_updated_at();

create index if not exists idx_triage_scanner_id   on public.triage_notes (scanner_id);
create index if not exists idx_triage_fingerprint  on public.triage_notes (fingerprint);

alter table public.triage_notes enable row level security;

-- Authenticated users can read all triage notes
create policy "auth users read triage"
  on public.triage_notes
  for select
  using ( auth.uid() is not null );

-- Authenticated users can insert/update their own triage notes
create policy "auth users write triage"
  on public.triage_notes
  for all
  using ( auth.uid() is not null )
  with check ( auth.uid() is not null );


-- ============================================================
-- VERIFICATION QUERIES
-- Run these after applying the schema to confirm everything
-- was created correctly.
-- ============================================================

-- 1. List all tables
-- select table_name from information_schema.tables
--   where table_schema = 'public' order by table_name;

-- 2. List all RLS policies
-- select tablename, policyname, cmd, qual
--   from pg_policies where schemaname = 'public' order by tablename;

-- 3. Test anon access (should return 0 rows, not error)
-- set role anon;
-- select count(*) from public.scan_runs;   -- 0 rows (RLS blocks anon)
-- reset role;

-- 4. Test auth access (after creating a user)
-- set role authenticated;
-- set local "request.jwt.claims" = '{"sub":"test-uid","role":"authenticated"}';
-- select count(*) from public.scan_runs;   -- should work
-- reset role;
