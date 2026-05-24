# SOC 2 Type II Compliance Mapping — AISec + Pursh

> **Trust Services Criteria (TSC)** from the AICPA. Five categories: Security (CC), Availability (A), Processing Integrity (PI), Confidentiality (C), Privacy (P). For a developer-facing security platform like AISec + Pursh, Security and Availability are the primary categories. Confidentiality applies to findings data; Privacy applies to Pursh patient data.
>
> SOC 2 Type II measures **operating effectiveness over a period** (usually 6–12 months) — not just design. Every control below needs documented evidence of consistent operation, not just a one-time setup.

---

## CC1 — Control Environment

| Criteria | Description | AISec/Pursh implementation | Evidence |
|---|---|---|---|
| CC1.1 | Demonstrates commitment to integrity and ethical values | CLAUDE.md anti-patterns list; SECURITY.md vulnerability disclosure policy | CLAUDE.md §8; `.github/SECURITY.md` |
| CC1.2 | Board / management oversight | Owner sign-off documented in ADRs | `/docs/architecture/` ADRs |
| CC1.3 | Organizational structure and reporting | Five-persona RBAC documented | CLAUDE.md §4.3 |
| CC1.4 | Competence requirements | JD-to-project mapping shows required skills | CLAUDE.md §1.6 |
| CC1.5 | Accountability enforced | CODEOWNERS + branch protection + signed commits | `.github/CODEOWNERS`; `commit-signing-policy.md` |

---

## CC2 — Communication and Information

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC2.1 | Information security communication | PR template security checklist on every merge | `.github/pull_request_template.md` |
| CC2.2 | External communication of security | SECURITY.md vulnerability disclosure | `.github/SECURITY.md` |
| CC2.3 | Reporting failures to relevant parties | Slack + email alerts for critical findings; TheHive case escalation | DefectDojo notification config |

---

## CC3 — Risk Assessment

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC3.1 | Risk assessment process | STRIDE + PASTA threat models per service | `/docs/threat-models/` |
| CC3.2 | Fraud risk considered | Pursh: synthetic patient record manipulation scenarios in threat models | `/docs/threat-models/pursh-overall.md` |
| CC3.3 | Risk assessment updated for change | Threat model CI check — fails if model > 90 days stale | `.github/workflows/` threat-model-check |
| CC3.4 | Identifies + assesses significant vendor risks | Dependency-Track + Dependabot + Syft SBOM | Dependency-Track policy violations |

---

## CC4 — Monitoring

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC4.1 | Monitors + evaluates control effectiveness | Monthly tabletop drills + postmortems | `/docs/runbooks/postmortems/` |
| CC4.2 | Evaluates and communicates deficiencies | DefectDojo SLA breach reports; Wazuh compliance reports | DefectDojo monthly export |

---

## CC5 — Control Activities

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC5.1 | Selects and develops mitigating controls | Remediation loop: scan → triage → fix → verify in DefectDojo | DefectDojo engagement history |
| CC5.2 | Selects general IT controls | Checkov/tfsec IaC scanning; Wazuh FIM on critical files | CI scan results |
| CC5.3 | Deploys through policies and procedures | CLAUDE.md §10 coding standards; pre-commit hooks enforced | `.pre-commit-config.yaml` |

---

## CC6 — Logical and Physical Access Controls

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC6.1 | Restricts logical access | Supabase RLS on all Pursh patient tables; AISec RBAC per persona | RLS test results; RBAC tests |
| CC6.2 | Access provisioning | OIDC-based provisioning; no manual account creation | OIDC config |
| CC6.3 | Removes access when no longer needed | Offboarding runbook; IAM Access Analyzer external access findings | IAM Access Analyzer export |
| CC6.6 | Logical access from outside restricted | VPC private subnets; ALB-only ingress; SSH via SSM | Security group rules; SSM config |
| CC6.7 | PHI/sensitive data transmitted securely | TLS 1.3; HSTS; no plaintext transmission | ZAP TLS scan result |
| CC6.8 | Malware prevention | Trivy image scanning; Wazuh malware detection; Gitleaks | CI scan logs; Wazuh dashboard |

---

## CC7 — System Operations

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC7.1 | Detects and monitors configuration changes | Wazuh FIM on `/etc`, certs, app configs; AWS Config for IaC drift | Wazuh FIM alert history |
| CC7.2 | Monitors system components for anomalous behavior | Wazuh + Suricata + Falco + Zeek — all feeding into TheHive | Wazuh alert count over time |
| CC7.3 | Evaluates security events | TheHive case investigations with Cortex enrichment | TheHive closed-case history |
| CC7.4 | Responds to identified security incidents | IR runbooks tested monthly in tabletops | `/docs/runbooks/postmortems/` |
| CC7.5 | Identifies and remediates known vulns | DefectDojo vuln lifecycle; Dependency-Track CVE alerts | DefectDojo MTTR metrics |

---

## CC8 — Change Management

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| CC8.1 | Manages changes to infrastructure and software | Branch protection + PR review + signed commits + all CI checks must pass | GitHub branch protection settings |

---

## A1 — Availability

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| A1.1 | Current processing capacity | ECS autoscaling; CloudWatch capacity alarms | CloudWatch dashboard |
| A1.2 | Environmental threats addressed | RDS Multi-AZ; S3 cross-region replication; ECS across AZs | Terraform config |
| A1.3 | Recovery procedures tested | Quarterly RDS restore drill; chaos-drill runner | Tabletop postmortems |

---

## C1 — Confidentiality

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| C1.1 | Confidential information identified | Pursh `audit_log` tracks every patient-data access; KMS CMK on all stores | Audit log schema; KMS config |
| C1.2 | Confidential information destroyed when no longer needed | S3 lifecycle policies; Supabase data retention config | Terraform lifecycle rules |

---

## P — Privacy (Pursh-specific)

| Criteria | Description | Implementation | Evidence |
|---|---|---|---|
| P1.0 | Privacy notice provided | "Demonstration project — not a real medical service" banner on every Pursh page | CLAUDE.md §1.2 disclaimer requirement |
| P3.1 | Personal information collected only for stated purpose | Synthea-generated synthetic data only; no real PHI ever | Seed scripts in `pursh/seed/` |
| P6.1 | Personal information disclosed to third parties only as agreed | LLM calls use PHI-redaction layer; no patient data to OpenAI without redaction | `pursh/backend/llm/` redaction layer |

---

## Evidence Collection Strategy

SOC 2 Type II requires **evidence of consistent operation**, not a one-time check. Automate evidence collection:

| Evidence type | Collection method | Storage location | Frequency |
|---|---|---|---|
| Vuln scan results | DefectDojo engagement history export | `/docs/compliance/evidence/defectdojo/` | Monthly |
| Access logs | Wazuh audit module export | `/docs/compliance/evidence/wazuh/` | Monthly |
| FIM alerts | Wazuh FIM report | `/docs/compliance/evidence/wazuh/` | Weekly |
| IaC scan results | Checkov/tfsec CI output archived | S3 `aisec-artifacts/ci-scans/` | Per commit |
| SBOM + CVE status | Dependency-Track project export | S3 `aisec-artifacts/sboms/` | Per build |
| Host hardening | Lynis HTML report | `/docs/compliance/evidence/lynis/` | Monthly |
| IR drills | Tabletop postmortems | `/docs/runbooks/postmortems/` | Monthly |

---

*Last updated: 2026-05-21 · Next review: 2026-08-21*
