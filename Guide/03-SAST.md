# Chapter 3: SAST — Static Application Security Testing

> **Goal:** Understand how SAST works, what it finds, which tools enterprises use, and how to integrate and tune SAST in CI/CD pipelines. SAST is a core "shift-left" control — finding vulnerabilities in code before the application is ever deployed.

---

## 3.1 What Is SAST?

**Static Application Security Testing (SAST)** analyzes source code (or compiled bytecode) for security vulnerabilities **without running the application**.

Think of it like spell-check, but for security bugs. It reads your code and says: "On line 42, you are passing user input directly into a SQL query — that is a SQL injection vulnerability."

**The key word is "static"** — the code is not executed. The tool reads it like a reviewer would.

### What SAST Can Find

- SQL injection, command injection, LDAP injection
- Cross-site scripting (XSS)
- Path traversal
- Hardcoded secrets and passwords
- Weak cryptographic algorithms (MD5, SHA1 for passwords)
- Insecure random number generation
- Insecure deserialization
- Improper exception handling
- Security misconfigurations in code
- XML External Entity (XXE) vulnerabilities

### What SAST Cannot Find

- Authentication flaws that depend on runtime state
- Authorization bypasses that depend on complex business logic
- Configuration issues (misconfigurations are in config files, not code)
- Race conditions (need runtime observation)
- Business logic flaws

This is why SAST is used alongside DAST, not instead of it.

---

## 3.2 How SAST Works

### Approach 1: Pattern Matching (Regex-based)

The simplest approach — look for known-bad patterns:

```python
# Rule: flag any string concatenation into SQL
pattern: "execute(" + user_input
```

Fast and low false-negatives, but also high false-positives (flags safe code that looks like the pattern).

### Approach 2: Abstract Syntax Tree (AST) Analysis

The tool parses the code into a tree structure representing its syntax. Rules match against the tree, not raw text.

```python
# Source code
result = db.execute("SELECT * FROM users WHERE id=" + user_id)

# AST representation (simplified)
BinaryOp(
  left=StringLiteral("SELECT * FROM users WHERE id="),
  op="+",
  right=Identifier("user_id")
)
→ Passed to db.execute()
→ FLAGGED: string concatenation into SQL call
```

AST analysis is more accurate — it understands code structure, not just text.

### Approach 3: Taint Analysis (Data Flow)

The most powerful approach. The tool tracks how user-controlled data ("tainted" data) flows through the code from **sources** to **sinks**.

- **Source:** Where tainted data enters (HTTP request, form field, URL parameter)
- **Sink:** Where tainted data would cause harm (SQL query, OS command, HTML output)
- **Sanitizer:** Where tainted data is cleaned (parameterized query, HTML encode)

```
Source: request.args.get("id")        → tainted
          ↓ (no sanitization)
Sink:   db.execute("SELECT ... WHERE id=" + id)  → SQL Injection!
```

```
Source: request.args.get("id")        → tainted
          ↓
Sanitizer: int(id)                    → validates it is an integer
          ↓
Query:  db.execute("SELECT ... WHERE id=" + str(id)) → SAFE (integer cannot inject SQL)
```

Taint analysis produces fewer false positives because it only flags cases where tainted data actually reaches a dangerous sink.

---

## 3.3 SAST in the Enterprise CI/CD Pipeline

SAST fits into the **PR/merge request phase** of CI/CD:

```
Developer pushes branch
        ↓
Pull Request opened
        ↓
CI pipeline starts automatically
   ├── Unit tests
   ├── SAST scan (Semgrep/SonarQube)    ← happens here
   ├── SCA scan (Trivy)
   └── Linting
        ↓
Results posted as PR comments (inline on the vulnerable line)
        ↓
Critical/High findings block merge until resolved
```

### Two SAST Approaches in CI

**1. Full scan on every commit (for small repos)**
- Scans the entire codebase
- More thorough
- Slower for large repos (can take 10–30 minutes)

**2. Incremental scan (diff-only)**
- Only scans files changed in the PR
- Much faster (seconds to a few minutes)
- Can miss inter-file vulnerabilities (data flow across files)

Enterprise standard: **incremental for PRs, full scan nightly on main**.

---

## 3.4 Enterprise SAST Tools

### Semgrep (Open Source — Recommended for most teams)

**What it is:** A fast, flexible SAST tool that uses pattern-matching rules written in YAML. Used by many top tech companies.

**Why enterprises like it:**
- Runs in seconds (not minutes)
- Rules are human-readable YAML — security engineers can write custom rules
- Large rule library: `semgrep.dev/r` has thousands of community and official rules
- Native CI integration — runs as a GitHub Action, GitLab job, etc.
- SARIF output (standard format for security findings)

**Example Semgrep rule — detecting SQL injection in Python:**
```yaml
rules:
  - id: python-sqli-format-string
    pattern: |
      $DB.execute("..." + $USER_INPUT)
    message: "Potential SQL injection: string concatenation in execute()"
    languages: [python]
    severity: ERROR
    metadata:
      cwe: CWE-89
      owasp: A03:2021
```

**Running Semgrep in GitHub Actions:**
```yaml
- name: Run Semgrep SAST
  uses: returntocorp/semgrep-action@v1
  with:
    config: >-
      p/owasp-top-ten
      p/python
      p/secrets
```

### SonarQube (Commercial + Community Edition)

**What it is:** A comprehensive code quality and security platform. Analyzes code quality, security, and maintainability.

**Why enterprises use it:**
- Deep language support (30+ languages)
- Quality Gate concept: define pass/fail criteria for security and quality metrics
- Security hotspots for issues that require human review
- Integrates with Jira for ticket creation
- Compliance-ready reports (OWASP, CWE, SANS Top 25)

**SonarQube Quality Gate example:**
```
Quality Gate: FAIL if:
- Any new blocker/critical security issues
- Code coverage drops below 80%
- Duplicated lines exceed 3%
```

### Checkmarx (Commercial)

**What it is:** Enterprise SAST tool with deep taint analysis across many languages. Popular in finance and healthcare.

**Why enterprises pay for it:**
- Cross-file taint analysis (tracks data flow across multiple files)
- Compliance mapping (PCI-DSS, HIPAA, SOC 2)
- Detailed audit reports
- Integrates with Jira, ServiceNow
- Training content for developers on each finding type

### Veracode (Commercial)

**What it is:** Cloud-based SAST/SCA/DAST platform. Submits code to Veracode's cloud for analysis.

**Why enterprises use it:**
- No infrastructure to manage (cloud-based)
- Very comprehensive binary analysis (finds issues in compiled code even without source)
- Strong compliance reporting
- Policy-based gating

### Fortify (Commercial)

**What it is:** HP/Micro Focus enterprise SAST. Very deep analysis but slower than Semgrep.

---

## 3.5 Reading and Triaging SAST Reports

A raw SAST report from a large codebase can have thousands of findings. 80% may be false positives. Your job is to separate signal from noise.

### Triage Framework

**Step 1: Filter by severity**
Start with Critical and High. Ignore Info-level findings until higher-severity findings are handled.

**Step 2: Check exploitability**
Not every SAST finding is actually exploitable. Check:
- Is the tainted data actually user-controlled?
- Is there a sanitizer downstream that the tool missed?
- Is this code even reachable in production?

**Step 3: Check asset criticality**
A SQL injection in an internal admin tool used by 2 people is lower risk than the same bug in a customer-facing API handling millions of requests.

**Step 4: Determine true positive vs false positive**

| Category | Definition | Action |
|---|---|---|
| True Positive | Real vulnerability | Fix it; document in tracking system |
| False Positive | Tool is wrong; code is actually safe | Suppress with justification comment |
| True Negative | Tool correctly identified no issue | No action |
| False Negative | Tool missed a real issue | Tune rules to catch this pattern |

### Writing a Triage Note

Good triage notes save time in future reviews and audits:

```
Finding: CWE-89 SQL Injection in /api/users.py line 87
Triage: TRUE POSITIVE
Impact: Attacker can read all user records from the database
Exploitability: HIGH — parameter is directly user-controllable via GET request
Affected: Customer-facing API, handles ~50k requests/day
Fix: Replace string concatenation with parameterized query
Priority: P1 — fix within 24 hours
```

```
Finding: CWE-89 SQL Injection in /internal/reports.py line 203
Triage: FALSE POSITIVE
Reason: The "user_id" variable is an integer validated via int() cast on line 198.
        An integer cannot carry SQL injection payloads. Tool missed the sanitizer.
Suppressed: Yes, with justification above
Reviewer: @security-engineer, 2024-03-15
```

---

## 3.6 Reducing False Positives (Tuning SAST)

High false-positive rates are the #1 reason developers stop trusting and using SAST tools.

### Tuning Strategies

**1. Add sanitizer annotations**
Tell the tool: "This function sanitizes data, do not flag data that passes through it."

```yaml
# Semgrep: mark a function as a sanitizer
- id: integer-cast-is-safe
  pattern: int($X)
  type: sanitizer
```

**2. Suppress specific findings with justification**

In code (use sparingly — each suppression must have a reason):
```python
# nosemgrep: python-sqli  -- safe: value is cast to int above
result = db.execute("SELECT * FROM orders WHERE user_id=" + str(user_id))
```

**3. Exclude generated code**
Code generated by ORMs, protobuf, or frontend build tools is not reviewed by humans and should not be scanned.

```yaml
# semgrep.yml
paths:
  exclude:
    - "**/*_pb2.py"         # generated protobuf
    - "src/generated/**"     # any generated code
    - "node_modules/**"
    - "**/*.min.js"
```

**4. Tune rules to match your framework**
If your team uses SQLAlchemy's ORM correctly, suppress the raw SQL pattern — SQLAlchemy handles parameterization internally.

**5. Set severity thresholds correctly**
Not all findings need to block the build. Only CRITICAL and HIGH should block. MEDIUM goes to backlog. LOW/INFO are informational.

---

## 3.7 Real-World Case Study: Heartbleed and SAST

**Heartbleed (CVE-2014-0160)** was a vulnerability in OpenSSL that allowed attackers to read 64KB of server memory per request. Passwords, private keys, session tokens — all leaked. Affected over 500,000 websites.

**The bug (simplified):**
```c
// Attacker sends: "hello" with claimed length = 65535
memcpy(bp, p, payload);  // copies 65535 bytes — but "hello" is only 5 bytes!
                          // reads 65530 bytes of adjacent memory
```

**Could SAST have caught it?**
A modern SAST tool with bounds-checking rules and taint analysis would likely flag:
- `memcpy` called with user-controlled length without validation
- No check that `payload <= actual_data_length`

Semgrep has rules today that catch this exact pattern in C code. Had OpenSSL used SAST in their development process, there is a reasonable chance this two-year-old bug would have been flagged earlier.

**Lesson:** Even widely-used, security-focused open-source code benefits from automated static analysis. And enterprise engineers should not just scan their own code — SCA (Chapter 5) scans the open-source libraries they use.

---

## 3.8 Custom SAST Rules for Your Application

Generic SAST rulesets miss application-specific vulnerabilities. Write custom rules for your codebase.

### Scenario: Your App Has a Custom Encryption Function

Your codebase has a function `encrypt_with_weak_key()` that a developer wrote using DES (a broken algorithm). Generic SAST rules don't know your custom function name.

**Custom Semgrep rule:**
```yaml
rules:
  - id: custom-weak-encryption
    pattern: encrypt_with_weak_key($DATA)
    message: "Do not use encrypt_with_weak_key() — DES is broken. Use AES-256-GCM via the approved crypto module."
    severity: ERROR
    languages: [python]
    metadata:
      cwe: CWE-327
      remediation: "Use crypto_module.encrypt_aes256gcm($DATA) instead"
```

### Scenario: Your API Framework Has a Known Dangerous Pattern

Your Python FastAPI app uses a specific pattern for database queries. Write rules that understand your patterns:

```yaml
rules:
  - id: raw-sql-in-fastapi
    patterns:
      - pattern: |
          async def $HANDLER($REQ: Request, ...):
            ...
            $DB.execute("..." + $USER_INPUT)
    message: "Raw SQL in FastAPI handler with user input — use parameterized queries"
    severity: ERROR
    languages: [python]
```

---

## 3.9 SAST Metrics to Track

| Metric | What It Tells You |
|---|---|
| Findings per 1,000 lines of code | Code quality and security debt density |
| False positive rate | How much developers trust the tool |
| Mean time to fix (MTTF) by severity | How responsive teams are to security findings |
| Fix rate over time | Is security debt growing or shrinking? |
| Coverage (% repos scanned) | Are any repos flying under the radar? |

---

## Chapter 3 Summary

| Topic | Key Takeaway |
|---|---|
| How SAST works | Pattern matching + AST + taint analysis — tracks tainted data from sources to sinks |
| What it finds | Injection, XSS, hardcoded secrets, weak crypto, path traversal |
| What it misses | Runtime auth/authz issues, business logic, configuration |
| Key tools | Semgrep (fast, flexible), SonarQube (quality+security), Checkmarx/Veracode (enterprise deep analysis) |
| CI integration | Diff scan on every PR; full scan nightly; critical findings block merge |
| Tuning | Suppress false positives with justification; exclude generated code; write custom rules |
| Triage | True positive → fix; false positive → suppress + justify; always document |

---

*Next: [Chapter 4 — DAST: Dynamic Application Security Testing](04-DAST.md)*
