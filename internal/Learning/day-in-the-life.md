# Day in the Life — Cybersecurity Analyst (AppSec Focus)

> Real workflow cadence. What you actually do hour by hour. Two scenarios: normal sprint day and incident day.

---

## Normal Sprint Day (Monday)

### 8:30 AM — Morning triage

Before touching anything else, you check what happened overnight.

```
Morning triage checklist:
├── GitHub: any new SAST/DAST/SCA alerts on open PRs?
├── Supabase / AISec dashboard: any failed scans? (empty result = silent failure)
├── Email: any Dependabot alerts? Any new GitHub Security Advisory for your stack?
├── CISA KEV (bookmark it): any new Known Exploited Vulns published yesterday?
└── Slack #security-alerts: anything from overnight automated scans
```

**Time: ~20 minutes.** If you find a CISA KEV hit on a package you use, everything else pauses — that becomes the day.

### 9:00 AM — Sprint standup

What you say:
- "Triaged 4 findings from Friday's ZAP scan. 1 confirmed High (broken auth on /api/doctor endpoint), sent to [dev lead]. 3 are FPs — documenting."
- "Blocked on the Checkov IaC scan — Terraform module is throwing a false positive on CKV_AWS_18. Working on an inline suppression with justification."

What you don't say:
- Scanner names and CVE IDs that mean nothing to product managers
- "We found a CWE-89" — say "SQL injection risk in the patient search feature"

### 9:15 AM — Finding triage block (60-90 min)

The largest block of your day. Every finding that came in needs a decision:

```
For each finding in queue:

1. Read the finding: what scanner, what rule, what file/line/endpoint?

2. Reproduce it (or attempt to):
   ├── SAST: read the code path — is there an external entry point?
   ├── DAST: replay the HTTP request that triggered it
   └── SCA: check if the vulnerable code path is in our call graph

3. Decision tree:
   ├── Exploitable → assign severity, create ticket, notify owner
   ├── FP → document WHY it's FP, suppress rule at line level (not globally)
   ├── Won't fix (accepted risk) → justify, set expiry date, get sign-off
   └── Need more info → ask dev who owns that module

4. Write the triage note — at minimum:
   "Reviewed 2024-01-15. Exploitable: [yes/no]. Reasoning: [one sentence].
    Action: [fix by Sprint 42 / accepted risk expires 2024-04-15 / FP: reason]"
```

**Do not skip writing the note.** In 6 months when a finding re-opens, you need to know why you closed it. And auditors will ask.

### 11:00 AM — PR security reviews

You review PRs that touch sensitive paths (CODEOWNERS routes you):
- Any changes to authentication logic
- Any changes to query builders, raw SQL
- Any new third-party dependencies
- Any changes to IAM roles or Terraform

**PR review checklist:**
```markdown
- [ ] Are new dependencies pinned? Any known CVEs in new deps?
- [ ] Is user input sanitized before it reaches any sink (DB, file system, subprocess)?
- [ ] Are secrets referenced via env vars / Secrets Manager, not hardcoded?
- [ ] Does this change affect any HIPAA-controlled paths (patient data, audit log)?
- [ ] If auth changed: does it still enforce MFA? Does session expiry still work?
- [ ] If IaC changed: are encryption settings preserved? Logging enabled?
```

### 1:00 PM — Finding remediation support

Devs working on security tickets come to you. Your job is:
1. **Explain the attack scenario** — not just "parameterize your query" but "here's what an attacker does with the current code"
2. **Show the fix** — code example in the actual language/framework they're using
3. **Verify the fix** — you run the scanner again yourself, not just trust CI

### 2:00 PM — Documentation + metrics

Not glamorous. But this is what builds your program's credibility:
- Close verified fixed tickets with remediation notes
- Update MTTR metrics (did we fix this within SLA?)
- Update the posture dashboard
- If anything new was learned (new FP pattern, new scanner behavior), update the relevant skill file

### 3:30 PM — Tooling / scanner tuning

Ongoing work. If Semgrep is generating 40% FPs on a specific rule, that rule is worse than useless — it trains devs to ignore SAST alerts.

```
Scanner tuning workflow:
├── Pull last 30 days of findings for a scanner
├── Calculate FP rate per rule
├── Any rule with FP rate > 25%:
│   ├── Is it a real vulnerability class that our code handles safely?
│   │   └── YES: add a narrow suppression with a comment explaining why
│   └── Is the rule pattern just too broad?
│       └── YES: tune the rule config, or replace with a tighter custom rule
└── Document changes in /docs/skills/<scanner>.md
```

### 4:30 PM — Async communication

- Reply to developer questions in security channels
- Write up any decisions that were made verbally (Slack threads disappear; ADRs don't)
- Check if any accepted-risk items are approaching their expiry dates

---

## Incident Day (Wednesday — leaked secret discovered)

### 10:17 AM — Alert fires

Gitleaks CI check fails on PR #234. Finding: `AKIA...` (AWS access key pattern) in a test fixture file.

### 10:18 AM — Immediate triage (do not wait)

```bash
# Is this a real key or a fake one in a test?
aws sts get-caller-identity --access-key-id AKIA...

# If response shows an account → real key, incident declared
# If AccessDenied or InvalidClientTokenId → key is already revoked or fake
```

**If real:** declare incident NOW. Do not finish your coffee first.

### 10:22 AM — Incident declared

Notify:
1. Your direct manager (immediate, Slack + call)
2. AWS account owner
3. Affected team lead (who owns the repo/file)

**You own the technical response. Your manager owns the communication chain upward.**

### 10:25 AM — Contain: revoke the key

```bash
# In AWS IAM console or CLI:
aws iam delete-access-key --access-key-id AKIA... --user-name <iam-user>
# Do not deactivate. Delete. Deactivated keys can be reactivated.
```

**Do this before forensics. Revoking stops bleeding. You do forensics on the body, not the living patient.**

### 10:30 AM — Forensics: was the key used?

```bash
# CloudTrail: all API calls with this key, last 90 days
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA... \
  --start-time 2024-01-01 \
  --max-results 50
```

Look for:
- API calls from unexpected IPs or regions
- Calls to exfiltration-relevant services: `s3:GetObject`, `secretsmanager:GetSecretValue`, `iam:CreateUser`
- High volume of calls in a short window (scripted enumeration)
- Anything that ran AFTER the commit timestamp (proves the key was discovered and used)

### 11:00 AM — Scope assessment

Questions to answer:
```
1. What did this key have access to?
   → aws iam list-attached-user-policies --user-name <user>
   → aws iam simulate-principal-policy (what could they actually do?)

2. Was the key in git history only, or also in any deployed config files?
   → git log --all -- <filename>

3. Is the same key pattern in any other repos?
   → GitHub org-level code search

4. Are there other keys for this same IAM user that might also be compromised?
   → Rotate all credentials for the user, not just the found key
```

### 12:00 PM — Remediation: scrub history

```bash
# git-filter-repo (preferred over BFG)
git filter-repo --invert-paths --path path/to/fixture.py

# If the secret is inline in a Python file (not just the file):
git filter-repo --replace-text <(echo 'AKIA...==>REDACTED_AWS_KEY')

# Force push (requires coordination — other devs must re-clone or rebase)
git push origin --force --all
```

**Also file a GitHub Support request** to purge the key from GitHub's cached views — your force push removes it from the repo, but GitHub's "search code" index may still have it cached.

### 1:00 PM — Add controls to prevent recurrence

1. Add `gitleaks` pre-commit hook if not present
2. Add the key pattern to `.gitleaks.toml` `allowlist` with a `regexes` match that covers test file patterns (so future test fixtures with `AKIA` format are caught explicitly)
3. Review why `--no-verify` bypass was possible — was it? If so, add CI enforcement as second line of defense

### 3:00 PM — Post-incident document

Within 24 hours, regardless of incident severity:

```markdown
# Post-Incident: Leaked AWS Key — 2024-01-17

## Timeline
- 10:17 AM: Gitleaks alert fired on PR #234
- 10:22 AM: Incident declared, manager notified
- 10:25 AM: Key revoked in AWS IAM
- 10:30 AM: CloudTrail forensics initiated
- 11:00 AM: No evidence of unauthorized use confirmed
- 12:00 PM: Git history scrubbed
- 3:00 PM: Post-incident documentation

## Root Cause
Test fixture file contained a real AWS key from a developer's local environment.
Pre-commit hooks were not installed on the developer's machine.

## Impact
No unauthorized access detected. Key was valid for 6 hours 8 minutes before revocation.

## Remediation
- Key revoked [10:25 AM]
- Git history scrubbed and force-pushed [12:00 PM]
- GitHub cache purge requested [12:15 PM]
- Pre-commit hooks mandatory onboarding step added to dev setup guide

## Prevention
1. CI Gitleaks scan now runs as a required status check (was optional)
2. Developer onboarding checklist updated to include pre-commit hook installation
3. All IAM users audited for key age > 90 days — 3 found, rotated
```

**This document is your evidence trail for auditors** and your reference for the next incident.

---

## Time allocation across a typical week

```
Monday–Friday breakdown (approximate):
┌──────────────────────────────────────────────────────┐
│ Finding triage + remediation support    │ 35%        │
│ PR security reviews                     │ 20%        │
│ Documentation + reporting               │ 15%        │
│ Scanner tuning + tooling                │ 15%        │
│ Meetings (standup, sync, reviews)       │ 10%        │
│ Threat intel reading + policy work      │  5%        │
└──────────────────────────────────────────────────────┘

On incident days: triage + remediation swells to 70–80% of the day.
Everything else waits.
```
