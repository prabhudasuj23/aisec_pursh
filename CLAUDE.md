# CLAUDE.md — AISec (aisec.aivistix.com)

> **The Aivistix enterprise security platform: SAST · DAST · SCA · SBOM · Container · CloudSec · AI Security · Threat Modeling · Incident Response.**
>
> Monorepo containing two products:
> 1. **AISec** — the security platform (control plane, scanners, dashboard)
> 2. **Pursh** — a synthetic telehealth app, used as the realistic target that AISec scans, threat-models, and demonstrates HIPAA-aligned controls against
>
> This file is the source of truth for every Claude Code session in this repository. Read it fully before planning, coding, or running tools. Update it whenever you learn something new.

---

## 1. Project Context

### 1.1 What AISec is
**AISec** is a new product under the Aivistix brand at `aisec.aivistix.com`. Separate from the existing Aivistix education site, NerFree, and DarkFiber, but sharing brand, design system, and authentication.

AISec is an **enterprise-grade security platform** that:
1. Wires SAST, DAST, SCA, SBOM, container, secrets, IaC, and CloudSec scanners into CI/CD.
2. Normalizes every finding into one model and shows them on a five-persona dashboard.
3. Maps every finding to OWASP Top 10 (2021), OWASP ASVS v4.0.3, OWASP Top 10 for LLM Applications, HIPAA Security Rule, and GDPR Article 32.
4. Manages threat models as code, in version control.
5. Provides incident response runbooks and tabletop exercises against deliberately broken environments.
6. Demonstrates everything above by **scanning Pursh** — a realistic telehealth app built in the same repository.

### 1.2 What Pursh is
**Pursh** is a synthetic-data telehealth app (think "Hims/Hers concept" but original branding and no real medical service). Its sole purpose is to be a **realistic, HIPAA-shaped target** for AISec to scan, threat-model, and demonstrate compliance mapping against.

Pursh is **not** a real medical product. Every page in Pursh shows two prominent disclaimers:
- **"Demonstration project — not a real medical service. Do not enter real symptoms, conditions, or PHI."**
- **"Synthetic test data only. This is a security-engineering portfolio project."**

Pursh handles only synthetic patient data (Synthea-generated or obviously-fake records like "Test Patient A"). The HIPAA controls implemented are real; the data they protect is not. CLAUDE.md §4.5 documents the path to real HIPAA eligibility if the project is ever taken commercial, but that is **not** the v1 scope.

### 1.3 Aivistix brand relationships
| Property | Audience | AISec relationship |
|---|---|---|
| `aivistix.com` | Cybersecurity beginners | Shared brand, footer link, shared OIDC backend |
| `nerfree.aivistix.com` | Beginners exploring free tools | No technical coupling |
| `darkfiber.aivistix.com` | Beginners in hands-on labs | No technical coupling |
| `aisec.aivistix.com` | **Security engineers, DevSecOps, CISOs, auditors, hiring managers** | **This project** |
| `pursh.aivistix.com` *(optional subdomain)* | **Demo target only — public read shows Pursh's UI with synthetic data** | Lives in same repo, deployed separately |

**Brand voice rule.** Aivistix: *"Learn cybersecurity from zero — no tech background needed."* AISec: *"Production-grade security operations for engineering teams."* Pursh: warm consumer-app tone with security disclaimers. Three voices, one parent brand. Do not blur them.

### 1.4 Authentication model
- **Public read-only AISec view:** anonymized demo findings, sample dashboards, OWASP/HIPAA/GDPR coverage explainers, sample threat model, sample postmortem. No login.
- **Authenticated AISec view:** technical users sign in via `aivistix.com/login` (OIDC federation). AISec does not run its own user database — Aivistix is the IdP, AISec is the relying party. RBAC for the five personas lives in AISec.
- **Pursh authentication:** Supabase Auth (separate from Aivistix IdP, since Pursh simulates a real consumer telehealth app). Two roles: `patient` and `doctor`. Email + password + MFA.

### 1.5 Who is building it
The owner is transitioning from **operations to security engineering**, builds shipped products (Aivistix is live), and wants this project to demonstrate the responsibilities in a real Application Security Engineer job description (§1.6).

**Implication for Claude sessions:** explain *why* before *how*. When a Semgrep rule fires, a ZAP alert appears, a CVE shows up in Trivy, or Prowler flags an IAM misconfiguration — take one extra paragraph to explain the underlying weakness class (CWE, CIS control, HIPAA section, etc.). Never just dump a fix without the underlying lesson.

### 1.6 JD-to-project mapping
This project exists to demonstrate the responsibilities of an Application Security Engineer role. Every JD line points to specific deliverables.

| JD responsibility | AISec/Pursh deliverable | Where in this doc |
|---|---|---|
| **Conduct SAST and DAST assessments to identify vulnerabilities** | Semgrep + ZAP scan Pursh on every PR; findings flow to dashboard with severity, location, remediation | §3.3, §8 Phase 2 + 7 |
| **Provide remediation guidance** | Each finding in the dashboard includes a remediation card pulled from a curated `/app/mappings/remediation/` library | §3.5, §6 |
| **Implement and manage security configurations within CI/CD** | GitHub Actions reusable composite actions per scanner; OIDC to AWS; SLSA-style provenance (future); branch protection enforcement | §2.6, §4.5 |
| **Ensure secure code deployment** | Pre-push image scanning, signed commits, merge gating on critical findings, deployment via OIDC role with least privilege | §7, §11 |
| **Review and enhance SCM security practices** | CODEOWNERS, signed commits, branch protection, Dependabot, PR security-checklist template, Gitleaks pre-commit+CI+history | §4.6 |
| **Protect source code and sensitive information** | Gitleaks + detect-secrets in pre-commit and CI; secret-rotation runbook; AWS Secrets Manager for runtime secrets | §4.6, §5.2 |
| **Collaborate with dev teams to integrate security into SDLC** | PR comments (reviewdog), Slack notifications, IDE rule packs published as a public Semgrep ruleset | §7 |
| **Perform regular security reviews and audits** | Quarterly review schedule documented in `/docs/runbooks/audit-cadence.md`; auditor persona view in dashboard; exportable audit pack | §5.3, §6 |
| **Stay updated on latest threats and trends** | NVD + OSV.dev + KEV catalog ingestion in AISec; monthly "threat brief" doc in `/docs/threat-briefs/` | §3.4, §8 Phase 14 |
| **Recommend improvements to security policies and procedures** | ADRs in `/docs/architecture/`; policy-change PRs reviewable in git history | §11 |
| **Provide training and support to dev teams on secure coding** | Secure-coding mini-tutorials in `/docs/secure-coding/` mirroring Aivistix's voice, linked from PR comments | §6 |
| **Document security findings and remediation** | Every finding has structured triage record; every fixed bug appends to `/docs/skills/bug-log.md` | §2.2, §3.5 |
| **Report to management on security posture** | CISO persona view + monthly auto-generated posture report PDF | §6 |
| **Cloud security practices and tools (AWS)** | Prowler, ScoutSuite, Security Hub, GuardDuty, Inspector, Macie, IAM Access Analyzer — all integrated | §3.4 |
| **Secure coding standards and frameworks** | OWASP ASVS v4.0.3 mapping enforced on every Pursh finding | §3.5, §6 |
| **Regulatory compliance (GDPR, HIPAA)** | Compliance-mapping layer: each finding tagged to GDPR Art. 32 sub-clauses + HIPAA Security Rule sections | §4.5 |

### 1.7 Honest goal statement
This project does **not** deliver "7 years of experience from one repo." What it *does* deliver:

- **Broad mid-level coverage (3–4 YOE-equivalent)** across AppSec, CloudSec, AI Security, and DevSecOps.
- **Senior-depth (5–7 YOE-equivalent) in 2–3 chosen specializations** picked after Phase 8 based on what the owner finds most interesting and the job market values.
- **Public artifacts hiring managers actually look at:** public repo, working demo at `aisec.aivistix.com`, written threat models for Pursh, written incident postmortems from monthly tabletops, ADRs, chaos-drill record.

**Realistic timeline:** 6–9 months of consistent evenings/weekends. Phase 0–8 in the first ~4 months. Pursh and AISec are built in parallel — Pursh exists as a scan target from Phase 2 onward.

---

## 2. Robustness Practices (mandatory)

From *"How to Write Robust Code with Claude Code"* (Eivind Kjosbakken, TDS, May 2026). Non-negotiable.

### 2.1 Plan mode is the default
- Always enter plan mode before non-trivial work. Non-trivial = touches more than one file, adds a scanner, changes CI, changes data model, touches auth, modifies Pursh's PHI surface (even synthetic).
- Plan must include: files to change, files to create, expected output, rollback strategy, at least one risk.
- **The agent asks clarifying questions, not the user.** Push back when ambiguous.

### 2.2 Skill files (knowledge base)
`/docs/skills/` holds long-lived markdown. Update after every session; every bug appends a "Bug → Root cause → Fix → Prevention" entry to `/docs/skills/bug-log.md`.

Required files (create on demand):

| File | Purpose |
|---|---|
| `/docs/skills/semgrep.md` | Rule packs, FP patterns, custom rules |
| `/docs/skills/zap.md` | Baseline vs full, auth scripts, FPs |
| `/docs/skills/trivy.md` | Severity policy, ignore files, fs vs image |
| `/docs/skills/syft-grype.md` | CycloneDX vs SPDX, DB freshness |
| `/docs/skills/gitleaks.md` | Custom rules, allowlists, historical scans |
| `/docs/skills/promptfoo-garak.md` | LLM red-teaming, prompt injection tests |
| `/docs/skills/prowler.md` | Compliance packs, custom checks |
| `/docs/skills/scoutsuite.md` | Multi-cloud, HTML report parsing |
| `/docs/skills/aws-security-hub.md` | ASFF, dedup logic |
| `/docs/skills/guardduty.md` | Findings types, response automation |
| `/docs/skills/iam-access-analyzer.md` | Findings flow, archive rules |
| `/docs/skills/github-actions.md` | Reusable workflows, OIDC, retention |
| `/docs/skills/fastapi-platform.md` | Architecture, auth, deployment |
| `/docs/skills/supabase.md` | RLS patterns, auth flows, BAA caveats |
| `/docs/skills/dashboard.md` | Persona views, mapping logic |
| `/docs/skills/threat-modeling.md` | STRIDE/PASTA process, templates |
| `/docs/skills/incident-response.md` | Runbook structure, tabletop process |
| `/docs/skills/hipaa-mapping.md` | HIPAA Security Rule mapping decisions |
| `/docs/skills/gdpr-mapping.md` | GDPR Art. 32 mapping decisions |
| `/docs/skills/ai-security.md` | OWASP LLM Top 10, prompt injection patterns |
| `/docs/skills/bug-log.md` | Every bug: root cause, fix, prevention |
| `/docs/skills/false-positive-triage.md` | FP decision criteria |

### 2.3 Context window hygiene
- Reset before ~300–400k tokens. Reset on: scanner switch, AISec↔Pursh switch, infra↔dashboard switch, coding↔triage switch.
- Before reset, write handoff into the relevant skill file.

### 2.4 Agent code review
Every PR reviewed by a second agent session with clean context:
> "Review PR #N. Do not write code. Read CLAUDE.md, then `/docs/skills/bug-log.md`, then the diff. List concrete robustness, security, and correctness risks. Flag patterns from bug-log.md."

Alternate model families when possible.

### 2.5 Pre-commit verification
Author agent self-checks:
> "Is this production-ready? Walk through error handling, input validation, logging, secrets handling, idempotency, failure modes, test coverage. List what's not ready."

Pre-commit hooks: `ruff`, `black`, `mypy`, `gitleaks`, `detect-secrets`, `yamllint`, `terraform fmt`, `tflint`, `checkov`.

### 2.6 Reusable, break-resistant scanner adapters
Every scanner integration:
- Versioned composite GitHub Action in `pipelines/github-actions/<scanner>/` with own `action.yml`, README, CHANGELOG
- Contract tests with golden-file outputs in `tests/contracts/<scanner>/`
- Schema validator at ingestion boundary — malformed scanner output fails loudly
- Circuit breaker in ingestion adapter — 3 malformed outputs → dead-letter queue + alert
- Documented swap path: replacing Semgrep with SonarQube means writing one adapter, not rewriting AISec

---

## 3. Architecture

### 3.1 High-level diagram
```
                ┌─────────────────────────────────────────────┐
                │           aivistix.com (existing)           │
                │     OIDC provider · shared design system    │
                └────────────────────┬────────────────────────┘
                                     │ OIDC (AISec auth only)
                                     ▼
┌─────────────────┐   ┌──────────────────────────────────────────────┐
│ Pursh repo      │──▶│       GitHub Actions (per-repo CI)           │
│ (in monorepo)   │   │   Reusable composite actions per scanner     │
│ + customer repos│   │   SAST·DAST·SCA·SBOM·Container·Secrets·IaC   │
└─────────────────┘   │   + LLM red-team (promptfoo) for AI flows    │
                      └────────────┬─────────────────────────────────┘
                                   │ SARIF, CycloneDX, ASFF, JSON
                                   ▼
                      ┌──────────────────────────────────────────┐
                      │   AWS account: AISec control plane       │
                      │                                          │
                      │   FastAPI ingest API (ECS Fargate)       │
                      │   ├─ /findings  /sboms  /threat-models   │
                      │   ├─ Schema validators per scanner       │
                      │   ├─ Normalizer → unified Finding model  │
                      │   ├─ OWASP/ASVS/CIS/HIPAA/GDPR mapper    │
                      │   ├─ Triage workflow engine              │
                      │   ├─ Notification dispatcher             │
                      │   └─ Incident-response orchestrator      │
                      │                                          │
                      │   Workers (ECS Fargate + SQS)            │
                      │   ├─ AppSec ingestion                    │
                      │   ├─ CloudSec ingestion (ASFF)           │
                      │   ├─ Security Hub / GuardDuty poller     │
                      │   ├─ CVE/OSV/KEV feed ingester           │
                      │   └─ Chaos-drill runner                  │
                      └─────────┬────────────────────┬───────────┘
                                │                    │
                  ┌─────────────▼──────┐   ┌─────────▼──────────┐
                  │ Postgres (RDS)     │   │ OpenSearch + S3    │
                  │ findings, triage,  │   │ SARIF, SBOMs,      │
                  │ policies, threat   │   │ raw scan logs,     │
                  │ models, runbooks,  │   │ free-text search   │
                  │ compliance mapping │   │                    │
                  └────────────────────┘   └────────────────────┘
                                │
                  ┌─────────────▼──────────────────────────────┐
                  │ AISec dashboard (Next.js, on aisec.*)      │
                  │ Public read-only + 5 authenticated personas│
                  └────────────┬───────────────────────────────┘
                               │
                  ┌────────────▼──────────────────────────┐
                  │ PR comments · Slack · email · webhooks│
                  └───────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│  Pursh — synthetic telehealth app (in same monorepo)           │
│                                                                │
│  Next.js frontend  ──▶  FastAPI backend  ──▶  Supabase (DB+Auth)│
│       │                       │                      │         │
│       │                       ▼                      ▼         │
│       │                  AWS S3 (PHI files,    Supabase Storage│
│       │                  KMS-encrypted)        (general assets)│
│       │                       │                                │
│       └──▶ LLM call boundary ─┴──▶ OpenAI/Bedrock              │
│            (logged, rate-limited, PHI-redacted)                │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Tech stack
**AISec platform:**
| Layer | Choice |
|---|---|
| Backend | Python 3.12 + FastAPI |
| ORM | SQLAlchemy 2.0 + Alembic |
| DB | Postgres 16 (RDS Multi-AZ) |
| Object store | S3 |
| Search | OpenSearch |
| Queue | SQS (FIFO for ingest, standard for notifications) |
| Cache | ElastiCache Redis |
| Compute | ECS Fargate |
| IaC | Terraform |
| Secrets | AWS Secrets Manager + Parameter Store |
| Auth | OIDC federation from aivistix.com |
| Frontend | Next.js 15 (App Router) |
| Observability | OpenTelemetry → X-Ray + CloudWatch + Grafana |

**Pursh app:**
| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 15 | Same stack as AISec dashboard, reuses design system |
| Backend | Python 3.12 + FastAPI | Same stack as AISec, single language |
| DB | **Supabase Postgres** with **RLS enforced** | Fast iteration, demoable row-level security |
| Auth | **Supabase Auth** with MFA | Separate from Aivistix OIDC since Pursh simulates consumer app |
| File storage | **AWS S3 with KMS CMK** + bucket policy | Demonstrates cloud security; lab results, prescriptions |
| AI integration | OpenAI API (or AWS Bedrock if owner prefers AWS-native) | Phased — see §4.6 |
| Deployment | Vercel (frontend) + ECS Fargate (backend) | Vercel for speed; ECS for the security story |

### 3.3 AppSec scanner stack (open-source only)
| Category | Tool | Output | Notes |
|---|---|---|---|
| SAST | Semgrep CE | SARIF | `p/owasp-top-ten`, `p/security-audit`, Python + JS packs |
| DAST | OWASP ZAP | SARIF/JSON | Baseline on PR, full nightly |
| SCA | Trivy fs + Grype | SARIF + JSON | Trivy on repo, Grype on SBOM |
| SBOM | Syft | CycloneDX 1.5 + SPDX 2.3 | Generate once, scan many |
| Container | Trivy image | SARIF | Pre-push gate |
| Secrets | Gitleaks + detect-secrets | SARIF | PR + historical scans |
| IaC | Checkov + tfsec | SARIF | Terraform, K8s manifests |
| **LLM red-team** | **promptfoo + Garak** | JSON | Prompt injection, jailbreak, PHI-leak tests on Pursh AI flows |

### 3.4 CloudSec scanner stack (AWS-first)
| Category | Tool | Output | Notes |
|---|---|---|---|
| CSPM | Prowler | JSON + ASFF | CIS AWS, AWS Foundational |
| CSPM (alt) | ScoutSuite | JSON + HTML | Cross-validation |
| Native posture | AWS Security Hub | ASFF | Aggregates GuardDuty + Inspector + Macie |
| Threat detection | GuardDuty | ASFF | |
| Workload vuln | Inspector v2 | ASFF | EC2, ECR, Lambda |
| Data classification | Macie | ASFF | S3 sensitive-data scanning (PHI-relevant) |
| IAM analysis | IAM Access Analyzer | ASFF | External + unused access |
| Config drift | AWS Config + Conformance Packs | JSON | Continuous compliance |

### 3.5 Unified Finding model
```python
class Finding(BaseModel):
    id: UUID
    scanner: ScannerName
    scanner_rule_id: str
    discipline: Literal["appsec","cloudsec","aisec","devsecops"]
    severity: Literal["critical","high","medium","low","info"]
    target: Literal["aisec","pursh","customer_repo"]
    cwe: list[str]
    owasp_top10_2021: str | None
    owasp_llm_top10: str | None         # LLM01..LLM10 if applicable
    asvs_v4_controls: list[str]
    cis_aws_controls: list[str]
    nist_csf_subcategories: list[str]
    hipaa_security_rule: list[str]      # e.g., ["164.312(a)(1)", "164.312(b)"]
    gdpr_art32_subclauses: list[str]    # e.g., ["Art32(1)(a)", "Art32(1)(b)"]
    title: str
    description: str
    remediation: RemediationCard | None # pulled from /app/mappings/remediation/
    location: FindingLocation
    first_seen: datetime
    last_seen: datetime
    status: Literal["open","triaged","accepted_risk","fixed","false_positive"]
    triage: TriageRecord | None
    threat_model_ref: UUID | None
    incident_ref: UUID | None
    raw: dict
```

All mappings (CWE→OWASP→ASVS, AWS resource→CIS, finding→HIPAA, finding→GDPR) live as data files under `/app/mappings/`. **Never hardcode in business logic.**

---

## 4. Subsystem Modules

### 4.1 Threat Modeling
- **STRIDE for every microservice** at design time.
- **PASTA for high-risk services** (anything touching PHI, auth, payments).
- Threat models live at `/docs/threat-models/<service>.md`. Markdown + Mermaid only.
- **Pursh has a dedicated threat model** at `/docs/threat-models/pursh-overall.md` plus one per service (auth, patient-records, doctor-matching-llm, file-upload).
- CI fails if: new service has no threat model; threat model not reviewed in 90 days; critical threat lacks mitigation/accepted-risk justification.

### 4.2 Incident Response
- Runbooks at `/docs/runbooks/<scenario>.md`, NIST 800-61 structure (detection / triage / containment / eradication / recovery / postmortem).
- **15 top runbooks** built in Phase 11 (compromised IAM key, exposed S3, malicious container, supply-chain attack, critical CVE, compromised CI runner, web app compromise, DDoS, insider threat, phishing, GuardDuty critical, secrets leaked to public repo, ransomware, DB breach, SaaS compromise).
- **Pursh-specific runbook:** `pursh-phi-exposure.md` — synthetic PHI exposed in a finding, walk through breach-notification timing simulation under HIPAA §164.408 and GDPR Art. 33.
- **Tabletop cadence:** monthly. Every drill produces a postmortem at `/docs/runbooks/postmortems/YYYY-MM-DD-<scenario>.md`.
- **Chaos-drill runner** at `app/chaos/` injects failures (kill scanner, corrupt SARIF, expire IAM key, simulate PHI in a Pursh log) to make drills realistic.

### 4.3 Five-Persona Dashboard
Same data, five lenses. RBAC enforced at API layer.

| Persona | Cares about | Views |
|---|---|---|
| Developer | "What did I break?" | PR-scoped findings, remediation card, FP justification |
| Security Engineer | Triage, tuning, policy | All findings, FP rate, scanner health, rule tuning |
| CISO/Executive | Risk posture | Critical/High over time, MTTR, top vulnerable repos, AppSec vs CloudSec balance |
| Compliance Auditor | Evidence & mappings | OWASP/ASVS coverage, CIS AWS, HIPAA coverage matrix, GDPR Art.32 matrix, exportable audit pack |
| Operations | Pipeline health | Scan duration, failure rates, queue depth, cost per scan, chaos-drill results |

**Public read-only:** anonymized findings against Pursh demo data, OWASP coverage, sample threat model, sample postmortem. Marketing surface that proves AISec works.

### 4.4 Real-Time Feedback
- **PR comments** via reviewdog + SARIF. Inline on changed lines only. Cap at 20 per PR.
- **Slack/Teams:** one channel per repo, critical+high only by default, rate-limited to 1 msg per PR per 10 min.
- **Email digests:** daily for security engineers, weekly for CISOs and auditors.
- **Webhooks:** outgoing with HMAC signature; documented schema for Jira/ServiceNow/PagerDuty.
- **Gating:** block on new critical; warn on high without triage; baseline-grandfathering for 30 days per repo.

### 4.5 Compliance Mapping Layer (HIPAA + GDPR)
This is the **mapping discipline**, not a compliance certification. AISec does not claim to make Pursh HIPAA-compliant; it claims to **demonstrate which Pursh controls map to which regulatory requirements**.

**HIPAA Security Rule mapping** (each Pursh control documented in `/docs/compliance/hipaa-mapping.md`):

| HIPAA section | Requirement | Pursh implementation |
|---|---|---|
| §164.312(a)(1) | Access control | Supabase RLS policies on patient_records; FastAPI RBAC middleware |
| §164.312(a)(2)(i) | Unique user identification | Supabase Auth UUIDs; no shared accounts |
| §164.312(a)(2)(iii) | Automatic logoff | Session timeout 15 min; refresh-token rotation |
| §164.312(a)(2)(iv) | Encryption and decryption | AES-256 at rest (Supabase + S3 with KMS CMK) |
| §164.312(b) | Audit controls | `audit_log` table — every read/write of patient data logged with actor, timestamp, before/after |
| §164.312(c)(1) | Integrity | Checksum on uploaded files; cryptographic signatures on critical records |
| §164.312(d) | Person/entity authentication | MFA required; OIDC tokens with short TTL |
| §164.312(e)(1) | Transmission security | TLS 1.3 enforced, HSTS, no fallback |
| §164.308(a)(1)(ii)(D) | Information system activity review | Weekly auto-generated review in CISO dashboard view |
| §164.408 | Breach notification | Runbook simulates the 60-day notification timeline |

**GDPR Article 32 mapping** (in `/docs/compliance/gdpr-mapping.md`):

| Art. 32 sub-clause | Requirement | Pursh implementation |
|---|---|---|
| 32(1)(a) | Pseudonymization & encryption | Patient IDs separated from PII; AES-256 at rest |
| 32(1)(b) | Confidentiality, integrity, availability, resilience | TLS, audit logs, RDS Multi-AZ, S3 versioning |
| 32(1)(c) | Ability to restore availability | RDS PITR, S3 versioning, documented RTO/RPO |
| 32(1)(d) | Regular testing and evaluation | Monthly tabletops, scheduled DAST scans, this whole project |
| 32(2) | Risk-appropriate measures | Threat model documents the risk assessment |

**Path to real HIPAA (documented, not implemented in v1):**
1. Sign BAA with Supabase (paid Team plan) and AWS (default for HIPAA-eligible services).
2. Enable encryption everywhere with customer-managed KMS keys.
3. Implement formal Security Risk Assessment per §164.308(a)(1)(ii)(A).
4. Designate Security Officer (§164.308(a)(2)) and Privacy Officer.
5. Implement workforce training program (§164.308(a)(5)).
6. Document policies and procedures per §164.316.
7. Engage third-party HIPAA assessor.

In v1, document these but **do not implement**, and ensure no real PHI ever enters the system.

### 4.6 AI Security Module
AISec scans Pursh's three AI integration flows. OWASP Top 10 for LLM Applications (2025) is the framework.

**Three phased AI integrations in Pursh:**

| Phase | Feature | Risk profile | Mitigations |
|---|---|---|---|
| **AI-1** | **Doctor-matching:** symptoms → recommended specialty | Lowest. No medical advice given to patient | Input length cap, prompt injection tests, output validation against specialty allowlist |
| **AI-2** | **Visit summarization:** patient history → doctor-facing summary | Medium. PHI in prompt | PHI redaction layer on input; LLM provider data-processing addendum; audit log every call; no training on data |
| **AI-3** | **Symptom checker:** patient → possible conditions, urgency | Highest. Borderline medical advice | Prominent "not medical advice" UI banner; conservative output (always recommend "consult doctor"); rate limiting; refusal on emergency symptoms with hotline display |

**LLM Top 10 testing via promptfoo + Garak in CI:**

| LLM Top 10 | Test |
|---|---|
| LLM01 — Prompt Injection | Inject "ignore previous instructions" in symptom field |
| LLM02 — Insecure Output Handling | Render LLM output as plain text, never HTML |
| LLM03 — Training Data Poisoning | N/A — using vendor models |
| LLM04 — Model DoS | Token-count caps, rate limits, timeout |
| LLM05 — Supply Chain | SBOM tracks LLM SDK and pinned versions |
| LLM06 — Sensitive Info Disclosure | PHI redaction test cases; output never echoes patient ID |
| LLM07 — Insecure Plugin Design | N/A in v1 — no function calling |
| LLM08 — Excessive Agency | LLM has zero write access to DB or actions |
| LLM09 — Overreliance | "Not medical advice" disclaimer everywhere |
| LLM10 — Model Theft | API keys in Secrets Manager; CloudTrail on access |

**Findings discipline:** AI security findings flow into the same unified Finding model with `discipline="aisec"` and `owasp_llm_top10` populated.

---

## 5. SCM Hardening

**The repo itself must look like it was built by someone who knows source-code-management security.** These are the visible artifacts (referenced by JD line "Review and enhance SCM security practices").

### 5.1 Required artifacts in repo
| File | Purpose |
|---|---|
| `CODEOWNERS` | Sensitive paths (auth, mappings, runbooks, IaC) require security review |
| `.github/branch-protection.md` | Documents the branch protection rules applied to `main` |
| `.github/pull_request_template.md` | Security checklist on every PR — threat model touched? secrets handled? auth changed? |
| `.github/dependabot.yml` | Daily for production deps, weekly for dev deps |
| `.github/SECURITY.md` | Vulnerability disclosure policy for this repo |
| `.gitignore` | Strict — no `.env`, no `.pem`, no `*.key` |
| `.pre-commit-config.yaml` | Gitleaks, detect-secrets, ruff, black, mypy, terraform fmt, checkov |
| `.github/workflows/secret-scan.yml` | Gitleaks on PR + scheduled full-history scan weekly |
| `commit-signing-policy.md` | Signed commits required on `main`; how to set up |
| `/docs/scm-hardening.md` | Master document explaining the whole SCM security posture |

### 5.2 Branch protection rules (documented + enforced)
- `main` requires: signed commits, linear history, at least 1 approving review, CODEOWNERS review on sensitive paths, all status checks pass, conversations resolved, up-to-date with base.
- Force pushes blocked; deletions blocked.
- Admins cannot bypass.

### 5.3 Secrets rotation
- Quarterly rotation of all long-lived credentials (those that exist; OIDC-from-GitHub-to-AWS means there should be very few).
- Runbook: `/docs/runbooks/secret-rotation.md`.
- AWS Secrets Manager rotation lambdas where supported.

### 5.4 Supply chain (v1 scope minimal, future expansion)
- Dependabot enabled.
- SBOM generated and stored per build (Phase 4).
- **Future (out of v1):** SLSA Level 3 provenance, sigstore signing, in-toto attestations. Documented in `/docs/architecture/future-supply-chain.md` so reviewers see you know about it.

---

## 6. Secure Coding Training (the JD's "Provide training to dev teams")
- `/docs/secure-coding/` holds short tutorials mirroring Aivistix's voice but for *developers*, not beginners.
- Topics: SQL injection in SQLAlchemy; XSS in React; SSRF; insecure deserialization; weak crypto; broken auth; secrets in code; CSRF; mass assignment; open redirect; SSRF in webhooks; PHI in logs.
- Each tutorial has: **what the weakness is**, **vulnerable code example**, **fixed code example**, **how Semgrep detects it**, **how the developer fixes it next time**.
- **Linked from PR comments:** when Semgrep flags CWE-89, the PR comment links to the SQL-injection tutorial.

---

## 7. Phased Build Plan

Pursh and AISec are built in parallel. Pursh is the scan target from Phase 2 onward.

| Phase | AISec deliverable | Pursh deliverable | Exit criteria |
|---|---|---|---|
| **0** | Monorepo, CLAUDE.md, pre-commit, Terraform skeleton, FastAPI `/healthz`, OIDC from aivistix.com, full SCM hardening artifacts (§5) | — | `terraform plan` clean; login redirect works; CODEOWNERS in place |
| **1** | Ingest API (`/findings`, `/sboms`), Postgres schema, SARIF + ASFF normalizers | Pursh skeleton — Next.js + FastAPI hello, Supabase project | POST a SARIF file → normalized Finding in DB; Pursh shows synthetic patient list |
| **2** | **SAST: Semgrep** composite action against Pursh | Patient + Doctor + Symptom models in Supabase with RLS | Semgrep PR comment shows findings on Pursh; RLS blocks cross-patient queries in tests |
| **3** | **SCA: Trivy fs** | Pursh booking flow (patient picks doctor) | Vulnerable test dep flows to dashboard |
| **4** | **SBOM: Syft + Grype** | Pursh visit notes feature | CycloneDX in S3, Grype findings ingested |
| **5** | **Container: Trivy image** with pre-push gate | Pursh deployed to ECS (backend) and Vercel (frontend) | Vulnerable image fails build |
| **6** | **Secrets: Gitleaks + IaC: Checkov/tfsec** | Pursh file upload (lab results PDF to S3 with KMS) | Leaked test secret blocked; bad Terraform blocked |
| **7** | **DAST: ZAP baseline on PR + full nightly** | Pursh auth + MFA hardened | ZAP findings appear within 10 min of PR |
| **8** | **CloudSec: Prowler + ScoutSuite + Security Hub** | Pursh AWS account scanned | AWS sandbox findings in dashboard |
| **9** | **CloudSec extended: GuardDuty + Inspector + Macie + IAM Access Analyzer** | Macie configured to detect synthetic PHI patterns in S3 | All four sources flow + correlate |
| **10** | **AI Security module: promptfoo + Garak** | **Pursh AI-1 (doctor-matching) ships** with prompt-injection tests | LLM red-team runs in CI; PHI-redaction test passes |
| **11** | **Threat models + IR runbooks (15) + chaos-drill runner** | **Pursh AI-2 (visit summarization)** with PHI-redaction layer | Threat models for all Pursh services; first tabletop drill complete |
| **12** | **Compliance mapping layer (HIPAA + GDPR)** | **Pursh AI-3 (symptom checker)** with disclaimers + rate limits | Auditor dashboard shows HIPAA + GDPR coverage matrix for Pursh |
| **13** | **Dashboard MVP: Developer + Security personas** | Pursh user-facing polish | Both personas log in, see real data |
| **14** | **CISO + Compliance Auditor + Ops personas; exportable audit pack; threat-brief ingestion** | — | Auditor exports OWASP+ASVS+HIPAA+GDPR PDF |
| **15** | **Public read-only view at aisec.aivistix.com** | Pursh public demo at pursh.aivistix.com with synthetic data | Both subdomains live |
| **16** | **Slack + email + webhooks + merge gating** | — | Critical finding gates merge + pings Slack |
| **17** | **Hardening — load test, chaos drills, FP triage cleanup** | — | p95 ingest < 500ms, FP rate < 15% per scanner |
| **18** | **Specializations deep-dive (pick 2–3)** | — | Each specialization has a written deep-dive doc |

**Honest timeline:** 6–9 months evenings/weekends. Phase 0–7 ≈ 3–4 months. Pursh+AISec parallel work is the main accelerator vs v2.

---

## 8. Anti-Patterns
1. Treating scanners as black boxes — tune within 2 weeks of integration.
2. Scanning everything at max severity — start critical+high gating only.
3. No baseline — grandfather existing findings 30 days per repo.
4. Hardcoding CWE/OWASP/HIPAA/GDPR mappings in business logic — use `/app/mappings/`.
5. Storing raw scanner output as source of truth — normalize.
6. Forgetting AISec scans itself — eat your own dog food.
7. Building dashboard charts before findings flow end-to-end.
8. Letting context windows balloon past 400k tokens.
9. Skipping skill-file updates.
10. Confusing "no findings" with "secure."
11. Duplicating Aivistix user store — OIDC federation only for AISec.
12. Blurring Aivistix / AISec / Pursh brand voices.
13. Auto-remediation before triage is solid.
14. Threat models nobody reviews — CI enforces freshness.
15. Runbooks never drilled — fiction.
16. **Real PHI ever entering Pursh** — synthetic only, hard rule.
17. **Claiming HIPAA compliance** — only claim *mapping*.
18. **LLM with write access in Pursh** — read-only forever in v1.
19. **PHI in LLM prompts without redaction** — redaction layer is mandatory before AI-2 ships.
20. **Pursh deployed without disclaimers** — every page shows the two banners from §1.2.

---

## 9. Repository Layout

```
.
├── CLAUDE.md
├── docs/
│   ├── skills/                     # knowledge base — §2.2
│   ├── architecture/               # ADRs
│   ├── threat-models/              # one .md per service — §4.1
│   ├── runbooks/                   # one .md per scenario — §4.2
│   │   └── postmortems/
│   ├── compliance/
│   │   ├── hipaa-mapping.md
│   │   ├── gdpr-mapping.md
│   │   └── path-to-real-hipaa.md
│   ├── secure-coding/              # dev training tutorials — §6
│   ├── threat-briefs/              # monthly threat updates
│   ├── scm-hardening.md
│   └── public/                     # marketing content for aisec.aivistix.com
├── aisec/                          # AISec platform
│   ├── app/                        # FastAPI control plane
│   │   ├── api/
│   │   ├── ingest/
│   │   │   ├── sarif/
│   │   │   ├── asff/
│   │   │   ├── cyclonedx/
│   │   │   └── spdx/
│   │   ├── mappings/               # CWE↔OWASP↔ASVS↔CIS↔HIPAA↔GDPR
│   │   │   └── remediation/        # remediation cards per finding type
│   │   ├── models/
│   │   ├── notifications/
│   │   ├── policies/
│   │   ├── triage/
│   │   ├── chaos/
│   │   ├── auth/                   # OIDC federation
│   │   ├── rbac/
│   │   └── tests/
│   │       └── contracts/
│   └── dashboard/                  # Next.js — public + 5 personas
├── pursh/                          # Pursh demo app
│   ├── frontend/                   # Next.js — patient + doctor UI
│   ├── backend/                    # FastAPI — Supabase + S3 + LLM adapter
│   │   ├── api/
│   │   ├── auth/                   # Supabase Auth integration
│   │   ├── llm/                    # AI-1, AI-2, AI-3 with redaction
│   │   ├── audit/                  # audit_log writes
│   │   └── storage/                # S3 + KMS adapter
│   └── seed/                       # synthetic-data generators (Synthea)
├── infra/
│   └── terraform/
│       ├── aisec/                  # AISec AWS resources
│       └── pursh/                  # Pursh AWS resources
├── pipelines/
│   └── github-actions/
│       ├── semgrep/
│       ├── zap/
│       ├── trivy-fs/
│       ├── trivy-image/
│       ├── syft/
│       ├── grype/
│       ├── gitleaks/
│       ├── checkov/
│       ├── tfsec/
│       ├── prowler/
│       ├── promptfoo-garak/        # LLM red-team
│       └── threat-model-check/
├── scanners/                       # scanner configs (rules, contexts, policies)
├── scripts/
├── .github/
│   ├── workflows/                  # AISec + Pursh scanned by each other's pipelines
│   ├── CODEOWNERS
│   ├── pull_request_template.md
│   ├── dependabot.yml
│   ├── SECURITY.md
│   └── branch-protection.md
├── .pre-commit-config.yaml
├── commit-signing-policy.md
└── pyproject.toml
```

---

## 10. Coding Standards
- **Python 3.12**, `ruff` + `black`, `mypy --strict` on `aisec/app/` and `pursh/backend/`.
- **Hexagonal architecture:** routes → services → repositories. No business logic in routes. SQLAlchemy 2.0 typed style.
- **All external calls** through adapters with timeout + circuit breaker + retry-with-jitter.
- **Structured logging** (`structlog`, JSON) with `correlation_id`, `repo`, `scanner`, `finding_id`, and for Pursh — `actor_id`, never `patient_id_value` (use hashed IDs in logs).
- **No secrets in code or logs.** AWS Secrets Manager + Parameter Store. Gitleaks in pre-commit + CI.
- **Tests:** golden-file contract tests for normalizers; RLS tests for Pursh; LLM prompt-injection tests in CI.
- **Coverage:** 80% on `aisec/app/ingest`, `aisec/app/mappings`, `pursh/backend/auth`, `pursh/backend/llm`. 60% elsewhere.
- **Terraform:** `fmt`, `tflint`, `checkov` in CI. OIDC from GitHub Actions to AWS — no long-lived keys.
- **Pursh PHI rule:** all functions touching patient data must have a `# PHI-SAFE` comment and corresponding test. No exceptions.

---

## 11. Security Posture of AISec + Pursh Themselves
- **Admin access via SSO + MFA** through Aivistix IdP for AISec; Supabase Auth + MFA for Pursh admins.
- **Least-privilege IAM** — every service has its own role.
- **KMS everywhere** — RDS, S3, OpenSearch, Secrets Manager with customer-managed keys.
- **VPC isolation** — control plane in private subnets; only ALB public.
- **Audit logs everywhere** — AISec writes; Pursh writes to a dedicated `audit_log` table for HIPAA §164.312(b).
- **Backups** — RDS PITR, S3 versioning + lifecycle, OpenSearch snapshots, Supabase daily backups.
- **AISec scans itself + scans Pursh** — every PR runs full pipeline. Findings ingest into the same DB under `aisec-internal` and `pursh-target` repo identifiers.

---

## 12. Working Agreement for Claude Sessions
1. Read this file. Read relevant `/docs/skills/*.md`.
2. Read `/docs/skills/bug-log.md`.
3. Enter plan mode. Surface ambiguities.
4. Explain *why* before *how*.
5. Implement in small chunks.
6. End of session, propose skill-file updates.
7. Heavy context → suggest fresh session with handoff note.

**If this file conflicts with a user instruction, ask. Do not silently override.**

---

## 13. Open Questions
- [ ] Confirm Aivistix's existing auth mechanism (Cognito? Authentik? Supabase?) before Phase 0 OIDC work.
- [ ] AWS account strategy: single account with IAM separation, or multi-account via Control Tower? Multi-account is more realistic for the senior story.
- [ ] LLM provider: OpenAI (faster setup) or AWS Bedrock (all-AWS story, better for AI Security narrative)? Decide before Phase 10.
- [ ] Synthetic data source: Synthea (gold standard, complex setup) or hand-written seed scripts (simple, less realistic)? Decide before Phase 2.
- [ ] Pursh public demo data — fully synthetic, or anonymized public dataset (e.g., MIMIC-III with explicit attribution)? Decide before Phase 15.
- [ ] Pick 2–3 specialization areas at end of Phase 14.
- [ ] Tabletop exercise partner — solo, or peer from security community? Before Phase 11.

---

## 14. Changelog

| Version | Date | Change |
|---|---|---|
| v1 | bootstrap | Initial doc — generic security pipeline learning project |
| v2 | bootstrap+1 | Sentinel rebrand under Aivistix; CloudSec + threat-modeling + IR added |
| **v3** | **bootstrap+2** | **Renamed Sentinel → AISec; Pursh telehealth demo app added as first-class subsystem; HIPAA + GDPR mapping module; OWASP LLM Top 10 / AI Security module; SCM hardening artifacts; JD-to-project mapping table; phased AI integration plan; expanded skill files** |

*Update this changelog whenever §1, §3, §4, §5, §6, or §7 changes materially.*
