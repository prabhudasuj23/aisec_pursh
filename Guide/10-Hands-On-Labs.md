# Chapter 10: Hands-On Labs & Projects

> **Goal:** Practical exercises that turn knowledge into demonstrated skill. These labs are designed to build a portfolio of real work you can show in interviews and use on the job. Each lab has clear setup instructions, what to do, and what to document.

---

## 10.1 Why Hands-On Practice Is Non-Negotiable

AppSec knowledge without hands-on experience is like knowing the rules of chess without ever playing a game. Interviewers will ask:

- "Walk me through a vulnerability you found."
- "How did you set up your SAST pipeline?"
- "Show me a threat model you made."
- "What happened when you ran ZAP against your app?"

You need real answers to real questions. These labs give you those answers.

---

## 10.2 Lab Environment Setup

### What You Need

| Tool | Purpose | Install |
|---|---|---|
| Docker + Docker Compose | Run vulnerable apps and scanners | docker.com |
| Python 3.12 | Build demo apps | python.org |
| Git | Version control | git-scm.com |
| GitHub account | CI/CD and SCM labs | github.com |
| OWASP ZAP | DAST scanning | zaproxy.org |
| Semgrep | SAST scanning | semgrep.dev |
| Trivy | Container and SCA scanning | trivy.dev |

### Optional (for cloud labs)

| Tool | Purpose |
|---|---|
| AWS Free Tier account | Cloud security labs |
| Terraform | IaC labs |
| kubectl + minikube | Kubernetes labs |
| Burp Suite Community | Manual web testing |

---

## 10.3 Lab 1: OWASP Juice Shop — Exploitation and Remediation

**Time:** 4–6 hours  
**Skill:** Understanding OWASP Top 10 vulnerabilities through real exploitation

### Setup

```bash
# Run Juice Shop locally via Docker
docker pull bkimminich/juice-shop
docker run -d -p 3000:3000 bkimminich/juice-shop
# Open http://localhost:3000
```

### Exercises

**Exercise 1: SQL Injection (OWASP A03)**
1. Go to the login page
2. In the email field, enter: `' OR 1=1--`
3. Any password, click login
4. You are now logged in as the first user in the database (admin)

What to document:
- The request and response (use browser dev tools → Network tab)
- Why this worked (no parameterized query)
- What the fix looks like (parameterized query in code)

**Exercise 2: Broken Access Control — IDOR (OWASP A01)**
1. Log in as any user
2. Navigate to: `http://localhost:3000/api/BasketItems/1`
3. Try: `http://localhost:3000/api/BasketItems/2`
4. You can read another user's basket

What to document:
- The request showing the IDOR
- Why this worked (no ownership check in the API)
- The authorization check that should have been there

**Exercise 3: Stored XSS (OWASP A03)**
1. Go to the product reviews section
2. Submit a review with: `<script>alert('XSS')</script>`
3. When the review is displayed, the JavaScript executes

What to document:
- The stored XSS payload
- Why this worked (no output encoding)
- The output encoding fix (HTML entity encoding)

**Exercise 4: Sensitive Data Exposure**
1. View page source of the login page
2. Find the Angular source maps and look for sensitive strings
3. Navigate to: `http://localhost:3000/ftp/` — directory listing exposed
4. Download any file from the FTP directory

What to document:
- What sensitive information is exposed
- Why directory listing should be disabled
- What should be in `.gitignore` vs what should not be in the repo at all

### Portfolio Output

Write a 1–2 page vulnerability report covering at least 3 vulnerabilities you found, following the report format from Chapter 9.

---

## 10.4 Lab 2: Build a Vulnerable Demo API and Secure It

**Time:** 6–8 hours  
**Skill:** Writing vulnerable code, identifying it, fixing it — the full cycle

### Step 1: Build a Simple Vulnerable API

```python
# Create: vulnerable_api.py
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT)""")
    conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'Alice', 'alice@example.com', 'secret123')")
    conn.execute("INSERT OR IGNORE INTO users VALUES (2, 'Bob', 'bob@example.com', 'password')")
    conn.commit()
    return conn

# VULNERABILITY 1: SQL Injection
@app.route("/users/search")
def search_users():
    email = request.args.get("email", "")
    conn = get_db()
    # VULNERABLE: string concatenation into SQL
    query = f"SELECT id, name, email FROM users WHERE email LIKE '%{email}%'"
    users = conn.execute(query).fetchall()
    return jsonify([{"id": u[0], "name": u[1], "email": u[2]} for u in users])

# VULNERABILITY 2: No authorization (IDOR)
@app.route("/users/<int:user_id>")
def get_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"id": user[0], "name": user[1], "email": user[2]})

# VULNERABILITY 3: Hardcoded secret
API_SECRET = "super_secret_key_12345"

@app.route("/admin")
def admin():
    token = request.headers.get("X-Admin-Token")
    if token == API_SECRET:
        users = get_db().execute("SELECT * FROM users").fetchall()
        return jsonify(users)
    return jsonify({"error": "Unauthorized"}), 401

if __name__ == "__main__":
    app.run(debug=True, port=5000)  # VULNERABILITY 4: debug=True in "production"
```

### Step 2: Run Semgrep Against Your Code

```bash
pip install semgrep
semgrep --config p/python --config p/owasp-top-ten vulnerable_api.py --json > semgrep-results.json
```

**What you should see:**
- SQL injection finding on the `f"..."` line
- Hardcoded secret finding on `API_SECRET = "super_secret_key_12345"`
- Debug mode finding on `app.run(debug=True)`

### Step 3: Manually Exploit Each Vulnerability

Test the SQL injection:
```bash
curl "http://localhost:5000/users/search?email=' OR '1'='1"
# Should return all users if vulnerable
```

Test the IDOR:
```bash
# As "user 1", try to read user 2's data (no auth checks)
curl "http://localhost:5000/users/2"
```

Test the hardcoded secret:
```bash
# The secret is visible in source code — anyone who reads the code can use it
curl -H "X-Admin-Token: super_secret_key_12345" http://localhost:5000/admin
```

### Step 4: Fix Each Vulnerability

Create a `secure_api.py` with all vulnerabilities fixed:

```python
from flask import Flask, request, jsonify, g
import sqlite3
import os
import functools

app = Flask(__name__)

# FIX 3: Load secret from environment variable (not hardcoded)
API_SECRET = os.environ.get("API_SECRET")
if not API_SECRET:
    raise RuntimeError("API_SECRET environment variable is required")

def get_db():
    conn = sqlite3.connect("users.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'Alice', 'alice@example.com')")
    conn.execute("INSERT OR IGNORE INTO users VALUES (2, 'Bob', 'bob@example.com')")
    conn.commit()
    return conn

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token == "valid_user_1_token":
            g.user_id = 1
        elif token == "valid_user_2_token":
            g.user_id = 2
        else:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# FIX 1: Parameterized query — SQL injection fixed
@app.route("/users/search")
@require_auth
def search_users():
    email = request.args.get("email", "")
    conn = get_db()
    # SAFE: parameterized query
    users = conn.execute(
        "SELECT id, name, email FROM users WHERE email LIKE ?",
        (f"%{email}%",)
    ).fetchall()
    return jsonify([{"id": u[0], "name": u[1], "email": u[2]} for u in users])

# FIX 2: Authorization check — IDOR fixed
@app.route("/users/<int:user_id>")
@require_auth
def get_user(user_id):
    # Only allow users to read their own record
    if user_id != g.user_id:
        return jsonify({"error": "Forbidden"}), 403
    conn = get_db()
    user = conn.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"id": user[0], "name": user[1], "email": user[2]})

if __name__ == "__main__":
    # FIX 4: debug=False in production
    app.run(debug=False, port=5000)
```

### Step 5: Write Tests

```python
# test_security.py
import pytest
from secure_api import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_sql_injection_blocked(client):
    """SQL injection should return empty results, not all users"""
    response = client.get(
        "/users/search?email=' OR '1'='1",
        headers={"Authorization": "Bearer valid_user_1_token"}
    )
    data = response.get_json()
    assert len(data) == 0  # No results for this SQL injection payload

def test_idor_blocked(client):
    """User 1 should not be able to read User 2's data"""
    response = client.get(
        "/users/2",
        headers={"Authorization": "Bearer valid_user_1_token"}
    )
    assert response.status_code == 403

def test_auth_required(client):
    """Endpoints require authentication"""
    response = client.get("/users/1")
    assert response.status_code == 401
```

### Step 6: Wire Into GitHub Actions

```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Semgrep
        run: |
          pip install semgrep
          semgrep --config p/python --config p/owasp-top-ten \
            --json --output semgrep.json \
            --error   # exit non-zero if findings
        
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: semgrep-results
          path: semgrep.json

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dependencies
        run: pip install flask pytest
      
      - name: Run security tests
        env:
          API_SECRET: test-secret-for-ci
        run: pytest test_security.py -v
```

### Portfolio Output

1. Vulnerable API code with vulnerability comments
2. Semgrep scan results (screenshot or JSON)
3. Secure API code with fixes explained
4. Security test file
5. GitHub Actions workflow
6. Short writeup: "I built a Flask API with 4 common vulnerabilities, identified them with Semgrep, manually confirmed exploitability, fixed them, and added automated tests to prevent regression"

---

## 10.5 Lab 3: DAST with OWASP ZAP

**Time:** 2–3 hours  
**Skill:** Running DAST against your own application

### Setup

Use the vulnerable Flask API from Lab 2 (run the `vulnerable_api.py` version).

### Step 1: ZAP Baseline Scan

```bash
# Pull ZAP Docker image
docker pull zaproxy/zap-stable

# Run baseline scan (passive scan only — no attacks)
docker run --network host zaproxy/zap-stable \
  zap-baseline.py \
  -t http://localhost:5000 \
  -r zap-baseline-report.html \
  -J zap-baseline-report.json
```

### Step 2: ZAP Full Scan (Active Attacks)

```bash
# Run full scan (active attacks — use only against your own app)
docker run --network host zaproxy/zap-stable \
  zap-full-scan.py \
  -t http://localhost:5000 \
  -r zap-full-report.html \
  -J zap-full-report.json
```

### Step 3: ZAP API Scan

Create an OpenAPI spec for your API (`openapi.yaml`):

```yaml
openapi: 3.0.0
info:
  title: Demo API
  version: 1.0.0
paths:
  /users/search:
    get:
      parameters:
        - name: email
          in: query
          schema:
            type: string
      responses:
        '200':
          description: User list
  /users/{user_id}:
    get:
      parameters:
        - name: user_id
          in: path
          schema:
            type: integer
      responses:
        '200':
          description: User details
```

```bash
docker run --network host zaproxy/zap-stable \
  zap-api-scan.py \
  -t http://localhost:5000/openapi.yaml \
  -f openapi \
  -r zap-api-report.html
```

### Step 4: Analyze and Document Findings

Open `zap-full-report.html` and for each finding:
- Risk level (High/Medium/Low/Informational)
- Description of the vulnerability
- Request/response that demonstrates it
- Recommended fix

### Portfolio Output

- ZAP scan reports (HTML)
- Written analysis of 3–5 findings
- Before/after: "ZAP found X findings on the vulnerable app; after fixes, only Y informational findings remain"

---

## 10.6 Lab 4: Secure CI/CD Pipeline

**Time:** 3–4 hours  
**Skill:** Building a production-grade DevSecOps pipeline

### Goal

Build a GitHub Actions pipeline that includes:
- SAST (Semgrep)
- SCA (Trivy)
- Secret scanning (Gitleaks)
- Container scanning (Trivy image)
- DAST (ZAP baseline)

### Complete Pipeline File

```yaml
# .github/workflows/devsecops.yml
name: DevSecOps Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  # 1. Secret Scanning
  secrets-scan:
    name: Secret Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
        with:
          fetch-depth: 0  # Full history for Gitleaks
      
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # 2. SAST
  sast:
    name: Static Analysis (Semgrep)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/owasp-top-ten
            p/python
            p/secrets
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}

  # 3. SCA — Dependency Scanning
  sca:
    name: Dependency Scanning (Trivy)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      
      - name: Run Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-fs.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-fs.sarif

  # 4. Container Build + Scan
  container:
    name: Container Build and Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      
      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .
      
      - name: Scan container image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-image.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
      
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-image.sarif

  # 5. DAST (only on push to main, after deploy to staging)
  dast:
    name: DAST (ZAP Baseline)
    runs-on: ubuntu-latest
    needs: [sast, sca]  # Only run if SAST and SCA pass
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      
      - name: Start application
        run: |
          pip install flask
          API_SECRET=test python secure_api.py &
          sleep 5  # Wait for startup
      
      - name: ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: 'http://localhost:5000'
          fail_action: true
```

### Portfolio Output

- The complete `.github/workflows/devsecops.yml` file
- Screenshot of the pipeline running in GitHub Actions
- A PR where the pipeline caught a real finding (try committing a hardcoded secret)
- Short writeup explaining each stage and why it is in that position in the pipeline

---

## 10.7 Lab 5: Threat Model a Real System

**Time:** 2–3 hours  
**Skill:** Threat modeling — the most important AppSec skill

### Scenario

Threat model a simple e-commerce system:
- Users can browse products and add to cart
- Users can check out with credit card
- Admins can manage inventory and view orders

### Step 1: Draw the Data Flow Diagram

```
[User Browser] ──HTTPS──▶ [Load Balancer] ──HTTP──▶ [Web Application]
                                                           │
                                              ┌────────────┼────────────┐
                                              ▼            ▼            ▼
                                         [PostgreSQL]  [Redis       [Stripe
                                         (users,        Cache]       API]
                                          orders,       (sessions)
                                          products)
                                              │
                                         [Admin Panel]
                                         (separate app,
                                          separate creds)
```

### Step 2: Apply STRIDE to Each Component

Create a table:

| Component/Flow | S (Spoofing) | T (Tampering) | R (Repudiation) | I (Info Disclosure) | D (DoS) | E (Priv Escalation) |
|---|---|---|---|---|---|---|
| Login endpoint | Brute force password | — | No auth logs | — | Rate limiting needed | Bypass auth |
| HTTPS traffic | — | MITM if TLS weak | — | Intercept traffic | — | — |
| Session cookie | Cookie theft (XSS) | Modify session data | — | — | — | Change user_id in cookie |
| Order API | IDOR (other user's order) | Price manipulation | No order audit log | Order details exposure | Mass order creation | User → Admin |
| Stripe integration | — | Tamper price before sending | — | Card data in logs? | — | — |
| Admin panel | Brute force admin login | — | — | Admin functions exposed | — | Regular user → Admin |

### Step 3: Write Security Requirements

For each threat, write a security requirement:

```
From: Session cookie spoofing threat
Requirement: Session cookies MUST be marked HttpOnly, Secure, and SameSite=Strict.
             JWTs MUST be validated server-side for signature and expiry.
             Session IDs MUST be regenerated after login.

From: Price manipulation threat
Requirement: Price MUST be read from the database at checkout time, not trusted
             from client-side request parameters. Any price discrepancy > 1% 
             MUST trigger a fraud alert.

From: No order audit log threat
Requirement: All order creation, modification, and cancellation events MUST be
             logged with: user_id, timestamp, action, before_state, after_state.
             Logs MUST be immutable (append-only).

From: IDOR in order API threat
Requirement: All order API endpoints MUST verify that the authenticated user's
             ID matches the order's user_id before returning data.
```

### Portfolio Output

- Data flow diagram (can be hand-drawn and photographed, or made with draw.io, Mermaid, or Lucidchart)
- Completed STRIDE table
- Security requirements document (5–10 requirements)
- 1-paragraph summary: "I threat modeled an e-commerce system. The highest-risk threats I identified were X and Y because... The security controls I recommended are..."

---

## 10.8 Lab 6: Cloud Security Configuration Review

**Time:** 2–3 hours (requires AWS Free Tier account)  
**Skill:** Cloud security configuration review

### Setup

If you do not have an AWS account: use the [Prowler playground](https://github.com/prowler-cloud/prowler) which can run against a demo environment.

### Step 1: Run Prowler Against Your AWS Account

```bash
# Install Prowler
pip install prowler

# Configure AWS credentials (use a read-only IAM role!)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Run CIS AWS benchmark checks
prowler aws --compliance cis_aws_3.0
```

### Step 2: Run AWS Security Hub

In the AWS Console:
1. Go to Security Hub → Enable Security Hub
2. Enable AWS Foundational Security Best Practices standard
3. Wait 24 hours for initial assessment
4. Review failed controls

### Step 3: Interpret and Prioritize Findings

For each High/Critical finding:
1. What is the finding?
2. What is the risk if not fixed?
3. How difficult is the fix?
4. Priority (risk × effort)?

### Step 4: Fix One Finding

Pick a simple finding (like "MFA not enabled on root account" or "CloudTrail not enabled in all regions") and fix it. Document:
- Before state (screenshot of finding)
- Change made
- After state (finding resolved or re-scan showing green)

### Portfolio Output

- Prowler or Security Hub scan results (screenshot)
- Written analysis of top 5 findings
- One finding fixed with before/after evidence
- Prioritization rationale for the other findings

---

## 10.9 Building Your Portfolio

### What to Show in Interviews

The best portfolio artifacts for an AppSec engineer role:

1. **A vulnerable-then-secured application** (Lab 2) — shows you understand vulnerabilities from both attacker and defender perspective

2. **A CI/CD security pipeline** (Lab 4) — shows you can build automation, not just run tools manually

3. **A threat model** (Lab 5) — shows you can think at the design level, not just find code bugs

4. **Vulnerability reports** (Labs 1, 3) — shows you can communicate findings clearly

5. **A cloud security review** (Lab 6) — shows cloud fluency

### How to Document Your Labs

For each lab, write a short README:

```markdown
## Lab: SQL Injection — From Exploit to Fix

**What I did:** Built a vulnerable Flask API, identified SQL injection with
Semgrep, manually confirmed exploitability, fixed with parameterized queries,
added regression tests, and wired SAST into GitHub Actions.

**What I learned:** SAST caught the SQL injection in seconds. The manual 
exploit confirmed that the vulnerability was real and demonstrated the blast
radius (all user records readable). The fix was a 2-line change but required
understanding why parameterized queries are safe (DB treats input as data, 
not code).

**Tools used:** Python/Flask, Semgrep, SQLite, GitHub Actions

**Key finding:**
[screenshot of Semgrep finding]

**Fix:**
[code diff showing the fix]

**Verified:**
[Semgrep scan passing after fix]
```

---

## Chapter 10 Summary

| Lab | Skills Demonstrated |
|---|---|
| Lab 1: Juice Shop | OWASP Top 10 exploitation, vulnerability report writing |
| Lab 2: Vulnerable API | Build-exploit-fix cycle, SAST integration, security testing |
| Lab 3: DAST with ZAP | Dynamic testing, DAST report interpretation |
| Lab 4: CI/CD Pipeline | DevSecOps automation, pipeline design, GitHub Actions |
| Lab 5: Threat Model | Design-level security thinking, STRIDE, security requirements |
| Lab 6: Cloud Review | Cloud security configuration, Prowler, Security Hub |

**Remember:** What matters is not just running the tools, but being able to explain:
- What did you find and why is it a risk?
- How did you fix it and why does the fix work?
- How do you prevent it from coming back?

These three questions cover every vulnerability question in an AppSec interview.

---

*Next: [Chapter 11 — Learning Progression & Career Map](11-Learning-Progression.md)*
