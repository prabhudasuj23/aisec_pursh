# HIPAA Security Rule Mapping — Pursh

> **Disclaimer:** Pursh is a demonstration project containing **synthetic data
> only**. This document maps Pursh's technical controls to HIPAA Security Rule
> sections. It does **not** constitute a HIPAA compliance certification.
> AISec claims HIPAA-aligned design, not HIPAA compliance.
>
> See `path-to-real-hipaa.md` for the steps required to pursue actual compliance.

---

## Administrative Safeguards (§164.308)

| HIPAA section | Requirement | Pursh implementation | Status |
|---|---|---|---|
| §164.308(a)(1)(ii)(D) | Information system activity review | Weekly auto-generated review in CISO dashboard view | Phase 14 |
| §164.308(a)(2) | Assigned security responsibility | Owner designated as Security Officer | Phase 0 (documented) |
| §164.308(a)(5)(ii)(C) | Log-in monitoring | Failed login attempts logged with actor IP, timestamp | Phase 1 |
| §164.408 | Breach notification simulation | `pursh-phi-exposure.md` runbook simulates 60-day timeline | Phase 11 |

## Technical Safeguards (§164.312)

| HIPAA section | Requirement | Pursh implementation | Status |
|---|---|---|---|
| §164.312(a)(1) | Access control | Supabase RLS policies on `patient_records`; FastAPI RBAC middleware (`patient` and `doctor` roles) | Phase 2 |
| §164.312(a)(2)(i) | Unique user identification | Supabase Auth UUIDs; no shared accounts permitted | Phase 1 |
| §164.312(a)(2)(iii) | Automatic logoff | Session timeout 15 min; refresh-token rotation | Phase 7 |
| §164.312(a)(2)(iv) | Encryption and decryption | AES-256 at rest (Supabase Postgres + S3 with KMS CMK) | Phase 5/6 |
| §164.312(b) | Audit controls | `audit_log` table: every read/write of patient data logged with actor, timestamp, before/after value | Phase 1 |
| §164.312(c)(1) | Integrity | Checksum on uploaded files; cryptographic signatures on critical records | Phase 6 |
| §164.312(d) | Person/entity authentication | MFA required for all roles; OIDC tokens with short TTL | Phase 7 |
| §164.312(e)(1) | Transmission security | TLS 1.3 enforced, HSTS, no fallback to weaker ciphers | Phase 5 |

## Compliance mapping status legend

| Symbol | Meaning |
|---|---|
| ✅ | Implemented and tested |
| 🔄 | In progress |
| 📋 | Planned (phase noted) |
| ⚠️ | Accepted gap (documented risk) |

---

## Audit log schema (§164.312(b))

```sql
CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id    UUID NOT NULL,          -- hashed, never raw patient_id_value
    action      TEXT NOT NULL,          -- READ | WRITE | DELETE
    resource    TEXT NOT NULL,          -- e.g., "patient_records"
    resource_id UUID,                   -- the record affected
    before_hash TEXT,                   -- SHA-256 of before state (writes/deletes)
    after_hash  TEXT,                   -- SHA-256 of after state (writes)
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Log entries are **append-only** (no UPDATE/DELETE permissions on `audit_log`
for any application role).
