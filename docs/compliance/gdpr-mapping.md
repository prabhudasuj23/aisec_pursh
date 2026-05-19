# GDPR Article 32 Mapping — Pursh

> **Disclaimer:** Pursh is a demonstration project containing **synthetic data
> only**. This document maps Pursh's technical controls to GDPR Article 32
> sub-clauses. It does **not** constitute a GDPR compliance certification.
> AISec demonstrates which controls *map to* which regulatory requirements.

---

## Article 32 — Security of processing

| Art. 32 sub-clause | Requirement | Pursh implementation | Status |
|---|---|---|---|
| 32(1)(a) | Pseudonymisation and encryption | Patient IDs separated from PII in separate tables; AES-256 encryption at rest via Supabase (at-rest encryption) + S3 with KMS CMK | Phase 1/6 |
| 32(1)(b) | Confidentiality, integrity, availability, and resilience | TLS 1.3 in transit; audit logs for integrity; RDS Multi-AZ for availability; S3 versioning for resilience | Phase 5 |
| 32(1)(c) | Ability to restore availability and access in timely manner | RDS Point-in-Time Recovery (PITR); S3 versioning + lifecycle; documented RTO/RPO in `/docs/runbooks/recovery.md` | Phase 11 |
| 32(1)(d) | Regular testing, assessing, and evaluating | Monthly tabletop exercises; scheduled DAST scans; full AISec scanner suite on every PR | Phase 7+ |
| 32(2) | Risk-appropriate measures | Threat model documents the risk assessment for each Pursh service; PASTA used for high-risk services | Phase 11 |

## Data subject rights mapping (informational)

Pursh implements no real data subject rights (right to access, erasure, portability)
because it contains only synthetic data. These are documented below as
design targets for any future real-data deployment.

| Right | GDPR article | Technical mechanism needed |
|---|---|---|
| Right of access | Art. 15 | API endpoint returning all data by `actor_id` |
| Right to erasure | Art. 17 | Cascade delete + audit log of erasure event |
| Data portability | Art. 20 | JSON/CSV export endpoint |
| Right to rectification | Art. 16 | Audit-logged UPDATE with before/after record |

---

## Pseudonymisation approach (32(1)(a))

```
real_identity_table (supabase auth.users):
  id (UUID)      ← Supabase Auth primary key
  email          ← stored in Supabase Auth, NOT in patient_records

patient_records (application table):
  id (UUID)      ← separate UUID, NOT linked to auth.users.id in app code
  auth_user_ref  ← FK to auth.users.id, only accessible via RLS
  synthetic_name ← "Test Patient A" — never a real name
  ...
```

The separation between `auth_user_ref` and the record UUID is the pseudonymisation
layer. Application code uses the record UUID; the auth link is resolved only
at the Supabase RLS layer, never returned to the frontend.
