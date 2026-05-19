# Path to Real HIPAA Eligibility

> This document is **informational only**. Pursh v1 does not pursue HIPAA
> compliance — it contains synthetic data and demonstrates HIPAA-aligned
> controls only. This document records the steps required if the project
> were ever taken commercial with real PHI.

---

## Steps required (in order)

### 1. Sign Business Associate Agreements (BAAs)

| Vendor | BAA availability | Notes |
|---|---|---|
| Supabase | ✅ Available on paid Team plan | Standard Supabase BAA covers managed Postgres + Auth |
| AWS | ✅ Available by default for HIPAA-eligible services | Sign via AWS console → "My Account → Agreements" |
| Vercel | ⚠️ Enterprise plan only | Or migrate frontend to AWS (ECS/CloudFront) to stay all-AWS |
| OpenAI / DeepSeek | ❌ Not available as of 2025 | Cannot send real PHI to external LLM APIs without BAA |

**Implication for LLM use:** If real PHI enters Pursh, AI features (AI-2 visit
summarization, AI-3 symptom checker) must use AWS Bedrock (BAA available) or
a self-hosted model. DeepSeek is incompatible with real PHI.

### 2. Enable encryption with customer-managed KMS keys

- RDS: enable at-rest encryption with CMK (not AWS-managed key)
- S3 buckets: SSE-KMS with CMK
- OpenSearch: at-rest encryption with CMK
- Supabase: confirm CMK support with vendor under BAA

### 3. Implement formal Security Risk Assessment (§164.308(a)(1)(ii)(A))

- Documented threat model covering all ePHI flows
- Risk rating for each identified threat
- Mitigation plan with owner and target date
- Annual review cadence

### 4. Designate Privacy Officer and Security Officer (§164.308(a)(2))

Formal role assignments in writing, even for a solo project.

### 5. Implement workforce training program (§164.308(a)(5))

- Security awareness training for all staff with PHI access
- Records of training completion
- Annual refresh

### 6. Document policies and procedures (§164.316)

- Access control policy
- Audit log review procedure
- Incident response policy (already drafted as runbooks — formalize)
- Sanction policy for workforce violations
- Data retention and disposal policy

### 7. Engage third-party HIPAA assessor

A qualified assessor reviews the above and issues a formal assessment.
This is not a certification (HIPAA has no official certification body), but
an independent assessment is standard practice for enterprise clients.

---

## What v1 already does correctly (and why it matters)

Even though Pursh v1 does not pursue HIPAA compliance, the following controls
are implemented correctly and would transfer to a real-PHI deployment with
minimal rework:

- Supabase RLS policies (§164.312(a)(1)) — already enforced
- Unique user IDs, no shared accounts (§164.312(a)(2)(i)) — already enforced
- Audit log table with append-only policy (§164.312(b)) — already designed
- TLS 1.3 in transit (§164.312(e)(1)) — already enforced
- S3 + KMS file encryption (§164.312(a)(2)(iv)) — already configured
- Breach notification runbook (§164.408 simulation) — Phase 11

The gap between v1 and a real HIPAA deployment is primarily: BAAs, CMKs,
formal policies, and a real risk assessment — not code rewrites.
