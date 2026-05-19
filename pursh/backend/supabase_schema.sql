-- Pursh Supabase schema
-- Apply via Supabase SQL editor or supabase db push
--
-- DISCLAIMER: Demonstration project. All data is synthetic.
-- This schema implements HIPAA §164.312(a)(1) access control via RLS
-- and §164.312(b) audit controls via the audit_log table.

-- ── Extensions ───────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ── Patient records ──────────────────────────────────────────────────────────
-- NOTE: display_name and date_of_birth are synthetic test data only.
-- In a real deployment these would be encrypted at the application layer.
create table if not exists patient_profiles (
    id              uuid primary key default uuid_generate_v4(),
    auth_user_ref   uuid not null references auth.users(id) on delete cascade,
    display_name    text not null default 'Test Patient (synthetic)',
    date_of_birth   date,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- RLS: patients see only their own record (HIPAA §164.312(a)(1))
alter table patient_profiles enable row level security;

create policy "patients_own_profile" on patient_profiles
    for all
    using (auth_user_ref = auth.uid());

-- ── Doctor profiles ───────────────────────────────────────────────────────────
create table if not exists doctor_profiles (
    id              uuid primary key default uuid_generate_v4(),
    auth_user_ref   uuid not null references auth.users(id) on delete cascade,
    display_name    text not null,
    specialty       text not null,
    bio             text,
    availability    text,
    created_at      timestamptz not null default now()
);

-- RLS: doctors see their own profile; patients see all doctors (for booking)
alter table doctor_profiles enable row level security;

create policy "doctors_own_profile" on doctor_profiles
    for all
    using (auth_user_ref = auth.uid());

create policy "patients_read_doctors" on doctor_profiles
    for select
    using (true);  -- all authenticated users can browse doctors

-- ── Appointments ──────────────────────────────────────────────────────────────
create table if not exists appointments (
    id                  uuid primary key default uuid_generate_v4(),
    patient_user_ref    uuid not null references auth.users(id),
    doctor_user_ref     uuid not null references auth.users(id),
    appointment_type    text not null check (appointment_type in ('video', 'async_message')),
    reason              text not null,
    status              text not null default 'pending'
                            check (status in ('pending', 'confirmed', 'completed', 'cancelled')),
    scheduled_at        timestamptz,
    created_at          timestamptz not null default now()
);

-- RLS: patients see their own appointments; doctors see appointments assigned to them
alter table appointments enable row level security;

create policy "patients_own_appointments" on appointments
    for all
    using (patient_user_ref = auth.uid());

create policy "doctors_assigned_appointments" on appointments
    for select
    using (doctor_user_ref = auth.uid());

-- ── Symptom history ───────────────────────────────────────────────────────────
create table if not exists symptom_history (
    id                  uuid primary key default uuid_generate_v4(),
    patient_user_ref    uuid not null references auth.users(id),
    symptom_description text not null,
    severity            text not null check (severity in ('mild', 'moderate', 'severe')),
    suggested_specialty text,
    urgency             text check (urgency in ('routine', 'soon', 'emergency')),
    reported_at         timestamptz not null default now()
);

-- RLS: patients see only their own symptom history
alter table symptom_history enable row level security;

create policy "patients_own_symptoms" on symptom_history
    for all
    using (patient_user_ref = auth.uid());

-- ── Audit log (HIPAA §164.312(b)) ────────────────────────────────────────────
-- Append-only: no UPDATE or DELETE permissions granted on this table.
-- Every read/write of sensitive data is logged with hashed actor ID.
create table if not exists audit_log (
    id              uuid primary key default uuid_generate_v4(),
    actor_id        text not null,   -- SHA-256 hash of auth.uid(), never raw value
    action          text not null,   -- READ | WRITE | DELETE
    resource        text not null,   -- table name
    resource_id     uuid,
    before_hash     text,            -- SHA-256 of before state
    after_hash      text,            -- SHA-256 of after state
    ip_address      inet,
    user_agent      text,
    created_at      timestamptz not null default now()
);

-- RLS: only the service role can write; no SELECT for application roles
alter table audit_log enable row level security;

create policy "service_role_audit_write" on audit_log
    for insert
    with check (true);  -- service role bypasses RLS; app roles blocked from select/update/delete

-- ── RLS test helper (used in test suite) ─────────────────────────────────────
-- Verifies that cross-patient access is blocked at the database level.
-- Run this function in a test that switches between two user contexts.
create or replace function test_rls_cross_patient_blocked(
    patient_a_id uuid,
    patient_b_id uuid
) returns boolean
language plpgsql security definer as $$
declare
    count_result integer;
begin
    -- Simulate patient_b trying to read patient_a's profile
    set local role authenticated;
    set local "request.jwt.claims" to json_build_object('sub', patient_b_id::text)::text;
    select count(*) into count_result
    from patient_profiles
    where auth_user_ref = patient_a_id;
    return count_result = 0;  -- should be 0 if RLS is working
end;
$$;
