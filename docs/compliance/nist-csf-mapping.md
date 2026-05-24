# NIST CSF 2.0 Compliance Mapping — AISec + Pursh

> NIST Cybersecurity Framework 2.0 (February 2024). Six Functions: Govern (GV), Identify (ID), Protect (PR), Detect (DE), Respond (RS), Recover (RC). This document maps Pursh and AISec controls to CSF 2.0 subcategories.
>
> Note: the `Finding` model's `nist_csf_subcategories` field already exists. The mapping data below populates `/app/mappings/nist_csf_2_0.json`.

---

## GV — Govern

The 2.0 addition (was implicit in 1.1). Organizational context, risk management strategy, supply chain security.

| Subcategory | ID | AISec/Pursh implementation |
|---|---|---|
| Organizational context established | GV.OC-01 | CLAUDE.md §1 — product context, audience, objectives |
| Risk tolerance defined | GV.RM-02 | CLAUDE.md §7 phase exit criteria; DefectDojo SLA policy |
| Cybersecurity policy established | GV.PO-01 | CLAUDE.md + SECURITY.md + branch-protection.md |
| Roles and responsibilities assigned | GV.RR-01 | CODEOWNERS; CLAUDE.md §4.3 five-persona RBAC |
| Supply chain risk managed | GV.SC-01 | Syft SBOM + Dependency-Track + Dependabot |

---

## ID — Identify

| Subcategory | ID | AISec/Pursh implementation |
|---|---|---|
| Asset inventory maintained | ID.AM-01 | Syft SBOM per build; Nmap asset scans; Dependency-Track component list |
| Software inventory | ID.AM-02 | Syft CycloneDX SBOMs stored in S3 per build |
| Data flows documented | ID.AM-03 | `/docs/threat-models/pursh-overall.md` DFDs |
| External systems catalogued | ID.AM-05 | Architecture diagram §3.1; OpenAI/Bedrock as documented third parties |
| Vulnerabilities identified | ID.RA-01 | DefectDojo aggregating all scanners |
| Threats identified | ID.RA-02 | MISP IOC feeds; monthly threat briefs in `/docs/threat-briefs/` |
| Risk responses prioritized | ID.RA-07 | DefectDojo severity + SLA triage workflow |
| Improvements identified | ID.IM-01 | `/docs/skills/bug-log.md`; postmortems in `/docs/runbooks/postmortems/` |

---

## PR — Protect

| Subcategory | ID | AISec/Pursh implementation |
|---|---|---|
| Identities managed | PR.AA-01 | Supabase Auth UUIDs; OIDC federation for AISec; no shared accounts |
| Authentication enforced | PR.AA-02 | MFA required (Supabase TOTP); short-TTL OIDC tokens |
| Least privilege enforced | PR.AA-05 | ECS task roles; Supabase RLS; IAM least-privilege policies |
| Physical access managed | PR.AA-06 | AWS managed (not applicable for cloud-native) |
| Secure config management | PR.PS-01 | Checkov + tfsec in CI; Lynis on EC2 hosts; OpenSCAP CIS profiles |
| Software installed securely | PR.PS-02 | Trivy image scan pre-push gate; Dependabot for dep updates |
| Backups maintained | PR.DS-11 | RDS PITR; S3 versioning + lifecycle; Supabase daily backups |
| Data-at-rest protected | PR.DS-01 | KMS CMK on RDS, S3, Secrets Manager, OpenSearch |
| Data-in-transit protected | PR.DS-02 | TLS 1.3; HSTS; no fallback below TLS 1.2 |
| Sensitive data identified | PR.DS-10 | Macie on S3 buckets; Gitleaks in CI + pre-commit |
| Secure development practiced | PR.PS-04 | Semgrep SAST + ZAP DAST on every PR; CLAUDE.md coding standards |
| Security in supply chain | PR.PS-05 | Syft + Grype; Dependabot; SBOM attestation |

---

## DE — Detect

| Subcategory | ID | AISec/Pursh implementation |
|---|---|---|
| Networks monitored | DE.CM-01 | Suricata (IDS) + Zeek (telemetry) on network segments |
| Physical environment monitored | DE.CM-02 | N/A — cloud-native |
| Personnel activity monitored | DE.CM-03 | Wazuh audit logs; IAM CloudTrail |
| External service activity monitored | DE.CM-06 | GuardDuty; CloudTrail; Pursh `audit_log` for third-party calls |
| Computing hardware monitored | DE.CM-09 | Wazuh FIM + rootcheck agents on all hosts |
| Adverse events detected | DE.AE-02 | Wazuh alerts + Sigma rules + Suricata rules |
| Event correlation performed | DE.AE-03 | Wazuh correlation rules; TheHive case aggregation |
| Detection estimated impact | DE.AE-04 | Severity tagging in DefectDojo + TheHive; MISP threat actor context |
| Incidents declared | DE.AE-06 | Wazuh → TheHive auto-escalation via webhook |

---

## RS — Respond

| Subcategory | ID | AISec/Pursh implementation |
|---|---|---|
| Response plan executed | RS.MA-01 | NIST 800-61 runbooks in `/docs/runbooks/`; TheHive case workflow |
| Incidents investigated | RS.AN-03 | TheHive investigation + Cortex enrichment + Velociraptor DFIR |
| Incidents contained | RS.CO-01 | Runbook containment steps (isolate, revoke, patch) |
| Incidents reported | RS.CO-02 | HIPAA §164.408 breach notification simulation; GDPR Art. 33 runbook |
| Improvements incorporated | RS.IM-01 | Postmortem → bug-log.md → process update after every tabletop |

---

## RC — Recover

| Subcategory | ID | AISec/Pursh implementation |
|---|---|---|
| Recovery plan executed | RC.RP-01 | Recovery steps in each IR runbook; RTO/RPO documented |
| Recovery actions communicated | RC.CO-03 | Slack notifications from TheHive; status page template |
| Restoration verified | RC.RP-05 | Post-recovery scan (Trivy + ZAP + Semgrep) confirms clean state |
| Backups tested | RC.RP-04 | Quarterly RDS restore drill documented in tabletop schedule |

---

## Finding Model Integration

The `nist_csf_subcategories` field on `Finding` accepts values like `["DE.CM-01", "PR.PS-04"]`.

Mapping data lives at `/app/mappings/nist_csf_2_0.json`. Structure:

```json
{
  "scanner_rule_patterns": {
    "semgrep": {
      "default": ["PR.PS-04", "DE.AE-02"],
      "cwe-89": ["PR.PS-04", "ID.RA-01"],
      "cwe-798": ["PR.DS-10", "PR.PS-04"]
    },
    "trivy": {
      "default": ["ID.RA-01", "PR.PS-02"],
      "critical": ["DE.AE-02", "RS.MA-01"]
    },
    "wazuh": {
      "default": ["DE.CM-09", "DE.AE-02"],
      "fim": ["DE.CM-09"],
      "rootcheck": ["DE.CM-09", "PR.PS-01"]
    }
  }
}
```

---

*Last updated: 2026-05-21 · Next review: 2026-08-21*
