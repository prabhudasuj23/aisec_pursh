# Cybersecurity Analyst — Responsibilities Deep Dive

> Personal study reference. Internal language. Full end-to-end workflows including edge cases, negotiations, and reporting chains.

---

## Table of Contents

1. [SAST + DAST Assessments](#1-sast--dast-assessments)
2. [CI/CD Pipeline Security](#2-cicd-pipeline-security)
3. [SCM Security](#3-scm-security)
4. [Integrating Security into SDLC](#4-integrating-security-into-sdlc)
5. [Regular Security Reviews & Audits](#5-regular-security-reviews--audits)
6. [Threat Intelligence & Policy Updates](#6-threat-intelligence--policy-updates)
7. [Training Development Teams](#7-training-development-teams)
8. [Documentation & Management Reporting](#8-documentation--management-reporting)

---

## 1. SAST + DAST Assessments

### What actually happens end-to-end

```
New PR opened
     │
     ▼
CI triggers SAST (Semgrep/SonarQube)
     │
     ├── No findings → green check → done
     │
     └── Findings present
              │
              ▼
         Analyst triages each finding
              │
              ├── Is it exploitable in THIS codebase context?
              │       ├── YES → severity confirmed → open ticket
              │       └── NO → mark False Positive → document why
              │
              ├── Does it block merge? (Critical/High SLA policy)
              │       ├── YES → notify dev lead + block merge gate
              │       └── NO → create tracking ticket, warn only
              │
              └── Remediation guidance written
                       │
                       ▼
                  Dev fixes + re-scans
                       │
                       ▼
                  Analyst verifies fix (not just CI green — manually check the diff)
                       │
                       ▼
                  Close ticket, update posture metrics
```

### SAST deep-dive workflow

**Tool runs on:** every PR, every commit to `main`, nightly full-repo scan.

**What you're actually looking for:**
- SQL injection sinks (raw string interpolation into query builders)
- Deserialization of untrusted input (pickle, yaml.load, eval)
- Hardcoded secrets in source (API keys, connection strings)
- Missing auth checks on sensitive routes
- Path traversal (user-controlled file paths without sanitization)
- XSS in template rendering

**Triage conversation with a dev (real exchange):**

> Dev: "Semgrep flagged line 47 but we never call that function from user input."
>
> You: "Walk me through the call chain from the API route to that function. If there's no external entry point, I'll mark it FP — but I need to see the call graph, not just your memory of it."

This is the critical discipline: **never accept verbal reassurance.** Make them show the code path.

**Edge cases that will burn you:**

| Scenario | Trap | Correct response |
|---|---|---|
| Dev says "it's already fixed in the next PR" | You close the ticket early | Never close until you see the fix in the *merged* commit |
| SAST fires on test code only | You mark it Critical | Test code can still leak to prod; investigate if `conftest.py` or fixtures are ever bundled |
| Third-party library owns the vulnerable line | You assign it to the dev team | It's an SCA issue (not SAST) — re-route to dependency scanner workflow |
| Finding is in dead code (never-called function) | You mark it FP | Dead code gets refactored back in 6 months — document the accepted risk with an expiry date |

### DAST deep-dive workflow

DAST runs **against a running application**, not source code. This means:

1. Target must be up (staging/QA environment, never prod directly unless with change control)
2. Auth must be scripted (ZAP auth scripts, Burp macros)
3. Crawler must be seeded with known URLs — auto-discovery misses 30–50% of modern SPA routes

**Full DAST run sequence:**

```
1. Confirm target URL is staging, not prod
2. Load auth script (Supabase JWT for Pursh → inject Bearer token into every request)
3. Configure scope: include pursh.staging.example.com/*, exclude /logout
4. Seed known routes manually (patient dashboard, doctor view, file upload)
5. Run baseline scan (5–10 min, just passive + active on known routes)
6. Ingest results
7. For each alert:
   a. Reproduce manually with curl or Burp to confirm it's real
   b. Check if it's a known WAF bypass or scanner false positive
   c. Assign severity based on CVSS + business impact (PHI exposure > CVSS score alone)
8. Write remediation card
9. Re-test after dev fix
```

**The re-test step is where most analysts fail.** They trust CI. You must:
- Replay the exact HTTP request that triggered the finding
- Confirm the response no longer contains the vulnerable indicator
- Check that the fix didn't just suppress the finding's symptom (e.g., adding a header to hide a stack trace doesn't fix the underlying error)

---

## 2. CI/CD Pipeline Security

### What you're actually defending

The pipeline is a **privileged code execution environment**. A compromised pipeline can:
- Exfiltrate secrets (AWS keys, NPM tokens, Supabase service role keys)
- Push malicious code to production without a PR
- Tamper with build artifacts (binary injection)
- Pivot to AWS account if OIDC roles are too broad

### Threat model for a GitHub Actions pipeline

```
Attack surface:
┌─────────────────────────────────────────────────────┐
│  1. Untrusted PR triggers workflow                  │  ← pull_request_target abuse
│  2. Third-party Action injected malware             │  ← supply chain (tj-actions/changed-files incident)
│  3. Secrets leaked via echo/env injection           │  ← add-mask bypasses
│  4. Self-hosted runner compromised                  │  ← persistent disk, no isolation
│  5. OIDC role too permissive                        │  ← full S3 write when only read needed
│  6. Artifact tampering between stages               │  ← no hash verification
└─────────────────────────────────────────────────────┘
```

### Your hardening checklist (what you implement, not just advise)

| Control | Why | How |
|---|---|---|
| Pin third-party Actions to full commit SHA | Tag `v3` can be silently overwritten by attacker | `uses: actions/checkout@8ade135a41bc4170...` |
| `GITHUB_TOKEN` minimal permissions | Default is read+write to repo | `permissions: contents: read` at workflow level |
| No `pull_request_target` on untrusted PRs | Runs with repo secrets in fork PR context | Use `pull_request` instead; use environment gates for secrets |
| Secret masking isn't enough — don't echo | `::add-mask::` only masks exact string | Never `echo $SECRET` even with masking; pass via env var |
| OIDC to AWS — no long-lived keys | Static keys can be stolen from secrets store | `aws-actions/configure-aws-credentials` with `role-to-assume` |
| Separate job for deployment | Build contamination isolated from deploy | Stage-separated jobs with artifact hash verification |
| `allow-unsecure-commands: false` | Older workflows can be injected via stdout | Explicit deny in workflow env |

### Edge case: a dev opens a PR that adds a new third-party Action

Your review checklist:
1. Is the Action pinned to SHA? If not, request change before merge.
2. What permissions does it request? If it reads `secrets.*`, what for?
3. Is the publisher verified (GitHub Marketplace verified badge)?
4. Does it have a recent commit with activity, or is it abandoned?
5. Run `grep -r "::set-env" .github/` — older Actions using deprecated commands are a vector.

---

## 3. SCM Security

### What "source code management security" actually covers

Most people think it's just "don't commit secrets." The real scope:

```
SCM Security
├── Identity & Access
│   ├── Who has write access to main?
│   ├── Are admin accounts using MFA?
│   └── Is SSO enforced for the org?
├── Branch Protection
│   ├── Force push blocked on main
│   ├── At least 1 approval + CODEOWNERS review
│   └── Status checks must pass (SAST, secret scan)
├── Secrets in Code
│   ├── Pre-commit (Gitleaks, detect-secrets)
│   ├── CI scan on every PR
│   └── Weekly historical scan (git log --all)
├── Supply Chain
│   ├── Dependabot alerts
│   ├── Pinned dependency versions
│   └── SBOM generation on every build
└── Audit Trail
    ├── Commit signing (GPG / SSH key)
    ├── GitHub audit log (org level)
    └── CODEOWNERS for sensitive paths
```

### Secrets scanning workflow when a leak is detected

This is a **full incident**, not just a ticket:

```
Gitleaks fires: found AWS_ACCESS_KEY_ID in commit abc123
          │
          ▼
Step 1: Confirm it's real (not a test/fixture key)
    - Try to call AWS STS GetCallerIdentity with the key
    - If valid → incident declared (P1)
    - If already expired/invalid → document + move on

Step 2: Revoke NOW (before anything else)
    - AWS IAM → delete access key
    - Don't wait for confirmation the key was used — assume it was

Step 3: Check CloudTrail (last 90 days)
    - Was the key used after the commit timestamp?
    - From what IP? AWS region? What API calls?
    - Cross-reference with known dev IPs

Step 4: Rotate all associated secrets
    - That key probably shared an IAM user — rotate all keys for that user
    - Check if same secret pattern exists in other repos (GitHub code search)

Step 5: Remove from git history
    - git filter-repo --invert-paths --path <file>
    - Force push (with approvals) after team coordination
    - GitHub support request to purge cached views

Step 6: Post-incident doc
    - How did it get committed? (no pre-commit hook, bypassed with --no-verify, etc.)
    - What access did the key have? Was least-privilege honored?
    - Prevention: add pre-commit + enforce via CI + block --no-verify in branch protection
```

---

## 4. Integrating Security into SDLC

### The friction points analysts actually face

Developers don't hate security. They hate **security that slows them down without explaining why.**

Your job is to be a translator: from "CVSS 9.8 RCE via deserialization" to "this means anyone on the internet can run arbitrary code on our server and exfiltrate all patient records."

### Shift-left integration map

```
Phase          What you do                           What dev sees
─────────────────────────────────────────────────────────────────
Design         Threat model review                   Async comment in architecture PR
               (STRIDE on new services)

Code           IDE Semgrep rules (VS Code ext)       Squiggly underline before commit
               Pre-commit hooks                      Local check before `git push`

PR             SAST + secret scan in CI              Inline PR comment on changed lines
               Reviewdog for inline annotations      "Possible SQL injection at line 47"

Build          SCA (Trivy/Grype) on deps             Build fails if Critical CVE in deps
               SBOM generation                       Artifact stored, not blocking

Staging        DAST (ZAP baseline)                   Test suite result + dashboard link

Pre-prod       Container scan (Trivy image)          Image rejected if Critical vuln
               IaC scan (Checkov)                    Terraform plan fails on misconfig

Production     Runtime (GuardDuty/WAF alerts)        Analyst monitors, not dev burden
               SIEM correlation
```

### When a dev pushes back on a finding

This will happen constantly. The protocol:

1. **Listen first.** They may actually be right that it's a FP.
2. **Ask for the exploit path.** "Show me how an attacker gets here."
3. **If they can't — that doesn't mean it's safe.** It means neither of you knows.
4. **Options you offer:**
   - Fix it (preferred)
   - Accept risk with documented justification + expiry date (90 days max for High)
   - Mark FP with evidence (not just assertion)
5. **Never negotiate severity down** to make the ticket go away. Severity is based on CVSS + business context, not developer comfort.

---

## 5. Regular Security Reviews & Audits

### What a quarterly security review actually looks like

**Week before:**
- Pull all findings from last 90 days (open, triaged, accepted-risk)
- Calculate: new findings vs closed, MTTR by severity, FP rate per scanner
- Identify any accepted-risk items approaching expiry

**During the review:**
- Walk through Critical + High open items — why are they still open?
- Review any accepted-risk justifications — do they still hold?
- Scanner health: are any scanners silently failing? (empty results file is a red flag, not a clean bill of health)
- OWASP coverage: are all 10 categories represented in your scanner stack?
- Compliance delta: any new HIPAA/GDPR requirements in the last quarter?

**Output:**
- Updated risk register
- Escalation list for leadership (what needs budget/headcount to fix)
- Closed accepted-risk items that expired
- Scanner tuning backlog (rules generating too many FPs need adjustment)

### Red flags in a "clean" audit

| What you see | What it might actually mean |
|---|---|
| Zero findings from SAST | Semgrep config is wrong, or scanning wrong directory |
| 100% findings closed in < 1 day | Devs are bulk-marking FP without investigation |
| No CRITICAL findings in 6 months | Good news, OR nobody is looking at critical services |
| Same findings re-opened repeatedly | Root cause not fixed — workaround applied each time |

---

## 6. Threat Intelligence & Policy Updates

### How threat intel actually flows into your work

You don't just "stay updated." You have a structured process:

```
Sources you monitor:
├── NVD (nvd.nist.gov) — CVE descriptions + CVSS scores
├── CISA KEV (Known Exploited Vulnerabilities catalog) — has it been exploited in the wild?
├── OSV.dev — open source specific, cross-ecosystem
├── GitHub Advisory Database — dependency-level
├── Twitter/X security researchers (follow specific people, not just hashtags)
└── Vendor bulletins (AWS, GitHub, Supabase, your stack vendors)

When something critical drops:
    1. Is any component in our stack affected?
       → grep sbom for package name
       → trivy scan with latest DB
    2. Is there a known exploit?
       → check KEV catalog
       → check Exploit-DB / PoC on GitHub
    3. Is it reachable from internet?
       → check the affected component's exposure
    4. Priority:
       → In KEV + internet-facing + our stack = P1, drop everything
       → In KEV + internal only = P2, fix in 24h
       → Not in KEV + CVSS >= 9 = P2 within 7 days
       → CVSS 7-9, not in KEV = P3, next sprint
```

### Policy update workflow

When you recommend a policy change (e.g., "we need to mandate signed commits"):

1. Write an ADR (Architecture Decision Record) — not just a Slack message
2. Include: current state, problem, options considered, recommended option, trade-offs
3. Get sign-off from: your manager + affected team leads
4. Update the policy doc, update CLAUDE.md or equivalent, update enforcement (branch protection rule, CI check)
5. Communicate the change with a migration window — never flip a policy that breaks existing workflows without a heads-up period

---

## 7. Training Development Teams

### What actually works (not death-by-slideshow)

**Most effective formats:**
- **PR comment links** — "This is a SQL injection risk. Here's a 3-minute read on why and how to fix it." Link to your own `/docs/secure-coding/` tutorial.
- **15-minute "show and tell"** — take a real finding from your codebase, explain the exploit, show the fix. Not a generic OWASP slide.
- **Pair on the fix** — sitting with the dev for 20 minutes to fix a SAST finding teaches more than any training doc.
- **Security champions** — identify 1 dev per team who is genuinely interested. Train them deeply. They become your eyes and ears in sprint planning.

### When you get "security theater" pushback

> Dev lead: "We've been shipping for 2 years without any breaches. These SAST findings are slowing us down."

Your response (internal framing):
- You don't argue about the absence of breaches — absence of evidence is not evidence of absence.
- You anchor on **business risk language**: "A SQL injection in the patient search endpoint means any user can read any other patient's records. That's a HIPAA breach. The notification cost alone is $100–$1000 per affected record."
- You offer a **tiered enforcement** compromise: Critical blocks merge (non-negotiable), High must be triaged within 5 days but doesn't block, Medium/Low are tracked but not gating.

---

## 8. Documentation & Management Reporting

### Two audiences, two documents

| Document | Audience | What they care about |
|---|---|---|
| Technical finding report | Dev team, Security engineer | CWE, file/line, reproduction steps, exact fix |
| Executive security posture report | CISO, VP Engineering | Risk trend (getting better or worse?), compliance status, cost of remaining risk |

### Posture report structure (monthly, 1 page)

```
SECURITY POSTURE — [MONTH YEAR]
═══════════════════════════════

Critical open findings:     3  (↑2 from last month)  ← RED flag, explain why
High open findings:        12  (↓5 from last month)
MTTR Critical (this month): 4.2 days  (target: <7)   ← meeting SLA
MTTR High (this month):    18.6 days  (target: <30)   ← meeting SLA

Scanner coverage:
  SAST:     ✓  (97% of PRs scanned)
  DAST:     ✓  (weekly full scan running)
  SCA:      ✓  (0 critical deps unpatched)
  Secrets:  ✓  (0 active leaks)
  IaC:      ⚠  (Checkov failing on 2 TF modules — investigating)

Compliance:
  HIPAA coverage:   82%  (↑3%)
  GDPR coverage:    79%  (stable)
  OWASP Top 10:     100% scanner coverage

Top 3 risks requiring attention:
  1. [Risk description] — recommended action — owner — deadline
  2. ...
  3. ...
```

### Why this matters beyond "covering yourself"

The posture report is your **budget justification instrument**. When you say "IaC scanning is failing on 2 modules" in a monthly report and it goes unfixed for 3 months, you've created a paper trail that protects you professionally and gives leadership the data to prioritize headcount or tooling investment.

Security without documentation is just noise. Documentation turns it into institutional memory.
