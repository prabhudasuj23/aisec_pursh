# Chapter 4: DAST — Dynamic Application Security Testing

> **Goal:** Understand how DAST works, what kinds of vulnerabilities it catches that SAST misses, how to use OWASP ZAP and Burp Suite, and how to integrate DAST into enterprise CI/CD pipelines.

---

## 4.1 What Is DAST?

**Dynamic Application Security Testing (DAST)** tests a **running application** by sending requests to it and analyzing the responses — exactly like an attacker would.

The key word is "dynamic" — the application is actually running and the tool interacts with it over HTTP/HTTPS.

### SAST vs DAST — Simple Comparison

| | SAST | DAST |
|---|---|---|
| Tests | Source code (not running) | Running application |
| Needs source code? | Yes | No |
| Finds | Code-level flaws (SQL injection patterns) | Runtime flaws (actual exploitable XSS) |
| False positives | High (flags patterns that may be safe) | Low (confirmed exploitable) |
| False negatives | Can miss runtime-only issues | Can miss code-level issues |
| When | PR / pre-merge | Staging / nightly |
| Speed | Fast (seconds–minutes) | Slow (minutes–hours) |

**They complement each other.** SAST finds the pattern in code; DAST confirms it is actually exploitable at runtime.

### What DAST Finds That SAST Misses

- **Authentication and session management flaws** (session fixation, missing logout, session tokens not expiring)
- **Misconfigurations** (missing security headers, TLS version issues, exposed admin panels)
- **Business logic flaws** (skipping payment step, price manipulation, workflow bypass)
- **Second-order injection** (data stored in DB, then later output unsanitized)
- **Race conditions** visible at runtime
- **Open redirect vulnerabilities**
- **CORS misconfigurations**

---

## 4.2 How DAST Works

### Step 1: Crawl (Spider/Discovery)

The DAST tool discovers all the pages, endpoints, and input fields in the application.

```
Starting URL: https://app.example.com

Crawler finds:
- /login (POST: username, password)
- /profile?user_id=123 (GET)
- /api/orders (GET, POST)
- /admin/users (GET)
- /search?q=keyword (GET)
```

For APIs, DAST tools use OpenAPI/Swagger specs instead of crawling — this gives them exact endpoint and parameter definitions.

### Step 2: Attack (Active Scanning)

The tool sends malicious payloads to each input field and analyzes responses.

For the `/search?q=keyword` parameter, DAST tries:
```
q=<script>alert(1)</script>    → Does the response reflect the script? (XSS)
q=' OR '1'='1                  → Does the response return unexpected data? (SQLi)
q=../../../../etc/passwd       → Does the response return file contents? (Path traversal)
q=http://internal-service/     → Does the response fetch from internal URLs? (SSRF)
```

### Step 3: Analyze and Report

The tool confirms vulnerabilities by examining responses:
- XSS: Was `<script>` reflected unencoded in the HTML response?
- SQLi: Did the response contain database errors or unexpected data?
- Auth bypass: Did a protected endpoint return data without valid credentials?

DAST reports confirmed vulnerabilities with request/response pairs — developers can reproduce the issue exactly.

---

## 4.3 Authentication in DAST

**The biggest DAST challenge:** Most enterprise applications require login. A DAST scanner that cannot log in can only test the login page and public content.

### Types of Authentication Configuration

**1. Form-based login (username/password)**

Configure DAST with credentials and the login form fields:
```yaml
# ZAP configuration
authentication:
  type: form-based
  login_url: https://app.example.com/login
  username_field: username
  password_field: password
  credentials:
    username: dast-test-user@example.com
    password: "${DAST_PASSWORD}"  # loaded from secrets manager, not hardcoded
  login_indicator: "Dashboard"    # text that confirms successful login
```

**2. Bearer token / JWT**

For APIs that use token-based auth:
```yaml
authentication:
  type: script
  script: |
    # 1. POST to /auth/token with credentials
    # 2. Extract JWT from response
    # 3. Add "Authorization: Bearer <token>" header to all requests
```

**3. OAuth / OIDC**

Modern enterprise apps often use SSO. DAST needs a script to complete the OAuth flow.

### DAST Users Should Be Dedicated Test Accounts

**Never run DAST against production with real user credentials.** Use:
- Dedicated DAST test accounts with real permissions (so DAST can test authenticated flows)
- Synthetic test data (so DAST does not delete real data)
- A flag to mark DAST sessions in audit logs (so security teams can filter noise)

---

## 4.4 Web Application Security Testing Focus Areas

### Testing Authentication

Check for:
- **Brute force protection:** Send 100 login attempts — does the account lock?
- **Password policy:** Can you set password `1`? Password `password`?
- **Account enumeration:** Does `/forgot-password?email=user@example.com` respond differently if the email exists vs. does not exist? (Allows attackers to enumerate valid accounts)
- **Session fixation:** Set a session cookie before login — does the app issue a new session cookie after login?
- **Session expiry:** Login, wait 2 hours, try to use the session — does it expire?
- **Logout effectiveness:** Login, click logout, press Back button — does cached page show protected content?

### Testing Session Management

- **Cookie flags:**
  - `HttpOnly` — cookie cannot be accessed by JavaScript (prevents XSS cookie theft)
  - `Secure` — cookie only sent over HTTPS
  - `SameSite=Strict` or `SameSite=Lax` — prevents CSRF

- **Predictable session IDs:** If session tokens are sequential or based on timestamp, an attacker can guess valid sessions.

- **Session token length:** Short tokens are brute-forceable. 128+ bits of entropy required.

### Testing for IDOR (Insecure Direct Object Reference)

One of the most common real-world vulnerabilities:

1. Log in as User A
2. Create an order → application shows `/orders/1042`
3. Log in as User B
4. Navigate to `/orders/1042` — can User B see User A's order?

This is a manual test or requires DAST with two sets of credentials (replay attack testing).

---

## 4.5 API Security Testing

Modern enterprise applications are often API-first. API testing requires different techniques than web application testing.

### OWASP API Security Top 10 (2023)

| # | Risk | Simple Explanation |
|---|---|---|
| API1 | Broken Object Level Authorization | Access other users' resources via ID manipulation |
| API2 | Broken Authentication | Weak tokens, no expiry, improper validation |
| API3 | Broken Object Property Level Auth | GET /users returns all fields including password hash |
| API4 | Unrestricted Resource Consumption | No rate limiting, large payloads cause DoS |
| API5 | Broken Function Level Authorization | Regular user calls admin-only API endpoint |
| API6 | Unrestricted Access to Sensitive Business Flows | Scrape product catalog, manipulate coupons |
| API7 | Server-Side Request Forgery | API fetches URLs you specify |
| API8 | Security Misconfiguration | CORS allows any origin, verbose error messages |
| API9 | Improper Inventory Management | Old API versions still accessible, undocumented debug endpoints |
| API10 | Unsafe Consumption of APIs | Trust third-party API responses without validation |

### API DAST Techniques

**Schema-based fuzzing:**
Use OpenAPI/Swagger spec to generate malicious payloads for every parameter:

```yaml
# OpenAPI spec tells DAST:
# POST /users/{id}/orders
# Parameters: id (integer), amount (number), product_id (string)
# DAST tries:
# - id: -1, 0, 99999999, "1; DROP TABLE users"
# - amount: -100, 99999999, "abc"
# - product_id: <script>alert(1)</script>, ../../../../etc/passwd
```

**Rate limiting verification:**
Send 1,000 requests per second to an endpoint — does the API throttle or return 429?

**Mass assignment testing:**
POST `/users` with extra fields not in the normal form: `{"name": "Alice", "role": "admin"}` — does the API accept and apply the `role` field?

---

## 4.6 OWASP ZAP — The Primary Open-Source DAST Tool

**OWASP ZAP (Zed Attack Proxy)** is the most widely used open-source DAST tool. It is free and maintained by OWASP.

### ZAP Scan Modes

**1. Baseline Scan (for CI/CD)**
- Spider the app
- Run passive checks only (no attacks — reads responses, does not send malicious input)
- Fast: 1–5 minutes
- Use on every PR to catch configuration issues

**2. Full Scan (nightly)**
- Spider the app
- Run active attack checks
- Slow: 30 minutes – several hours depending on app size
- Use in staging environment, not production

**3. API Scan**
- Import OpenAPI/Swagger/SOAP spec
- Test every API endpoint defined in the spec
- Active attacks on all parameters

### ZAP in GitHub Actions (Baseline Scan)

```yaml
name: DAST Baseline Scan
on:
  pull_request:

jobs:
  dast:
    runs-on: ubuntu-latest
    steps:
      - name: Start app (staging)
        run: docker-compose up -d

      - name: Wait for app to be ready
        run: sleep 20

      - name: ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: 'http://localhost:8000'
          rules_file_name: '.zap/rules.tsv'
          fail_action: true
          issue_title: 'ZAP Baseline Scan Report'

      - name: Upload ZAP Report
        uses: actions/upload-artifact@v4
        with:
          name: zap-report
          path: report_html.html
```

### ZAP in GitHub Actions (Full API Scan)

```yaml
- name: ZAP API Scan
  uses: zaproxy/action-api-scan@v0.7.0
  with:
    target: 'http://localhost:8000/openapi.json'
    format: openapi
    fail_action: true
```

### Configuring ZAP Rules

ZAP finds many issues, not all of which matter for your app. Configure a rules file to tune severity:

```tsv
# .zap/rules.tsv
# Format: Rule-ID	ACTION	PARAM	VALUE
# ACTIONS: IGNORE, WARN, FAIL

10020	WARN		# X-Frame-Options — warn but don't fail
10021	WARN		# X-Content-Type-Options
10038	FAIL		# Content Security Policy not set — fail the build
10202	FAIL		# Absence of Anti-CSRF Tokens
40018	FAIL		# SQL Injection
40014	FAIL		# Cross Site Scripting
```

---

## 4.7 Burp Suite — The Professional Manual Testing Tool

**Burp Suite** is the industry-standard tool for professional penetration testing and manual security testing. The Community edition is free; the Professional edition ($499/year) adds the active scanner.

### Key Burp Suite Features

**Proxy:** Intercept HTTP/HTTPS traffic between browser and server. Modify requests before they are sent.

**Repeater:** Send the same request repeatedly with modifications. Used to test injection payloads manually.

**Intruder:** Automated fuzzing — send many requests with different payloads to find vulnerabilities.

**Scanner (Pro):** Automated active scanning similar to ZAP, but often with better results for complex apps.

**Decoder/Encoder:** Encode/decode Base64, URL-encoded, HTML-encoded data in parameters.

### Manual Testing Workflow with Burp Suite

1. **Configure browser** to proxy through Burp Suite (127.0.0.1:8080)
2. **Browse the application** normally — Burp captures all requests in the Proxy > HTTP History tab
3. **Find interesting requests** (login, search, profile updates, file upload)
4. **Right-click → Send to Repeater** to manually test that request
5. **Modify parameters** to test for vulnerabilities
6. **Document findings** with request/response screenshots

### Example: Testing for IDOR with Burp Repeater

```
Original request:
GET /api/orders/1042 HTTP/1.1
Host: app.example.com
Authorization: Bearer <User_A_Token>

Test: Change 1042 to 1041 (another user's order)
GET /api/orders/1041 HTTP/1.1
Authorization: Bearer <User_A_Token>

Response: 200 OK + User B's order data
→ IDOR CONFIRMED
```

---

## 4.8 Interpreting DAST Results and Writing Remediation Guidance

### Severity Classification for DAST Findings

| DAST Finding | Severity | Why |
|---|---|---|
| SQL injection (confirmed) | Critical | Database compromise, data theft |
| XSS stored | High | Can steal sessions, deface app |
| XSS reflected | Medium–High | Requires social engineering to exploit |
| CSRF (no token) | High | Allows attacker to perform actions as victim |
| Missing HSTS | Medium | Allows downgrade to HTTP |
| Missing CSP | Medium | Reduces XSS exploitability, not a vulnerability itself |
| Missing X-Frame-Options | Medium | Clickjacking possible |
| Information disclosure (stack trace) | Low–Medium | Aids attackers, does not directly enable compromise |
| Directory listing enabled | Medium | Exposes file structure |

### Writing Developer-Friendly Remediation

**Bad remediation guidance:**
> "SQL injection found. Fix the SQL injection."

**Good remediation guidance:**
```
Finding: SQL Injection in /api/search endpoint
Severity: Critical
Confirmed: Yes — tested with payload ' OR '1'='1 — returned all records

Root cause: Direct string concatenation of user input into SQL query
File: src/api/search.py, line 87

Vulnerable code:
  query = "SELECT * FROM products WHERE name LIKE '%" + search_term + "%'"
  db.execute(query)

Fix:
  query = "SELECT * FROM products WHERE name LIKE %s"
  db.execute(query, (f"%{search_term}%",))

Verification:
  - Re-run the test with payload ' OR '1'='1 — should return 0 results (treated as literal)
  - Run SAST scan — Semgrep rule python-sqli should no longer flag this line

Reference: OWASP A03:2021 Injection, CWE-89
```

---

## 4.9 Real-World Case Study: British Airways Magecart Attack (2018)

**What happened:** In 2018, attackers compromised British Airways' website and injected malicious JavaScript that skimmed credit card details from the payment page. 500,000 customers had their payment data stolen. BA was fined £20 million under GDPR.

**The attack:**
1. Attackers found a vulnerability in a third-party JavaScript library used on the BA website
2. They modified the library to include card-skimming code
3. The malicious JS sent payment form data to an attacker-controlled server

**How DAST could have helped:**

1. **Content Security Policy (CSP) testing:** DAST would flag missing or misconfigured CSP. A properly configured CSP would have blocked the malicious JS from calling the attacker's external server:
   ```
   Content-Security-Policy: script-src 'self' https://trusted-payment-provider.com
   # Blocks the malicious script from sending data to attacker.com
   ```

2. **Subresource Integrity (SRI) testing:** DAST would flag external scripts without SRI hashes:
   ```html
   <!-- Vulnerable: no integrity check -->
   <script src="https://cdn.example.com/script.js"></script>
   
   <!-- Safe: browser rejects if script is tampered with -->
   <script src="https://cdn.example.com/script.js"
           integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
           crossorigin="anonymous"></script>
   ```

3. **Dependency inventory:** SCA (Chapter 5) would have flagged the vulnerable third-party library version.

**Lesson:** DAST tests the behavior of the running application. Missing security headers are only visible at runtime — SAST cannot detect them because they are set in server configuration, not in application code.

---

## 4.10 DAST in Regulated Environments (Safe Scanning)

Running aggressive automated attacks against a production system is dangerous. DAST safety guidelines:

### Safe DAST Practices

**1. Always scan staging, not production**
- Use a staging environment with realistic but synthetic data
- DAST can cause unintended side effects: creating thousands of fake records, triggering emails, consuming API quotas

**2. Allowlist DAST traffic**
- Configure firewalls and WAF to allow DAST scanner IP
- Configure WAF to not block DAST payloads (otherwise you get false negatives)

**3. Use a scan policy appropriate to the environment**

| Environment | Scan Type | Aggressiveness |
|---|---|---|
| PR / CI | Passive/Baseline | Low — no active attacks |
| Staging (nightly) | Full active scan | Medium — all tests, synthetic data |
| Production | Passive monitoring only | None — active scanning not permitted |

**4. Out-of-scope items**
Define what DAST should NOT test:
- Password reset (would lock out test accounts)
- Email sending (would spam users)
- Third-party APIs (not your responsibility, may rate-limit you)
- File deletion endpoints

**5. Rate limiting**
Configure DAST to limit requests per second — do not DDoS your own staging environment.

---

## Chapter 4 Summary

| Topic | Key Takeaway |
|---|---|
| What DAST is | Tests running application by sending real HTTP requests with attack payloads |
| DAST vs SAST | SAST = code patterns; DAST = runtime confirmation; both needed |
| Authentication | Must configure DAST with test credentials; dedicated test accounts |
| API testing | Use OpenAPI spec; test BOLA, broken auth, rate limiting, mass assignment |
| OWASP ZAP | Baseline scan on PR; full scan nightly; configure rules to tune noise |
| Burp Suite | Manual testing, penetration testing, request/response manipulation |
| Safety | Scan staging only; use safe scan policies; define out-of-scope items |
| Remediation | Provide specific code fix, not just "fix it" |

---

*Next: [Chapter 5 — Vulnerability Management](05-Vulnerability-Management.md)*
