# PCI-DSS v4.0 Compliance Mapping — Pursh + AISec

> **Scope note:** Pursh handles **synthetic card data only** (fake PANs, fake CVVs). No real cardholder data ever enters the system. The controls implemented are real; the data they protect is not. This document demonstrates what a PCI-DSS mapping looks like for a telehealth-adjacent SaaS platform — the same controls apply if Pursh were ever extended to handle real payments.

---

## Control-to-Implementation Matrix

### Requirement 1 — Network Security Controls

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 1.2.1 | Network security controls defined and implemented | pfSense/OPNsense VM segmenting MGMT/CORP/DMZ/RED subnets | `infra/terraform/` VPC + security group configs |
| 1.3.2 | Restrict inbound + outbound traffic to cardholder data environment | ECS Fargate security groups — inbound 443 only via ALB; no direct DB access | `infra/terraform/aisec/security_groups.tf` |
| 1.4.1 | Trusted and untrusted networks separated | VPC with public/private subnet split; ALB in public, ECS + RDS in private | Terraform plan output |

### Requirement 2 — Secure Configurations

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 2.2.1 | Configuration standards for all system components | Lynis audit + OpenSCAP CIS L1 profile applied to all EC2/ECS base images | `docs/compliance/evidence/lynis-*.html` |
| 2.2.7 | Non-console admin access encrypted | SSH only via bastion or SSM Session Manager; no password auth | `infra/terraform/aisec/ssm.tf` |
| 2.3.1 | All non-console admin access uses strong cryptography | TLS 1.3 enforced on ALB; SSH key pairs only | ALB listener config |

### Requirement 3 — Protect Stored Account Data

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 3.3.1 | SAD not retained after authorization | Pursh never stores raw card data — Stripe handles tokenization in future real impl | Architecture diagram note |
| 3.5.1 | PAN rendered unreadable anywhere stored | Synthetic PANs in Supabase stored with AES-256 via KMS CMK | `infra/terraform/pursh/kms.tf` |

### Requirement 4 — Protect Cardholder Data in Transit

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 4.2.1 | Strong cryptography for transmission | TLS 1.3 enforced; HSTS with 1-year max-age; no TLS < 1.2 | ALB SSL policy; ZAP TLS scan result |
| 4.2.2 | Policies for sending PANs via end-user messaging | Policy: no PANs in emails, Slack, or logs — enforced by Gitleaks + detect-secrets in CI | `.pre-commit-config.yaml` |

### Requirement 5 — Protect Against Malicious Software

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 5.2.1 | Anti-malware deployed on applicable components | Wazuh agents with rootcheck + malware detection on ECS hosts | Wazuh dashboard export |
| 5.3.3 | Anti-malware mechanisms updated | Wazuh agent auto-update; Trivy DB updated on every CI run | CI workflow logs |

### Requirement 6 — Develop and Maintain Secure Systems

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 6.2.4 | Secure coding training for devs | `/docs/secure-coding/` tutorials; linked from PR comments via reviewdog | PR comment examples |
| 6.3.3 | All components protected from known vulns | Dependency-Track policy: no High/Critical in cardholder-data-path deps; Trivy gates CI | DefectDojo SLA report |
| 6.4.1 | Web-facing apps protected against known attacks | ModSecurity + OWASP CRS in front of Pursh; ZAP baseline on every PR | ZAP scan results in DefectDojo |
| 6.4.2 | Automated technical solution detects and prevents web attacks | ModSecurity logging to Wazuh; ZAP active scan nightly | Wazuh alert count for ModSec events |

### Requirement 7 — Restrict Access

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 7.2.1 | Access control system in place | Supabase RLS on all patient-data tables; FastAPI RBAC middleware | RLS policy tests (`pursh/backend/tests/test_rls.py`) |
| 7.2.4 | User accounts and access reviewed quarterly | IAM Access Analyzer findings reviewed quarterly | IAM Access Analyzer export |

### Requirement 8 — Identify Users and Authenticate

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 8.2.1 | Unique IDs for all users | Supabase Auth UUIDs; no shared accounts | Supabase Auth dashboard |
| 8.4.2 | MFA required for all access into CDE | Supabase Auth MFA (TOTP) required for doctor role | Auth config + test |
| 8.6.1 | System/app accounts managed by policies | ECS task roles via OIDC; no long-lived access keys | `infra/terraform/aisec/iam.tf` |

### Requirement 10 — Log and Monitor

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 10.2.1 | Audit logs for all access to system components | Pursh `audit_log` table: every patient-data read/write logged with actor_id + timestamp | `pursh/backend/audit/` |
| 10.3.3 | Audit log files protected from destruction | CloudWatch log groups with 365-day retention; S3 log archive with Object Lock | `infra/terraform/aisec/cloudwatch.tf` |
| 10.4.1 | Audit logs reviewed daily | Wazuh daily compliance report; CISO dashboard alert summary | Wazuh scheduled report |

### Requirement 11 — Test Security

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 11.3.1 | Internal vuln scans quarterly | OpenVAS scans all subnets quarterly; results in DefectDojo | DefectDojo engagement history |
| 11.3.2 | External vuln scans by ASV | (Out of scope for synthetic demo; documented as gap) | `docs/compliance/gaps.md` |
| 11.4.1 | Pen testing methodology documented | ZAP DAST + Nuclei + manual Kali testing on Pursh; documented in threat models | `/docs/threat-models/pursh-overall.md` |
| 11.5.1 | Change detection mechanism deployed | Wazuh FIM on critical config files | Wazuh FIM policy |

### Requirement 12 — Support Information Security with Policies

| Req | Description | Pursh/AISec implementation | Evidence artifact |
|---|---|---|---|
| 12.3.2 | Targeted risk analysis performed | STRIDE threat model per Pursh service | `/docs/threat-models/` |
| 12.10.1 | Incident response plan maintained | IR runbooks for 15 scenarios + tabletop schedule | `/docs/runbooks/` |

---

## Tools Used for PCI-DSS Evidence Collection

| Tool | PCI-DSS role |
|---|---|
| OpenSCAP + SSG | Req 2 — secure config evidence (CIS L1 profile) |
| Lynis | Req 2 — host hardening audit |
| InSpec `pci-dss` profile | Automated control testing, machine-readable JSON |
| DefectDojo | Req 6.3.3, 11.3 — vuln lifecycle + SLA evidence |
| Dependency-Track | Req 6.3.3 — component CVE policy enforcement |
| Wazuh | Req 5, 10 — malware detection + audit logging |
| ModSecurity + CRS | Req 6.4 — WAF protection |
| ZAP | Req 6.4, 11.4 — dynamic app testing |
| IAM Access Analyzer | Req 7 — access review |

---

*Last updated: 2026-05-21 · Next review: 2026-08-21*
