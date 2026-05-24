# AISec + Pursh — Complete Manual Scan Guide

> Run any scanner three ways: **local (PowerShell)**, **Jenkins pipeline**, or **direct SSH on the build agent**.
> Start here when you want to test a single scanner without triggering a full pipeline run.

---

## Before you start — one-time setup

```powershell
# 1. Go to the project root (all commands assume you are here)
cd C:\Users\prabh\Downloads\ci_cd_seclab

# 2. Create the local output folder if it does not exist
New-Item -ItemType Directory -Force -Path scan-results

# 3. Confirm Docker is running
docker info | Select-String "Server Version"

# 4. Confirm tools are available
semgrep --version
trivy --version
.\scanners\gitleaks-bin\gitleaks.exe version
.\scanners\grype-bin\grype.exe version
```

---

## Scanner Index

| # | Scanner | Category | Local command prefix | Jenkins stage | SSH on agent |
|---|---|---|---|---|---|
| 1 | Semgrep | SAST | `semgrep` | `SAST — Semgrep` | `/usr/local/bin/semgrep` |
| 2 | Trivy FS | SCA | `trivy fs` | `SCA — Trivy FS` | `/usr/local/bin/trivy fs` |
| 3 | Gitleaks | Secrets | `.\scanners\gitleaks-bin\gitleaks.exe` | `Secrets — Gitleaks` | `docker run zricethezav/gitleaks` |
| 4 | Syft | SBOM | `syft` | (GitHub Actions sbom.yml) | `syft` |
| 5 | Grype | SCA (SBOM) | `.\scanners\grype-bin\grype.exe` | (GitHub Actions sbom.yml) | `grype` |
| 6 | Checkov | IaC | `checkov` | (GitHub Actions ci.yml) | `checkov` |
| 7 | Trivy Image | Container | `trivy image` | `Image Scan — Trivy` | `/usr/local/bin/trivy image` |
| 8 | ZAP | DAST | `docker run ghcr.io/zaproxy/zaproxy` | `DAST — ZAP Baseline` | `docker run ghcr.io/zaproxy/zaproxy` |
| 9 | SonarQube | Code Quality | `docker run sonar-scanner-cli` | `SonarQube Analysis` | `docker run sonar-scanner-cli` |

---

---

## 1 — SAST: Semgrep

### What it finds
Security bugs in Python source code: SQL injection, hardcoded secrets, insecure deserialization,
broken auth patterns, OWASP Top 10 violations.

---

### Local (PowerShell)

```powershell
# Quick scan — results printed to terminal
semgrep --config p/python --config p/security-audit --config p/owasp-top-ten `
  aisec/ pursh/

# Save as SARIF (same format as Jenkins archives)
semgrep --config p/python --config p/security-audit `
  --sarif --output scan-results\semgrep.sarif `
  aisec/ pursh/

# Read the SARIF — show rule IDs and file locations
Get-Content scan-results\semgrep.sarif | python -m json.tool | `
  Select-String "ruleId|uri|startLine" | Select-Object -First 40

# Also run the custom rules for this repo (PHI-SAFE, Supabase keys)
semgrep --config scanners\semgrep\custom-rules.yaml `
  aisec/ pursh/
```

**What you will see:**
```
Running 847 rules...
Findings:
  pursh/backend/api/patients.py:42: python.lang.security.audit.formatted-sql-query
  Severity: ERROR  CWE: CWE-89 SQL Injection
  ...
Ran 847 rules on 34 files: 2 findings.
```

---

### Jenkins pipeline
Runs automatically in the **`SAST — Semgrep`** stage.
To re-run only this stage: Jenkins → Build → Stage View → right-click `SAST — Semgrep` → (not available in declarative) → trigger full build.
To trigger a full build: **Build Now** in the Jenkins job.

SARIF is archived at: `Jenkins job → Build #N → Artifacts → semgrep.sarif`

---

### SSH on build agent (EC2)

```bash
# SSH in first
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

# Navigate to the workspace (adjust build number)
cd /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline

# Run exactly as Jenkins does
/usr/local/bin/semgrep \
  --config p/python \
  --config p/security-audit \
  --sarif --output semgrep.sarif \
  --timeout 300 \
  pursh/ aisec/

# View findings
cat semgrep.sarif | python3 -m json.tool | grep -E "ruleId|uri|startLine" | head -40
```

---

---

## 2 — SCA: Trivy Filesystem

### What it finds
Known CVEs in Python packages (`requirements.txt`), Node packages, OS packages.
Checks against NVD, GitHub Advisory, OSV databases.

---

### Local (PowerShell)

```powershell
# Human-readable table — CRITICAL and HIGH only
trivy fs --severity CRITICAL,HIGH aisec/
trivy fs --severity CRITICAL,HIGH pursh/

# Include MEDIUM
trivy fs --severity CRITICAL,HIGH,MEDIUM aisec/ pursh/

# Only fixable CVEs (same as pipeline)
trivy fs --severity CRITICAL,HIGH --ignore-unfixed aisec/ pursh/

# Save as SARIF
trivy fs --severity CRITICAL,HIGH `
  --format sarif `
  --output scan-results\trivy-fs.sarif `
  --ignore-unfixed `
  aisec/ pursh/

# Read the SARIF
Get-Content scan-results\trivy-fs.sarif | python -m json.tool | `
  Select-String "ruleId|level|text" | Select-Object -First 30
```

**What you will see:**
```
aisec/requirements.txt (pip)
┌─────────────────┬────────────────┬──────────┬────────────────────┬──────────────┐
│ Library         │ Vulnerability  │ Severity │ Installed Version  │ Fixed Version│
├─────────────────┼────────────────┼──────────┼────────────────────┼──────────────┤
│ cryptography    │ CVE-2024-XXXXX │ HIGH     │ 41.0.3             │ 41.0.6       │
└─────────────────┴────────────────┴──────────┴────────────────────┴──────────────┘
```

---

### Jenkins pipeline
Runs in the **`SCA — Trivy FS`** stage.
SARIF archived at: `Build #N → Artifacts → trivy-fs.sarif`

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66
cd /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline

/usr/local/bin/trivy fs . \
  --severity CRITICAL,HIGH \
  --format sarif \
  --output trivy-fs.sarif \
  --ignore-unfixed \
  --exit-code 0

# View as table instead
/usr/local/bin/trivy fs . --severity CRITICAL,HIGH --ignore-unfixed
```

---

---

## 3 — Secrets: Gitleaks

### What it finds
Hardcoded API keys, passwords, tokens, connection strings in source code AND git history.
Custom rules for Supabase keys, AWS keys, DeepSeek keys, Postgres DSNs.

---

### Local (PowerShell)

```powershell
$gitleaks = ".\scanners\gitleaks-bin\gitleaks.exe"

# Scan current working tree (no git history)
& $gitleaks detect --source . `
  --config scanners\gitleaks\.gitleaks.toml `
  --verbose --no-git

# Scan full git history (slower, catches committed-then-deleted secrets)
& $gitleaks detect --source . `
  --config scanners\gitleaks\.gitleaks.toml `
  --verbose

# Save as SARIF
& $gitleaks detect --source . `
  --config scanners\gitleaks\.gitleaks.toml `
  --report-format sarif `
  --report-path scan-results\gitleaks.sarif `
  --no-git

# Read SARIF
Get-Content scan-results\gitleaks.sarif | python -m json.tool | `
  Select-String "ruleId|text|uri" | Select-Object -First 20
```

**What you will see (if clean):**
```
INF detecting...
INF scan completed in 1.2s
INF no leaks found
```

**What you will see (if a secret is found):**
```
RuleID:     supabase-service-role-key
File:       pursh/backend/config.py
Line:       14
Match:      eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Severity:   critical
```

---

### Jenkins pipeline
Runs in the **`Secrets — Gitleaks`** stage via Docker container.
SARIF archived at: `Build #N → Artifacts → gitleaks.sarif`

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66
cd /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline

# Exactly as Jenkins runs it
docker run --rm \
  -v "$(pwd):/repo" \
  -v "$(pwd)/scanners/gitleaks/.gitleaks.toml:/config/.gitleaks.toml" \
  zricethezav/gitleaks:latest \
  detect \
  --source=/repo \
  --config=/config/.gitleaks.toml \
  --report-format=sarif \
  --report-path=/repo/gitleaks.sarif \
  --no-git

cat gitleaks.sarif | python3 -m json.tool | grep -E "ruleId|text|uri" | head -20
```

---

---

## 4 — SBOM: Syft

### What it finds
Not vulnerabilities — generates a Software Bill of Materials (inventory of every
package in the project). The SBOM is then fed to Grype for CVE scanning.

---

### Local (PowerShell)

```powershell
# Install syft if not present
# winget install anchore.syft   OR   scoop install syft

# Generate SBOM as a readable table
syft aisec/ --output table
syft pursh/ --output table

# Generate machine-readable SBOM files (CycloneDX + SPDX)
syft aisec/ --output cyclonedx-json=scan-results\aisec.cyclonedx.json
syft aisec/ --output spdx-json=scan-results\aisec.spdx.json

syft pursh/ --output cyclonedx-json=scan-results\pursh.cyclonedx.json
syft pursh/ --output spdx-json=scan-results\pursh.spdx.json

# Count components
(Get-Content scan-results\aisec.cyclonedx.json | `
  python -m json.tool | Select-String '"name"').Count
```

**What you will see:**
```
NAME                    VERSION    TYPE
fastapi                 0.111.0    python
pydantic                2.7.1      python
sqlalchemy              2.0.30     python
uvicorn                 0.29.0     python
... (all dependencies)
```

---

### Jenkins pipeline
Runs in the GitHub Actions **`sbom.yml`** workflow (scheduled weekly, not in Jenkins).
To trigger manually: GitHub → Actions → `SBOM Generation` → Run workflow.

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

# Install syft if not present on agent
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | \
  sudo sh -s -- -b /usr/local/bin

syft /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline/aisec \
  --output cyclonedx-json=aisec.cyclonedx.json

syft /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline/pursh \
  --output cyclonedx-json=pursh.cyclonedx.json
```

---

---

## 5 — SCA (SBOM): Grype

### What it finds
CVEs in the SBOM generated by Syft. Cross-validates Trivy's results using
Grype's own vulnerability database (Anchore). Run Syft first (step 4).

---

### Local (PowerShell)

```powershell
$grype = ".\scanners\grype-bin\grype.exe"

# Scan the SBOM files generated in step 4
& $grype "sbom:scan-results\aisec.cyclonedx.json" --output table
& $grype "sbom:scan-results\pursh.cyclonedx.json" --output table

# Only HIGH and CRITICAL
& $grype "sbom:scan-results\aisec.cyclonedx.json" `
  --fail-on high `
  --output table

# Save as SARIF
& $grype "sbom:scan-results\aisec.cyclonedx.json" `
  --output sarif `
  --file scan-results\grype.sarif
```

**What you will see:**
```
NAME          INSTALLED  FIXED-IN  TYPE    VULNERABILITY   SEVERITY
cryptography  41.0.3     41.0.6    python  CVE-2024-XXXXX  High
```

---

### Jenkins pipeline
Runs in the GitHub Actions **`sbom.yml`** workflow alongside Syft.

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

# Install grype if not present
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | \
  sudo sh -s -- -b /usr/local/bin

grype sbom:aisec.cyclonedx.json --output table
grype sbom:pursh.cyclonedx.json --output table
```

---

---

## 6 — IaC: Checkov

### What it finds
Misconfigurations in Terraform files: public S3 buckets, unencrypted resources,
missing IAM least-privilege, no MFA on root account, missing CloudTrail.

---

### Local (PowerShell)

```powershell
# Install if not present
pip install checkov

# Scan all Terraform
checkov --directory infra\terraform --framework terraform

# Only HIGH and CRITICAL
checkov --directory infra\terraform --framework terraform `
  --check CKV_AWS_*

# Save as SARIF
checkov --directory infra\terraform --framework terraform `
  --output sarif `
  --output-file-path scan-results\checkov.sarif

# Soft fail (don't exit 1 on findings — just report)
checkov --directory infra\terraform --soft-fail
```

**What you will see:**
```
Check: CKV_AWS_19: "Ensure all data stored in the S3 bucket is securely encrypted"
  FAILED for resource: aws_s3_bucket.aisec_artifacts
  File: /infra/terraform/aisec/s3.tf:12-25
```

---

### Jenkins pipeline
Runs in the GitHub Actions **`ci.yml`** workflow in the `iac-scan` job.
Not wired into Jenkins directly (IaC is not deployed from Jenkins in this setup).

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

cd /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline

pip3 install checkov

checkov --directory infra/terraform --framework terraform --output sarif \
  --output-file-path checkov.sarif --soft-fail

cat checkov.sarif | python3 -m json.tool | grep -E "ruleId|level|text" | head -30
```

---

---

## 7 — Container: Trivy Image

### What it finds
CVEs in the Docker image layers — OS packages (Debian/Alpine), Python packages
inside the image, language runtimes. Runs after `docker build`.

---

### Local (PowerShell)

```powershell
# Build the image first
docker build -t aisec:local -f aisec\Dockerfile aisec\

# Scan the built image
trivy image --severity CRITICAL,HIGH aisec:local

# With .trivyignore (same as pipeline — accepted CVEs excluded)
trivy image --severity CRITICAL,HIGH `
  --ignore-unfixed `
  --ignorefile scanners\trivy\.trivyignore `
  aisec:local

# Save as SARIF
trivy image --severity CRITICAL,HIGH `
  --format sarif `
  --output scan-results\trivy-image.sarif `
  --ignore-unfixed `
  --ignorefile scanners\trivy\.trivyignore `
  aisec:local

# Human-readable summary only
trivy image --severity CRITICAL,HIGH `
  --format table `
  --ignore-unfixed `
  aisec:local
```

**What you will see:**
```
aisec:local (debian 12.6)
┌──────────────┬────────────────┬──────────┬───────────────────┬──────────────┐
│ Library      │ Vulnerability  │ Severity │ Installed Version │ Fixed Version│
└──────────────┴────────────────┴──────────┴───────────────────┴──────────────┘
Total: 0 (CRITICAL: 0, HIGH: 0)   ← after .trivyignore applied
```

---

### Jenkins pipeline
Runs in the **`Image Scan — Trivy`** stage after `Build Images`.
SARIF archived at: `Build #N → Artifacts → trivy-aisec-image.sarif`

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

SHORT_SHA=$(git -C /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline \
  rev-parse --short HEAD)

/usr/local/bin/trivy image \
  --severity CRITICAL,HIGH \
  --format sarif \
  --output trivy-aisec-image.sarif \
  --exit-code 0 \
  --ignore-unfixed \
  --ignorefile /home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline/scanners/trivy/.trivyignore \
  ghcr.io/prabhudasuj23/aisec:${SHORT_SHA}

cat trivy-aisec-image.sarif | python3 -m json.tool | \
  grep -E '"level"|"ruleId"|"text"' | head -30
```

---

---

## 8 — DAST: ZAP Baseline

### What it finds
Runtime vulnerabilities in the live running application: missing security headers,
XSS, CSRF, injection surfaces, insecure cookies, information disclosure.
ZAP talks to the app over HTTP — it finds things SAST cannot.

---

### Local (PowerShell) — Step by step

**Step 1 — Start the AISec app**

```powershell
# Terminal 1 — keep this open the whole time
cd C:\Users\prabh\Downloads\ci_cd_seclab\aisec

$env:SUPABASE_URL          = "https://placeholder.supabase.co"
$env:SUPABASE_ANON_KEY     = "placeholder"
$env:SUPABASE_JWT_SECRET   = "placeholder-32-chars-minimum-here"
$env:DATABASE_URL          = "postgresql+asyncpg://test:test@localhost:5432/test"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8090
```

You should see:
```
INFO:     Started server process [XXXX]
INFO:     Uvicorn running on http://0.0.0.0:8090
```

**Step 2 — Verify the app is up**

```powershell
# Terminal 2 — new window
Invoke-WebRequest -Uri "http://localhost:8090/healthz" | Select-Object StatusCode, Content
# Expected: StatusCode=200, Content={"status":"ok","service":"aisec"}
```

**Step 3 — Run ZAP**

```powershell
# Terminal 2 — run ZAP against the live app
$out = "$PWD\scan-results"
New-Item -ItemType Directory -Force -Path $out

docker run --rm `
  -v "${out}:/zap/wrk/:rw" `
  -v "${PWD}\scanners\zap\zap-baseline.conf:/zap/wrk/zap-baseline.conf:ro" `
  ghcr.io/zaproxy/zaproxy:stable `
  zap-baseline.py `
    -t "http://host.docker.internal:8090" `
    -c "/zap/wrk/zap-baseline.conf" `
    -J "zap-report.json" `
    -r "zap-report.html" `
    -I
```

**Step 4 — View results**

```powershell
# Open the HTML report in your browser (nicely formatted, clickable)
Start-Process "scan-results\zap-report.html"

# Or read the JSON
Get-Content scan-results\zap-report.json | python -m json.tool | `
  Select-String "alert|risk|confidence|url" | Select-Object -First 40
```

**What you will see during the scan:**
```
PASS: Cookie No HttpOnly Flag [10010]
WARN: X-Content-Type-Options Header Missing [10021]
PASS: SQL Injection [40018]
PASS: Remote OS Command Injection [90020]
...
WARN: 3   FAIL: 0
```

**Step 5 — Stop the app when done**
```powershell
# Terminal 1 — press Ctrl+C
```

---

### Jenkins pipeline
Runs in the **`DAST — ZAP Baseline`** stage.
The smoke test keeps the container running; ZAP scans it; container is removed after.
Reports archived at: `Build #N → Artifacts → zap.sarif` and `zap-report.html`

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

WORKSPACE=/home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline

# Start the AISec container
docker run -d --name zap-target \
  -p 8090:8000 \
  -e SUPABASE_URL="https://placeholder.supabase.co" \
  -e SUPABASE_ANON_KEY="placeholder" \
  -e SUPABASE_JWT_SECRET="placeholder-32-chars-minimum-here" \
  -e DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test" \
  ghcr.io/prabhudasuj23/aisec:latest

# Wait for health check
sleep 15
curl -s http://localhost:8090/healthz

# Run ZAP
docker run --rm \
  --network host \
  -v "${WORKSPACE}:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
    -t "http://localhost:8090" \
    -c "/zap/wrk/scanners/zap/zap-baseline.conf" \
    -J "/zap/wrk/zap.sarif" \
    -r "/zap/wrk/zap-report.html" \
    -I

# Read results
cat ${WORKSPACE}/zap.sarif | python3 -m json.tool | \
  grep -E '"level"|"ruleId"|"text"' | head -30

# Stop the target container
docker rm -f zap-target
```

---

---

## 9 — Code Quality: SonarQube

### What it finds
Code smells, duplicated code, test coverage gaps, security hotspots.
Complements Semgrep with a full code-quality picture.

---

### Local (PowerShell)

```powershell
# SonarQube server is already running on the EC2
# Replace YOUR_TOKEN with a token from http://3.14.146.228:9000
$SONAR_TOKEN = "YOUR_TOKEN_HERE"

docker run --rm `
  -v "${PWD}:/usr/src" `
  sonarsource/sonar-scanner-cli:latest `
  -Dsonar.projectKey=aisec_pursh `
  -Dsonar.sources=aisec/app,pursh/backend `
  -Dsonar.host.url=http://3.14.146.228:9000 `
  -Dsonar.token=$SONAR_TOKEN
```

Then open: http://3.14.146.228:9000/dashboard?id=aisec_pursh

---

### Jenkins pipeline
Runs in the **`SonarQube Analysis`** stage using the `sonar-token` Jenkins credential.

---

### SSH on build agent

```bash
ssh -i ~/Downloads/devsecops-lab.pem ubuntu@3.128.18.66

WORKSPACE=/home/ubuntu/jenkins-agent/workspace/aisec-devsecops-pipeline

# Get token from Jenkins credential store or SonarQube UI
SONAR_TOKEN="your-sonar-token"

docker run --rm \
  -v "${WORKSPACE}:/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.projectKey=aisec_pursh \
  -Dsonar.sources=aisec/app,pursh/backend \
  -Dsonar.host.url=http://3.14.146.228:9000 \
  -Dsonar.token=${SONAR_TOKEN}
```

---

---

## Run all scanners in sequence (local PowerShell)

Copy-paste this block to run every scanner end-to-end locally.
App must NOT be running yet (ZAP section starts it).

```powershell
cd C:\Users\prabh\Downloads\ci_cd_seclab
New-Item -ItemType Directory -Force -Path scan-results

Write-Host "=== 1/7 SAST — Semgrep ===" -ForegroundColor Cyan
semgrep --config p/python --config p/security-audit `
  --sarif --output scan-results\semgrep.sarif aisec/ pursh/

Write-Host "=== 2/7 SCA — Trivy FS ===" -ForegroundColor Cyan
trivy fs --severity CRITICAL,HIGH --ignore-unfixed `
  --format sarif --output scan-results\trivy-fs.sarif aisec/ pursh/

Write-Host "=== 3/7 Secrets — Gitleaks ===" -ForegroundColor Cyan
.\scanners\gitleaks-bin\gitleaks.exe detect --source . `
  --config scanners\gitleaks\.gitleaks.toml `
  --report-format sarif --report-path scan-results\gitleaks.sarif --no-git

Write-Host "=== 4/7 SBOM — Syft ===" -ForegroundColor Cyan
syft aisec/ --output cyclonedx-json=scan-results\aisec.cyclonedx.json
syft pursh/ --output cyclonedx-json=scan-results\pursh.cyclonedx.json

Write-Host "=== 5/7 SCA (SBOM) — Grype ===" -ForegroundColor Cyan
.\scanners\grype-bin\grype.exe sbom:scan-results\aisec.cyclonedx.json `
  --output sarif --file scan-results\grype.sarif

Write-Host "=== 6/7 Container — Trivy Image ===" -ForegroundColor Cyan
docker build -t aisec:local -f aisec\Dockerfile aisec\ --quiet
trivy image --severity CRITICAL,HIGH --ignore-unfixed `
  --ignorefile scanners\trivy\.trivyignore `
  --format sarif --output scan-results\trivy-image.sarif aisec:local

Write-Host "=== 7/7 DAST — ZAP ===" -ForegroundColor Cyan
Write-Host "Starting app in background..." -ForegroundColor Yellow
$app = Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList `
  "-Command `"cd aisec; `$env:SUPABASE_URL='https://placeholder.supabase.co'; `$env:SUPABASE_ANON_KEY='placeholder'; `$env:SUPABASE_JWT_SECRET='placeholder-32-chars-minimum-here'; `$env:DATABASE_URL='postgresql+asyncpg://test:test@localhost:5432/test'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8090`""
Start-Sleep 8

$out = "$PWD\scan-results"
docker run --rm `
  -v "${out}:/zap/wrk/:rw" `
  -v "${PWD}\scanners\zap\zap-baseline.conf:/zap/wrk/zap-baseline.conf:ro" `
  ghcr.io/zaproxy/zaproxy:stable `
  zap-baseline.py -t "http://host.docker.internal:8090" `
    -c "/zap/wrk/zap-baseline.conf" -J "zap-report.json" -r "zap-report.html" -I

Stop-Process -Id $app.Id -Force 2>$null

Write-Host ""
Write-Host "=== All scans complete. Results in scan-results\ ===" -ForegroundColor Green
Get-ChildItem scan-results\ | Select-Object Name, Length

# Open HTML reports
Start-Process "scan-results\zap-report.html"
```

---

## Quick reference card

| Scanner | Local quick command | Expected clean output |
|---|---|---|
| Semgrep | `semgrep --config p/python aisec/ pursh/` | `0 findings` |
| Trivy FS | `trivy fs --severity CRITICAL,HIGH aisec/` | `Total: 0` |
| Gitleaks | `.\scanners\gitleaks-bin\gitleaks.exe detect --source . --no-git` | `no leaks found` |
| Syft | `syft aisec/ --output table` | Package table |
| Grype | `.\scanners\grype-bin\grype.exe sbom:scan-results\aisec.cyclonedx.json` | `No vulnerabilities found` |
| Checkov | `checkov -d infra\terraform --soft-fail` | `Passed checks: N` |
| Trivy Image | `trivy image --severity CRITICAL,HIGH aisec:local` | `Total: 0` |
| ZAP | *(app must be running — see step 8)* | `WARN: N  FAIL: 0` |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `semgrep: command not found` | `pip install semgrep` |
| `trivy: command not found` | Download from https://github.com/aquasecurity/trivy/releases |
| `syft: command not found` | `winget install anchore.syft` or `scoop install syft` |
| ZAP shows HTTP 000 | App is not running — check Terminal 1 for errors |
| ZAP cannot reach `host.docker.internal` | Docker Desktop must be running; use `host.docker.internal` not `localhost` |
| Grype: `no SBOM file` | Run Syft first (step 4) to generate the `.cyclonedx.json` files |
| Trivy image: `image not found` | Run `docker build` first (step 7) |
| Jenkins build fails at DAST | Check that port 8000 is not already in use on the build agent |
