# Cybersecurity Analyst — Skills Deep Dive

> Two sections per skill: **How it works internally** + **Why the business cares**. Personal study reference.

---

## Table of Contents

1. [SAST — Static Application Security Testing](#1-sast)
2. [DAST — Dynamic Application Security Testing](#2-dast)
3. [CI/CD Pipeline Security](#3-cicd-pipeline-security)
4. [SCM Security](#4-scm-security)
5. [Vulnerability Analysis & Remediation](#5-vulnerability-analysis--remediation)
6. [Stakeholder Communication](#6-stakeholder-communication)

---

## 1. SAST

### How it works internally

SAST is **code analysis without execution**. The tool reads source code and builds an internal representation to reason about it.

#### Three analysis techniques (most tools use all three):

**1. Pattern matching (grep on steroids)**
- Looks for known-bad code patterns: `eval(`, `os.system(`, `md5(`, `pickle.loads(`
- Fast, low FP for obvious patterns
- Misses context: `eval(CONSTANT_STRING)` is safe; `eval(user_input)` is not — pattern matching can't always distinguish

**2. AST (Abstract Syntax Tree) analysis**
```
Source code:
    user_input = request.args.get('name')
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    db.execute(query)

AST representation:
    Assignment(target=user_input, value=HTTPRequest.args.get)
    Assignment(target=query, value=f-string(template, user_input))
    Call(db.execute, args=[query])

SAST sees:
    - user_input originates from HTTP request (taint source)
    - query incorporates user_input via string formatting
    - db.execute receives query (taint sink)
    - No sanitization between source and sink → SQL injection
```

**3. Data flow / taint analysis**
- Tracks "tainted" data from sources (HTTP input, env vars, file reads) to sinks (DB queries, eval, subprocess, file writes)
- The most powerful technique — catches multi-hop injections across function calls
- Most expensive computationally — why full taint analysis takes 10–30 min on large repos

#### Why false positives happen

| Root cause | Example |
|---|---|
| Tool can't see runtime config | Framework auto-escapes SQL — SAST doesn't know |
| Dead code | Vulnerable function exists but is never called |
| Sanitization in an unconventional place | Custom validator not in the tool's sanitizer list |
| Third-party library wraps the sink | ORM prevents injection but SAST sees raw DB call |

#### Semgrep specifically

Semgrep uses **pattern + metavariable matching**, not full AST:
```yaml
# This rule finds SQL injection in Python
rules:
  - id: sql-injection
    pattern: |
      $QUERY = "..." + $USER_INPUT
      $DB.execute($QUERY)
    message: "Possible SQL injection"
    severity: ERROR
```
The `$VAR` syntax captures any expression — this is what makes Semgrep rules readable and customizable without a PhD in compiler theory.

### Why the business cares

**Risk without SAST:** A vulnerability in the codebase for months before anyone finds it. By then, it's in 12 versions of the app, maybe already in prod, maybe already exploited.

**Business translation:**
- SAST catches issues **before they reach production** — the cheapest time to fix a bug is during code review (IBM estimates fixing in code review costs 6x less than fixing post-release)
- Compliance evidence: PCI DSS, HIPAA, SOC 2 auditors ask "do you scan your code?" SAST reports are the evidence
- HIPAA §164.312(b) requires audit controls and activity review — SAST findings feed into that evidence trail
- For a client: "We scan 100% of code changes before they're merged. Here's the findings dashboard from the last 30 days showing what we caught and fixed."

---

## 2. DAST

### How it works internally

DAST sends **real HTTP requests to a running application** and observes the responses.

#### How ZAP works under the hood

```
ZAP architecture:
┌─────────────────────────────────────────────────────┐
│  ZAP Proxy (sits between browser/scanner and app)   │
│                                                     │
│  1. Spider (crawler): discovers all pages/endpoints │
│     - Traditional spider: follows <a href> links    │
│     - AJAX spider: executes JS, captures XHR calls  │
│                                                     │
│  2. Passive scan: inspects all traffic              │
│     - No modification — just observes               │
│     - Finds: missing headers, info disclosure,      │
│       cookie flags, HTTPS issues                    │
│                                                     │
│  3. Active scan: attacks each parameter             │
│     - Inserts payloads into every input             │
│     - SQL injection: ' OR 1=1 --                    │
│     - XSS: <script>alert(1)</script>                │
│     - Path traversal: ../../etc/passwd              │
│     - Watches response for indicators of success    │
└─────────────────────────────────────────────────────┘
```

#### Why authenticated DAST is hard

Most enterprise apps require login. DAST must:
1. Get a valid session (JWT, cookie, OAuth token)
2. Include that session in every scan request
3. Detect when the session expires and re-authenticate
4. Scope the scan to avoid logging out (which would invalidate the session)

In ZAP, you write an authentication script:
```python
def authenticate(helper, paramsValues, credentials):
    # Called by ZAP to get a fresh session
    loginUrl = paramsValues.get("loginUrl")
    loginData = "email=" + credentials.getParam("username") + \
                "&password=" + credentials.getParam("password")
    msg = helper.prepareMessage()
    msg.setRequestBody(loginData)
    helper.sendAndReceive(msg)
    # Extract and return the auth token
```

#### DAST blind spots

| What DAST misses | Why |
|---|---|
| Logic flaws | DAST doesn't understand business logic — it won't know that a doctor shouldn't see another doctor's patients |
| Stored XSS in admin panels | If admin is out of scope, injection stored via user never gets triggered |
| Race conditions | HTTP scanner is sequential — doesn't test concurrent requests |
| Second-order SQL injection | Payload stored in DB, triggered on next read — scanner doesn't connect the two |
| Issues in thick clients | DAST only talks HTTP — desktop apps, mobile binaries, WebSocket-heavy SPAs need custom setup |

### Why the business cares

SAST proves the code looks safe. DAST proves the **running app is safe**. They're complementary.

**Client pitch:** "We run ZAP against your staging environment weekly. Unlike SAST which reads code, this actually tries to break into the running application — the same way a real attacker would. We caught a broken authentication issue last quarter that the code scan missed because the vulnerability was in the session management configuration, not the code itself."

**Compliance angle:** OWASP ASVS Level 2 requires "dynamic analysis testing at regular intervals." SOC 2 Type 2 wants evidence of regular penetration testing — DAST reports are admissible evidence. PCI DSS Requirement 6.6 requires web application protection via scanning or WAF.

---

## 3. CI/CD Pipeline Security

### How it works internally

The pipeline is code. It runs with elevated privileges. Securing it requires treating it with the same scrutiny as application code.

#### GitHub Actions execution model

```
When a workflow triggers:
  1. GitHub provisions a runner VM (ephemeral — fresh OS each time)
  2. Workflow file is read from .github/workflows/
  3. Each job runs in a new container/VM
  4. Secrets are injected as environment variables at runtime
  5. GITHUB_TOKEN is auto-generated per run with scoped permissions
  6. OIDC: runner calls GitHub token endpoint → gets short-lived OIDC token
          → presents to AWS → AWS validates via GitHub's JWKS endpoint
          → issues temporary AWS credentials (15min–1hr)
  7. Job completes → runner VM is destroyed → all credentials gone
```

#### How secrets leak in pipelines

**1. Log injection:**
```yaml
# Bad: user-controlled input in step name
- name: "Deploy to ${{ github.event.inputs.environment }}"
```
If an attacker controls `environment` value, they can inject `$(env)` to dump all env vars to logs.

**2. `pull_request_target` abuse:**
```yaml
on: pull_request_target  # ← runs with SECRETS from base repo, not fork
```
A malicious fork PR triggers this workflow with access to your secrets. Classic supply-chain vector.

**3. Action supply chain:**
```yaml
uses: some-action/upload@v2  # ← what if v2 tag is moved to a malicious commit?
```
Fix: `uses: some-action/upload@a1b2c3d4e5f6...` (full SHA, immutable)

#### SLSA levels (supply chain maturity)

| Level | What it means | How you get there |
|---|---|---|
| 1 | Build process documented | Any CI/CD |
| 2 | Build is tamper-resistant | Hosted runner + provenance |
| 3 | Build environment is isolated, auditable | Ephemeral runners + attestations |
| 4 | Two-party review of all changes | Branch protection + signed commits + code review |

### Why the business cares

The pipeline has the keys to the kingdom: AWS credentials, deployment tokens, secrets to every downstream system.

**The SolarWinds model (scaled down):** Attackers compromised the build pipeline, not the application code. Every customer who downloaded a legitimate, signed update got malware. Your pipeline security determines whether you can be used as a supply-chain attack vector against your own customers.

**Client language:** "If your pipeline is compromised, an attacker doesn't need to find a vulnerability in your app — they just push code directly to production. We enforce: every Action is pinned to a specific commit hash, no long-lived AWS credentials in CI, OIDC ephemeral credentials only, and all pipeline changes require security team review via CODEOWNERS."

---

## 4. SCM Security

### How it works internally

Source code management security is **identity + access control on the most sensitive asset in the company: the code itself.**

#### Git's security model

Git is not a security boundary. By default:
- Anyone with read access can clone the entire history, including deleted branches
- Commits are only as trustworthy as the person who made them — no verification
- Tags can be moved silently (unless annotated + signed)
- Force push rewrites history — no record unless you're watching the GitHub event log

#### What branch protection actually enforces

```
main branch protection stack:
├── require_pull_request_reviews
│   ├── required_approving_review_count: 1
│   ├── require_code_owner_reviews: true    ← CODEOWNERS file enforced here
│   └── dismiss_stale_reviews: true         ← new commit invalidates old approval
├── required_status_checks
│   ├── strict: true                        ← must be up-to-date with base
│   └── contexts: [semgrep, trivy, gitleaks, build]
├── enforce_admins: true                    ← even repo admins can't bypass
├── required_linear_history: true           ← no merge commits on main
├── allow_force_pushes: false
└── allow_deletions: false
```

#### Signed commits — what they actually prove

```
Unsigned commit:
  Author: prabhudasuj23 <any@email.com>   ← anyone can set this
  Commit: abc123

Signed commit:
  Author: prabhudasuj23 <real@email.com>
  GPG/SSH signature: verified by GitHub
  ← GitHub checked the signature against the key registered to prabhudasuj23's account
  ← Proves: this commit was made by someone with physical access to that signing key
```

What it does NOT prove: the code is correct or safe. It proves authorship and non-repudiation.

#### Gitleaks — how secret detection works

Gitleaks uses regex patterns for known secret formats:
```toml
[[rules]]
id = "aws-access-key"
description = "AWS Access Key"
regex = '''(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'''
```

It scans:
- Every commit's diff (CI mode)
- Every file in the working tree (pre-commit mode)
- Full git history (audit mode: `git log --all`)

**The critical gap:** Gitleaks on PR doesn't catch secrets committed to a branch 6 months ago. You need the weekly historical scan.

### Why the business cares

**One leaked secret = one breach vector.** The 2022 CircleCI breach started with a compromised employee laptop that had access to production secrets. The attacker stole secrets from customer CI pipelines.

**Client conversation:** "We enforce signed commits on main so every change is non-repudiation auditable — you can prove in a legal context who committed what. We run automated secret scanning on every PR and weekly across the full git history. We have CODEOWNERS so any change to authentication code, Terraform, or compliance mappings requires a security team member's approval."

---

## 5. Vulnerability Analysis & Remediation

### How it works internally

Not all vulnerabilities are equal. Effective analysis requires **two scoring inputs**:

#### CVSS (technical severity)

```
CVSS v3.1 base score factors:
├── Attack Vector:    Network(0.85) | Adjacent(0.62) | Local(0.55) | Physical(0.2)
├── Attack Complexity: Low(0.77) | High(0.44)
├── Privileges Required: None(0.85) | Low(0.62) | High(0.27)
├── User Interaction: None(0.85) | Required(0.62)
├── Scope: Unchanged | Changed
├── Confidentiality Impact: None | Low | High
├── Integrity Impact: None | Low | High
└── Availability Impact: None | Low | High

Score = BaseScore formula → 0.0–10.0
Critical: 9.0–10.0
High:     7.0–8.9
Medium:   4.0–6.9
Low:      0.1–3.9
```

#### Business context adjustments

CVSS is a starting point, not the final word.

| Scenario | CVSS says | Business context says | You do |
|---|---|---|---|
| Critical RCE in an internal tool with no internet access | Critical 9.8 | Low business impact (only 3 internal devs have access, no PHI) | Document as Critical, accept risk with compensating controls |
| Medium path traversal in file upload that serves PHI | Medium 5.0 | HIGH business impact (PHI exposure = HIPAA breach) | Escalate to High, expedited fix |
| Critical in a library we use but in a code path we don't call | Critical 9.3 | No exposure | Mark FP-adjacent: "not reachable in our usage" — still track it |

#### Remediation card structure

Every finding you close should have a remediation record:
```markdown
## Finding: SQL Injection in patient search

**CWE:** CWE-89
**OWASP:** A03:2021 — Injection
**Scanner:** Semgrep, Rule ID: python.django.security.injection.raw-query

**Vulnerable code:**
```python
query = f"SELECT * FROM patients WHERE name = '{search_term}'"
```

**Why it's vulnerable:**
User-controlled input `search_term` is concatenated directly into the SQL query.
An attacker can submit `'; DROP TABLE patients; --` to destroy data,
or `' OR '1'='1` to return all patient records regardless of access control.

**Fix:**
```python
# Use parameterized queries — the DB driver handles escaping
patients = Patient.objects.filter(name=search_term)  # ORM
# or raw SQL with parameters:
cursor.execute("SELECT * FROM patients WHERE name = %s", [search_term])
```

**Verification:** Confirmed fix merged in PR #142. Re-ran Semgrep — no finding.
Manually tested with `' OR 1=1 --` payload — returns 0 results (correct).
```

### Why the business cares

**The business doesn't pay for vulnerabilities found. It pays to reduce risk.**

A finding that sits open for 180 days is the analyst's failure, not just the developer's. Your job includes tracking, escalating, and making the fix path as frictionless as possible.

**SLA framework to propose to clients:**

| Severity | Time to triage | Time to remediate | Escalation path |
|---|---|---|---|
| Critical | 4 hours | 7 days | CISO + VP Eng immediately |
| High | 24 hours | 30 days | Security lead + team lead |
| Medium | 5 days | 90 days | Security lead |
| Low | 30 days | Next quarter | Dev team backlog |

---

## 6. Stakeholder Communication

### How it works internally

AppSec requires communicating the same technical reality to three very different audiences simultaneously.

#### The translation matrix

| Technical fact | For the developer | For the manager | For the CISO/client |
|---|---|---|---|
| SQL injection, CVSS 9.8, in patient search | "Line 47 of search.py: parameterize the query. Here's the ORM call that fixes it." | "A security flaw in the patient search feature. Dev team is fixing it this sprint. No evidence of exploitation." | "A critical vulnerability in our PHI-adjacent search feature was identified and is being remediated within our 7-day SLA. No breach detected." |
| Leaked API key in git history | "Key was committed in commit abc123. Revoke it now in AWS IAM, then we'll scrub history." | "A credential was accidentally committed to the codebase. It's been revoked. We're cleaning history and adding controls to prevent recurrence." | "A credential was exposed in version control. Immediate revocation completed. Forensic analysis confirmed no unauthorized use. Root cause addressed via mandatory pre-commit scanning." |
| 3 critical findings open > 30 days | "These need to be prioritized. What's the blocker?" | "We have 3 overdue critical findings. Can we get a sprint dedicated to security debt?" | "3 critical findings have exceeded SLA. I'm requesting executive escalation to allocate remediation capacity." |

#### The non-technical stakeholder reality

CISOs and business leaders respond to:
- **Financial risk:** "HIPAA breach penalties: $100–$50,000 per violation, up to $1.9M per violation category per year."
- **Reputation risk:** "A breach in patient data would trigger mandatory breach notification to affected patients — public disclosure."
- **Competitive risk:** "SOC 2 Type 2 certification — clients are asking for it. Our DAST program is one of the checkboxes."
- **Trend, not snapshot:** "We're down from 12 critical open findings last quarter to 3. The program is working."

Security professionals who only speak in CVEs and CWEs get ignored. The ones who translate to business risk get budget.
