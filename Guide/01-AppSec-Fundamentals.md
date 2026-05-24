# Chapter 1: Application Security Fundamentals

> **Goal:** Understand the mental model that AppSec engineers use every day — how security fits into software development, what the most common vulnerabilities are, and how to think like an attacker while building like an engineer.

---

## 1.1 What Is Application Security?

Application security (AppSec) is the practice of finding and fixing security weaknesses in software — before attackers exploit them.

Think of it this way:
- A **developer** asks: "Does this feature work?"
- An **AppSec engineer** asks: "Can someone misuse this feature to steal data, break access controls, or take over the system?"

AppSec is **not** just running a scanner. It is a discipline that spans design, code, testing, deployment, and monitoring.

### Why It Matters at Enterprise Scale

At a startup, one developer might manually review every PR. At an enterprise with 500 engineers across 200 services, manual review does not scale. You need:

- Automated scanners wired into every CI/CD pipeline
- Policies that enforce standards without requiring a human gatekeeper on every PR
- A triage system to prioritize thousands of findings by real risk
- Developer education so security is built-in, not bolted on

---

## 1.2 The Secure Software Development Lifecycle (SSDLC)

The SDLC is the process software teams use to plan, build, and release software. The **Secure SDLC (SSDLC)** adds security activities at every phase so vulnerabilities are caught early — when they are cheap to fix.

### The Cost of Fixing Bugs Late

| Phase Found | Relative Cost to Fix |
|---|---|
| Requirements / Design | 1x |
| Development (code review) | 6x |
| Testing (QA) | 15x |
| Production (after release) | 100x |

Finding a SQL injection in a design review takes 10 minutes. Finding it after a breach costs millions.

### SSDLC Phases and Security Activities

```
Requirements → Design → Development → Testing → Release → Operations
     |              |          |            |          |          |
Security       Threat      Secure       SAST +     Security   Monitor +
requirements   modeling    coding       DAST +     sign-off   Incident
+ abuse cases  + arch      + code       SCA                   response
               review      review
```

#### Phase 1: Requirements
- Define **security requirements** alongside functional requirements
- Example: "The login endpoint must rate-limit to 5 attempts per minute per IP"
- Define **abuse cases**: "What if an attacker submits 10,000 login attempts per second?"

#### Phase 2: Design
- Run **threat modeling** sessions (covered in §1.4)
- Review system architecture for trust boundaries, data flows, and attack surfaces
- Identify high-risk components (authentication, payments, PHI handling)

#### Phase 3: Development
- Apply **secure coding practices** (covered in §1.5)
- Enforce through IDE plugins and pre-commit hooks
- Security-focused code reviews (not just functional review)

#### Phase 4: Testing
- **SAST** — scan source code for vulnerabilities (Chapter 3)
- **DAST** — attack the running application (Chapter 4)
- **SCA** — check third-party dependencies for CVEs (Chapter 5)
- **Penetration testing** for high-risk features

#### Phase 5: Release
- Security sign-off gate in CI/CD
- Verify all critical/high findings are resolved or accepted
- Generate SBOM (Software Bill of Materials)

#### Phase 6: Operations
- Monitor production logs for attack patterns
- Patch vulnerabilities in running systems
- Incident response when things go wrong

### Industry SSDLC Models

**Microsoft SDL (Security Development Lifecycle):** The original enterprise SSDLC. Defines mandatory security activities per phase. Used at Microsoft and adopted widely in enterprise.

**OWASP SAMM (Software Assurance Maturity Model):** Measures how mature your AppSec program is across 15 security practices in 5 business functions. Scored 1–3 per practice. Useful for building a roadmap.

---

## 1.3 OWASP Top 10 (2021)

The OWASP Top 10 is the most widely used reference for web application security risks. It is updated every 3–4 years based on real-world vulnerability data.

**OWASP** = Open Web Application Security Project (nonprofit, free resources at owasp.org)

The 2021 list covers the 10 most critical risk categories:

---

### A01: Broken Access Control

**What it is:** The application does not properly enforce who can do what. A regular user can access admin functions, view other users' data, or perform actions they should not be allowed to do.

**Simple analogy:** A hotel key card that opens every room, not just yours.

**Real example:**
- User A is logged in and views their profile at `/profile?user_id=123`
- They change the URL to `/profile?user_id=124` and see User B's private data
- This is called **IDOR (Insecure Direct Object Reference)**

**What AppSec engineers do:**
- Check every endpoint: "Does this verify the logged-in user owns this resource?"
- Write authorization tests as part of automated test suites
- Look for missing `@authorize` decorators, missing ownership checks

**Mitigation:**
- Always check authorization server-side, never trust client-supplied user IDs
- Implement attribute-based access control (ABAC) for complex scenarios
- Deny by default — if no explicit allow rule exists, deny access

---

### A02: Cryptographic Failures

**What it is:** Sensitive data (passwords, credit cards, health records) is not properly protected with encryption, or encryption is implemented incorrectly.

**Simple analogy:** Locking your front door with a combination of "0000."

**Real example — Equifax 2017:**
Equifax stored Social Security Numbers encrypted, but the encryption key was also stored on the same server in a readable file. The attacker stole both the encrypted data and the key.

**Common failures:**
- Passwords stored as MD5 or SHA1 hashes (easily crackable with rainbow tables)
- HTTP instead of HTTPS for sensitive pages
- Weak TLS versions (TLS 1.0, TLS 1.1) still enabled
- Encryption keys hardcoded in source code

**Mitigation:**
- Hash passwords with bcrypt, Argon2, or scrypt (not MD5/SHA1)
- Enforce TLS 1.2+ with HSTS (HTTP Strict Transport Security)
- Store encryption keys in dedicated key management systems (AWS KMS, HashiCorp Vault)
- Classify data — know what is sensitive before deciding how to protect it

---

### A03: Injection

**What it is:** User-supplied input is passed directly into interpreters (SQL databases, OS shells, LDAP servers) without validation, allowing attackers to inject malicious commands.

**Simple analogy:** Asking someone "What's your name?" and they answer `Robert'); DROP TABLE students;--` (the famous XKCD comic).

**SQL Injection example:**
```python
# VULNERABLE — never do this
query = "SELECT * FROM users WHERE username = '" + username + "'"

# If username = "admin' OR '1'='1"
# Query becomes: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
# Returns ALL users — attacker is logged in as admin
```

**Fixed:**
```python
# SAFE — parameterized query
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

**Other injection types:**
- **Command injection:** `os.system("ping " + user_input)` — attacker injects `; rm -rf /`
- **LDAP injection:** Attackers manipulate directory queries
- **Template injection:** Server-side template engines interpret attacker input as code

**Mitigation:**
- Always use parameterized queries / prepared statements
- Validate and sanitize all input at the boundary
- Use ORM (SQLAlchemy, Hibernate) correctly — raw queries bypass ORM protections

---

### A04: Insecure Design

**What it is:** Security flaws baked into the architecture itself — not bugs in implementation, but fundamental design mistakes that no amount of code fixes can fully address.

**Simple analogy:** Designing a bank vault with windows.

**Real example — Password Reset Flaws:**
Many apps send a password reset link via email but also allow resetting via "security questions" like "What was your first pet's name?" — information an attacker can look up on social media. The design allows bypassing email-based MFA.

**What AppSec engineers do:**
- Participate in design reviews before code is written
- Run threat modeling (§1.4) to catch insecure designs early
- Write security requirements: "The password reset flow MUST use a time-limited, single-use token sent to a verified email or phone"

**Mitigation:**
- Security requirements and abuse case analysis during requirements phase
- Threat modeling during design
- Reference architectures for common patterns (auth, payments, file upload)

---

### A05: Security Misconfiguration

**What it is:** Secure software deployed with insecure settings — default passwords left unchanged, unnecessary features enabled, debug mode left on, overly permissive permissions.

**Simple analogy:** A state-of-the-art safe left unlocked because the owner never set a combination.

**Real example — MongoDB default configuration:**
In 2017, thousands of MongoDB databases were exposed publicly with no authentication because the default config bound to all interfaces with no password. Attackers wiped databases and demanded ransom.

**Common misconfigurations:**
- Default admin credentials not changed (`admin/admin`, `admin/password`)
- S3 buckets set to public read
- Verbose error messages showing stack traces in production
- Unnecessary ports and services open
- Security headers missing (CSP, X-Frame-Options, HSTS)

**Mitigation:**
- Infrastructure-as-Code (IaC) with security scanning (Checkov, tfsec)
- Hardening benchmarks (CIS Benchmarks for every major platform)
- Automated configuration scanning (Prowler for AWS, Trivy for containers)
- Environment-specific configs — debug mode is always OFF in production

---

### A06: Vulnerable and Outdated Components

**What it is:** Using third-party libraries, frameworks, or system components with known vulnerabilities.

**Simple analogy:** Leaving a faulty car part unrepaired because replacing it is inconvenient.

**Real example — Equifax (Apache Struts CVE-2017-5638):**
Apache Struts had a critical remote code execution (RCE) vulnerability. A patch was available for 2 months. Equifax did not apply it. Attackers exploited it, stole 147 million Americans' personal data. Equifax paid $575 million in fines.

**Real example — Log4Shell (CVE-2021-44228):**
Log4j, a Java logging library used in thousands of enterprise applications, had a vulnerability allowing remote code execution via a single log message. Every enterprise scrambled to find which of their hundreds of services used Log4j.

**This is why SCA (Software Composition Analysis) matters.** You need to know every dependency you use and whether it has a known CVE.

**Mitigation:**
- SCA tools: Trivy, Grype, Dependabot, Snyk
- SBOM (Software Bill of Materials) — a complete inventory of every component
- Dependency update automation (Dependabot, Renovate)
- Define SLAs: patch critical CVEs within 24 hours, high within 7 days

---

### A07: Identification and Authentication Failures

**What it is:** Weaknesses in how users are identified and authenticated — weak passwords, broken session management, missing multi-factor authentication.

**Simple analogy:** A bank that accepts "I promise I'm John Smith" as valid ID.

**Common failures:**
- No account lockout — attackers can try millions of passwords (brute force)
- Session tokens that don't expire
- JWTs with weak secrets (`secret123`) or `alg: none` accepted
- No MFA for admin accounts
- Passwords allowed to be `123456`

**Real example — Rockstar Games 2022:**
Grand Theft Auto 6 footage leaked because an attacker used social engineering + SIM swapping to bypass SMS-based MFA. The attacker convinced a telecom to transfer the employee's phone number to an attacker-controlled SIM.

**Mitigation:**
- Enforce strong password policies + breached password checks (Have I Been Pwned API)
- MFA for all accounts, especially admin
- Implement account lockout and rate limiting on auth endpoints
- Use secure session management: HttpOnly, Secure, SameSite=Strict cookies
- JWT: validate signature, algorithm (`alg`), expiry (`exp`), and audience (`aud`)

---

### A08: Software and Data Integrity Failures

**What it is:** Code or data is used without verifying it hasn't been tampered with — insecure CI/CD pipelines, auto-updating from untrusted sources, deserializing untrusted data.

**Real example — SolarWinds 2020:**
Attackers compromised SolarWinds' build system and injected malicious code into the Orion software update. 18,000 organizations downloaded and installed the backdoored update, including US government agencies. The malicious code was **digitally signed** by SolarWinds — because the build system itself was compromised.

**Real example — event-stream npm package:**
A malicious contributor was given maintainer rights to a popular npm package. They added a dependency that stole cryptocurrency from certain wallets. Downloaded 8 million times before discovery.

**Mitigation:**
- Sign all artifacts (container images, packages) and verify signatures before use
- Pin dependency versions and verify checksums (`npm ci` with lockfile)
- Secure CI/CD pipelines — restrict who can modify build scripts
- SBOM to track what goes into every build
- Never deserialize data from untrusted sources without validation

---

### A09: Security Logging and Monitoring Failures

**What it is:** Not logging enough (or anything), not monitoring logs for attacks, or not alerting when attacks happen.

**Simple analogy:** A bank with security cameras but nobody ever watches the footage — and the cameras don't record.

**Real example — Marriott/Starwood 2018:**
Attackers had access to Starwood's systems for **4 years** before discovery. Why? No adequate monitoring. 500 million guest records were stolen over those 4 years. Marriott only discovered the breach because of a security alert on an internal security tool — not their logging system.

**What to log:**
- All authentication events (success and failure)
- Authorization failures (user tried to access something they can't)
- All admin actions
- Input validation failures (signs of probing/fuzzing)
- Changes to security configuration

**Mitigation:**
- Centralized logging (ELK Stack, Splunk, CloudWatch)
- SIEM (Security Information and Event Management) for correlation
- Alert on: multiple auth failures, impossible travel, off-hours admin actions
- Log retention: 90 days hot, 1 year cold (for compliance)

---

### A10: Server-Side Request Forgery (SSRF)

**What it is:** The application fetches a URL or resource based on user input. An attacker supplies a malicious URL pointing to internal services (cloud metadata APIs, internal databases, etc.).

**Simple analogy:** A courier who will deliver packages to any address you give them — including restricted internal areas.

**Real example — Capital One 2019:**
A misconfigured WAF allowed SSRF. The attacker used SSRF to query the AWS EC2 instance metadata endpoint (`http://169.254.169.254/latest/meta-data/iam/security-credentials/`) and retrieved temporary AWS credentials. With those credentials, they downloaded 100 million customer records from S3.

**How it works:**
```
1. App has a feature: "Enter a URL to preview an image"
2. Attacker enters: http://169.254.169.254/latest/meta-data/iam/security-credentials/
3. App fetches this URL server-side
4. Returns AWS IAM credentials to the attacker
```

**Mitigation:**
- Allowlist of permitted domains/IPs for outbound requests
- Block requests to private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x)
- Use cloud IMDSv2 (requires a session token — prevents simple SSRF exploitation)
- Validate and sanitize all URLs before fetching

---

## 1.4 Threat Modeling

Threat modeling is a **structured way to identify security risks during design** — before a single line of code is written.

Think of it as "brainstorming every way an attacker could break this" in a meeting room, not in a post-breach review.

### The STRIDE Framework

STRIDE is a mnemonic for six threat categories:

| Letter | Threat | Question to Ask | Security Control |
|---|---|---|---|
| **S** | Spoofing | Can an attacker pretend to be someone else? | Authentication |
| **T** | Tampering | Can an attacker modify data in transit or at rest? | Integrity checks, signing |
| **R** | Repudiation | Can an attacker deny they performed an action? | Audit logging |
| **I** | Information Disclosure | Can an attacker read data they shouldn't? | Encryption, authorization |
| **D** | Denial of Service | Can an attacker make the system unavailable? | Rate limiting, redundancy |
| **E** | Elevation of Privilege | Can an attacker gain more access than allowed? | Authorization, least privilege |

### How to Run a Threat Modeling Session

**Step 1: Gather the right people**
- Developer (knows the code)
- Architect (knows the design)
- AppSec engineer (knows the attack patterns)
- Product manager (knows the business context)

**Step 2: Draw a Data Flow Diagram (DFD)**

Show how data moves through the system:
```
User Browser → [TLS] → Load Balancer → [TLS] → API Server → Database
                                                    ↓
                                               Auth Service
```
Mark **trust boundaries** — where data crosses from one trust zone to another (internet → internal, user → admin, service A → service B).

**Step 3: Apply STRIDE to each component and data flow**

For each element in the DFD, ask: Which STRIDE threats apply here?

Example — API Server receives user login request:
- **S:** Could attacker spoof another user? → Validate JWT signature
- **T:** Could attacker tamper with the token? → JWT is signed, check signature
- **R:** Could attacker deny logging in as admin? → Log all auth events
- **I:** Could attacker read another user's response? → Check authorization on every endpoint
- **D:** Could attacker flood login endpoint? → Rate limiting
- **E:** Could attacker escalate from user to admin? → RBAC enforced server-side

**Step 4: Document findings as security requirements**

Each threat becomes a security requirement:
- "The API MUST rate-limit login to 5 attempts per minute per IP"
- "Every response MUST only return data belonging to the authenticated user"
- "All auth events MUST be logged with user ID, IP, timestamp, and result"

**Step 5: Track and review**

Store threat models in version control. Review when the system changes. Threat models that are never updated become fiction.

### Real Example — SolarWinds and the Missing Trust Boundary

SolarWinds never threat-modeled their build pipeline as an attack surface. They did not ask: "What if an attacker compromised our build server?" There was no threat, no control, no detection. If they had threat-modeled their CI/CD pipeline using STRIDE, **Tampering** would have flagged: "Could an attacker modify our build artifacts before signing?" The answer would have led to controls like build server isolation, SBOM generation, and independent artifact verification.

---

## 1.5 Secure Coding Principles

These are the fundamental rules that every enterprise developer should follow. As an AppSec engineer, your job is to enforce these through code reviews, training, and tooling.

### Principle 1: Input Validation

**Never trust user input.** Validate everything at the boundary of your system.

- **Allowlist > Denylist:** Define what is allowed (letters, numbers, specific formats). Reject everything else. Do not try to block "bad" characters — you will always miss one.
- **Validate type, length, format, and range:** An age should be a positive integer between 0 and 150. A phone number should match a specific format.

```python
# Bad — trusting user input directly
user_age = request.get("age")
db.execute(f"SELECT * FROM users WHERE age = {user_age}")

# Good — validate before use
user_age = request.get("age")
if not isinstance(user_age, int) or user_age < 0 or user_age > 150:
    raise ValueError("Invalid age")
db.execute("SELECT * FROM users WHERE age = ?", (user_age,))
```

### Principle 2: Output Encoding

**Encode data when outputting it** to prevent it from being interpreted as code.

- When outputting to HTML: HTML-encode (`<` becomes `&lt;`)
- When outputting to JavaScript: JavaScript-encode
- When outputting to SQL: Use parameterized queries (not encoding)
- When outputting to OS commands: Avoid it; if required, use safe APIs

This prevents XSS (Cross-Site Scripting).

### Principle 3: Parameterized Queries

**Never concatenate user input into SQL.** Always use parameterized queries.

```python
# VULNERABLE
query = "SELECT * FROM orders WHERE user_id = " + user_id

# SAFE
query = "SELECT * FROM orders WHERE user_id = %s"
cursor.execute(query, (user_id,))
```

### Principle 4: Least Privilege

**Give every component only the permissions it needs — nothing more.**

- A read-only reporting service should not have database write access
- A CI/CD pipeline that deploys to S3 should not have IAM Admin rights
- A web application should connect to the database as a user with SELECT/INSERT/UPDATE — not as root

### Principle 5: Fail Securely

**When something goes wrong, fail in a way that does not expose sensitive information or grant unintended access.**

```python
# Bad — fails open (grants access on error)
try:
    result = check_authorization(user_id, resource_id)
    if result:
        return data
except Exception:
    return data  # ERROR: returns data even when auth check failed

# Good — fails closed (denies access on error)
try:
    result = check_authorization(user_id, resource_id)
    if result:
        return data
    return 403_forbidden()
except Exception:
    log.error("Authorization check failed", exc_info=True)
    return 500_internal_error()
```

### Principle 6: Defense in Depth

**Never rely on a single security control.** Layer multiple controls so that if one fails, others compensate.

Example — protecting sensitive data:
1. Encryption at rest (if disk is stolen, data is unreadable)
2. Encryption in transit (TLS — if network is intercepted, data is unreadable)
3. Access control (only authorized users can request the data)
4. Audit logging (detect unauthorized access attempts)
5. Monitoring and alerting (alert when access patterns look suspicious)

### Principle 7: Secure Error Handling

**Never expose internal details in error messages shown to users.**

```python
# Bad — reveals internal path and database schema
raise Exception(f"Database error at /var/app/models/user.py:42: column 'ssn' not found in table 'users'")

# Good — generic user-facing message, detailed internal log
log.error("Database error", exc_info=True, extra={"user_id": user_id})
return {"error": "An unexpected error occurred. Please try again."}
```

---

## 1.6 Application Security Testing Methods

| Method | What It Tests | When to Use | Tools |
|---|---|---|---|
| **SAST** (Static) | Source code, bytecode | Every pull request | Semgrep, SonarQube, Checkmarx |
| **DAST** (Dynamic) | Running application | Staging, nightly | OWASP ZAP, Burp Suite |
| **SCA** (Composition) | Third-party dependencies | Every pull request | Trivy, Grype, Snyk |
| **IAST** (Interactive) | App behavior during testing | QA test execution | Contrast Security |
| **RASP** (Runtime) | Live production app | Production | Sqreen, Contrast |
| **Penetration Testing** | Full attack simulation | Quarterly, pre-launch | Manual + tools |

### When Each Finds Bugs

Think of it as layers:
```
SAST → finds SQL injection in source code before it's deployed
SCA  → finds vulnerable library before it's shipped
DAST → finds auth bypass in the running app that SAST missed
IAST → finds data flow issues only visible at runtime
Pen Test → finds business logic flaws that automated tools miss
```

All methods are complementary. Enterprise programs use all of them.

---

## Chapter 1 Summary

| Concept | Key Takeaway |
|---|---|
| SSDLC | Security at every phase is cheaper than security after the fact |
| OWASP Top 10 | Know all 10, their real-world examples, and mitigations |
| Threat Modeling | STRIDE + DFD + trust boundaries = security requirements before code |
| Secure Coding | Input validation, output encoding, parameterized queries, least privilege |
| Testing Methods | SAST + SCA on every PR; DAST on staging; pen test quarterly |

---

*Next: [Chapter 2 — Git & SCM Security](02-SCM-Security.md)*
