# Vulnerable App Scan Lab

Practice scanning OWASP Juice Shop, DVWA, and WebGoat using the same scanner stack
(ZAP DAST + Trivy) wired into the main AISec pipeline.

**These apps are intentionally broken. Every finding is expected. The goal is to read
scanner output, not fix it.**

---

## What's in here

| File | Purpose |
|---|---|
| `docker-compose.yml` | Pulls and runs all 3 vulnerable apps as containers |
| `Jenkinsfile-vuln-scan` | 7-stage Jenkins pipeline: start → scan 3×ZAP → scan 3×Trivy → summarize → stop |
| `zap/juice-shop.conf` | ZAP rule config for Juice Shop (all WARN, never FAIL) |
| `zap/dvwa.conf` | ZAP rule config for DVWA |
| `zap/webgoat.conf` | ZAP rule config for WebGoat |

---

## The three apps

### OWASP Juice Shop (port 3000)
A modern Node.js e-commerce app with 100+ intentional vulnerabilities covering
all OWASP Top 10 (2021) categories plus more. The most realistic of the three —
it looks and feels like a real shopping site. Every vulnerability is a puzzle you
can also solve manually through the app's built-in score board.

**Common ZAP alerts:** Missing security headers (CSP, X-Frame-Options, HSTS),
open redirects, JWT manipulation, reflected XSS, broken access control.

**Common Trivy CVEs:** Outdated npm packages (prototype pollution, ReDoS, path traversal).

Learn more: [OWASP Juice Shop Companion Guide](https://pwning.owasp-juice.shop/)

---

### DVWA — Damn Vulnerable Web Application (port 4280)
A PHP/MySQL app built purely to demonstrate classic web vulnerabilities. Has
adjustable security levels (low/medium/high/impossible) — starts on "low" by default,
which means all vulnerabilities are fully exploitable.

**Common ZAP alerts:** Anti-CSRF token missing, weak auth (HTTP Basic), no HSTS,
missing security headers.

**Common Trivy CVEs:** Old PHP version + OS packages in the base image.

Learn more: [DVWA GitHub](https://github.com/digininja/DVWA)

---

### WebGoat (port 8080, path /WebGoat)
A Java/Spring app structured as guided lessons. Unlike Juice Shop and DVWA,
WebGoat teaches you the vulnerability *and* asks you to exploit it as an exercise.
Covers injection, broken auth, sensitive data exposure, XXE, insecure deserialization.

**Common ZAP alerts:** Missing security headers, weak TLS config, session management issues.

**Common Trivy CVEs:** Outdated Java libraries (Spring, Log4j historically, etc.).

Learn more: [WebGoat GitHub](https://github.com/WebGoat/WebGoat)

---

## Run locally (no Jenkins)

```bash
# Start all 3 apps
docker compose -f thirdparty_app_scan/docker-compose.yml up -d

# Check they're up
curl http://localhost:3000        # Juice Shop
curl http://localhost:4280        # DVWA
curl http://localhost:8080/WebGoat  # WebGoat

# Stop when done
docker compose -f thirdparty_app_scan/docker-compose.yml down
```

---

## Run in Jenkins

1. In Jenkins → **New Item** → Pipeline → name it `vuln-app-scan-lab`
2. Under Pipeline → Definition: **Pipeline script from SCM**
3. SCM: Git, Repository URL: your repo
4. Script Path: `thirdparty_app_scan/Jenkinsfile-vuln-scan`
5. Save → **Build Now**

The pipeline takes ~20–30 min (ZAP baseline is slow).
When done, click **Build Artifacts** to see all SARIF files and HTML reports.

---

## How to read the results

### HTML reports (ZAP)
Open `juice-shop-zap-report.html` in a browser. Each alert shows:
- **Alert name** — the vulnerability class (e.g., "Content Security Policy Not Set")
- **Risk** — High / Medium / Low / Informational
- **URL** — which endpoint triggered it
- **Evidence** — the actual response header or body that triggered the alert
- **Solution** — what a developer should do to fix it

### SARIF files (both ZAP and Trivy)
Machine-readable JSON used by GitHub Security tab and other tools.
Open with any JSON viewer or the VS Code SARIF viewer extension.
Structure: `runs[0].results[]` — each result is one finding with:
- `ruleId` — the rule that fired
- `level` — "error" (critical/high) or "warning"
- `message.text` — description
- `locations[]` — where in the target it was found

---

## Why no Security Gate?

The main `Jenkinsfile-cicd` has a Security Gate (Stage 12) that fails the build
on unacknowledged CRITICAL findings. This pipeline deliberately has no gate because:

1. These apps are *supposed* to have hundreds of findings — a gate would always fail
2. The point is to practice *reading* scanner output, not to enforce a clean baseline
3. Findings here don't represent your codebase — they're controlled learning material

---

## Mapping findings to OWASP Top 10 (2021)

| ZAP Alert | OWASP Top 10 Category |
|---|---|
| Cross-Site Scripting | A03:2021 — Injection |
| SQL Injection | A03:2021 — Injection |
| Missing CSRF Tokens | A01:2021 — Broken Access Control |
| Broken Auth / Weak Session | A07:2021 — Identification & Authentication Failures |
| Missing Security Headers | A05:2021 — Security Misconfiguration |
| Sensitive Data in URL | A02:2021 — Cryptographic Failures |
| Open Redirect | A01:2021 — Broken Access Control |
| Outdated Libraries (Trivy) | A06:2021 — Vulnerable & Outdated Components |
