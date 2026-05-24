# Remediation Loop — Standard Operating Procedure

> This runbook defines the mandatory process for taking a security finding from detection to verified remediation. It applies to all findings ingested into DefectDojo regardless of source scanner.
>
> **Rule:** no finding is closed without a verification rescan. "I fixed it" is not evidence. A clean rescan is.

---

## The Loop

```
SCAN → TRIAGE → LEARN → REMEDIATE → VERIFY → DOCUMENT
```

---

## Step 1 — Scan

Findings enter DefectDojo automatically from CI (Semgrep, Trivy, ZAP, Gitleaks, Checkov, Nuclei) or from manual runs (OpenVAS, Lynis, OpenSCAP, InSpec).

DefectDojo deduplicates findings across scanners. A SQL injection found by both Semgrep and ZAP becomes one finding with two scanner references.

**Your only action in this step:** confirm the CI pipeline ran and results imported. Check the DefectDojo "All Findings" view is not stale.

---

## Step 2 — Triage

For every new **Critical** or **High** finding:

1. Open the finding in DefectDojo.
2. Confirm scanner-assigned severity is correct. Adjust if context changes it (e.g., a "Critical" SQLi in a read-only analytics endpoint that has no auth bypass path is a High).
3. Tag:
   - **CWE** — e.g., `CWE-89` for SQL injection
   - **Compliance controls** — which HIPAA / PCI-DSS / NIST CSF / SOC 2 controls does this finding violate? Add to the relevant fields.
   - **OWASP Top 10** — e.g., `A03:2021 - Injection`
4. Assign SLA deadline based on severity:
   - Critical → 3 days
   - High → 14 days
   - Medium → 30 days
   - Low → 90 days
5. Set status to **Active**.
6. If the finding is a false positive: document WHY (specific context that makes it safe), set status to **False Positive**, add to `/docs/skills/false-positive-triage.md`. Do not just dismiss — write the reasoning.

**Triage SLA:** complete triage within 24 hours of finding appearing in DefectDojo.

---

## Step 3 — Learn

Before writing a single line of fix code, understand the vulnerability class. This is the step most engineers skip — and it is why they fix the symptom but not the root cause.

**Web / code vulnerabilities (CWE-based):**
1. Look up the CWE at cwe.mitre.org — read "Description" and "Extended Description."
2. Find the matching tutorial in `/docs/secure-coding/<topic>.md`.
3. If it is a web vulnerability (SQLi, XSS, SSRF, etc.): open **OWASP WebGoat** and complete the corresponding lesson hands-on. WebGoat makes you exploit the vuln first, then explains the fix.
4. If it is a real CVE in a dependency: spin up the matching **Vulhub** environment, exploit the CVE against the real vulnerable version, then read the vendor patch notes before applying.

**Infrastructure / config findings:**
1. Read the specific Checkov or OpenSCAP rule documentation — it will name the CIS control or benchmark section.
2. Find the CIS Benchmark PDF for the relevant technology (AWS, Linux, K8s) and read the remediation guidance for that specific control.

**Why this matters:** understanding the weakness class means you fix the pattern, not just the line. A developer who fixes one SQL injection by adding a filter is still vulnerable to 10 others. A developer who understands CWE-89 and parameterized queries fixes all of them.

---

## Step 4 — Remediate

Apply the fix to the codebase, config, or infrastructure.

**Checklist before opening a PR:**
- [ ] Fix addresses the root cause, not just the symptom
- [ ] Added or updated a test that would have caught this finding originally
- [ ] Ran the self-check from CLAUDE.md §2.5 ("Is this production-ready?")
- [ ] No new secrets introduced (Gitleaks pre-commit hook must pass)
- [ ] If touching auth, PHI surface, or IaC: updated threat model if needed

**For dependency CVEs:** update to the patched version in `pyproject.toml` or `package.json`. If no patch exists, document the accepted risk in DefectDojo with a risk-acceptance note and a re-review date.

**For IaC findings:** fix the Terraform/CloudFormation and ensure `checkov` + `tfsec` pass locally before pushing.

---

## Step 5 — Verify

This step is non-negotiable. Fixes are not confirmed until a rescan shows the finding gone.

**Procedure:**

1. After your fix merges, trigger the relevant scanner manually (or wait for the next CI run):
   - Code vuln → re-run Semgrep: `semgrep --config=auto <affected_file>`
   - Dependency CVE → re-run Trivy: `trivy fs --exit-code 1 --severity HIGH,CRITICAL .`
   - Web vuln → re-run ZAP baseline against the staging deployment
   - IaC finding → re-run Checkov: `checkov -d infra/terraform/`
   - Network/host → re-run Nuclei or Lynis on the target

2. Confirm the specific finding is no longer reported.

3. In DefectDojo:
   - Set finding status to **Resolved**.
   - Add a note: "Fixed in PR #N. Verified clean by [scanner] rescan on [date]."
   - Close the finding.

**If the finding still appears:** do not close. Go back to Step 3/4. The fix was incomplete.

---

## Step 6 — Document

Append to `/docs/skills/bug-log.md` using this exact format:

```markdown
## [DATE] [SCANNER] [CWE-XXX] — [Short title]

**Bug:** [One sentence describing what the finding was and where]

**Root cause:** [The underlying weakness — not "we forgot to sanitize" but "we used string
formatting to build SQL queries instead of parameterized queries, because the ORM was
bypassed for this one ad-hoc query"]

**Fix:** [What specifically was changed — file, function, approach]

**Prevention:** [What would prevent this class of issue — rule added to Semgrep, linter
config, architecture constraint, test added, developer tutorial linked]

**Compliance controls addressed:** [e.g., PCI-DSS Req 6.3.3, NIST CSF PR.PS-04, SOC 2 CC6.8]
```

**If a Sigma detection rule is relevant:** also add the rule to `/docs/skills/` and reference it here.

---

## SLA Tracking

DefectDojo's SLA policy enforces deadlines. Check the "SLA Status" view weekly. Findings approaching SLA breach should be escalated in the daily Slack digest.

| Severity | SLA | Escalation if breached |
|---|---|---|
| Critical | 3 days | Immediate Slack alert + open TheHive case |
| High | 14 days | Daily Slack reminder at day 10 |
| Medium | 30 days | Weekly review |
| Low | 90 days | Quarterly batch review |

---

## Compliance Evidence

Every remediated finding contributes to compliance evidence. DefectDojo's monthly export (Findings Closed This Period + MTTR metrics) is a direct input to:

- **PCI-DSS Req 11.3** — quarterly scan results with remediation tracking
- **SOC 2 CC7.5** — evidence of consistent vuln identification and remediation
- **NIST CSF ID.RA-01 + RS.IM-01** — risk identification and improvement incorporation
- **HIPAA §164.308(a)(1)(ii)(D)** — information system activity review

Export from DefectDojo → save to `/docs/compliance/evidence/defectdojo/YYYY-MM.json` — this is the audit trail.

---

## Quick Reference Card

```
Finding appears in DefectDojo
        │
        ▼
Triage (24h SLA): confirm severity, tag CWE + compliance, set deadline
        │
        ▼
Learn: WebGoat lesson / Vulhub CVE demo / CIS Benchmark guidance
        │
        ▼
Remediate: fix root cause, add test, pass pre-commit hooks
        │
        ▼
Verify: rescan with same scanner, confirm finding gone
        │
        ▼
Close in DefectDojo with rescan note
        │
        ▼
Append to bug-log.md (Bug → Root cause → Fix → Prevention)
```
