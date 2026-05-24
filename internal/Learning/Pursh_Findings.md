# Pursh Security Findings — Complete Scanner Reference

> End-to-end guide for every scanner built into AISec. Covers what it scans, how to run it, what files it uses, how results are stored, and where to view live output. Beginner to full execution.

---

## How the whole system fits together

```
You click "Run" in the Dashboard
          │
          ▼
Dashboard (Next.js :3002)
  → POST http://localhost:8002/stream/{scanner_id}   ← Runner API
          │
          ▼
Runner (FastAPI :8002) spawns subprocess
  → Scanner binary / Docker container / Python module
          │
          ▼
Scanner runs against Pursh code / infra / running app
          │
          ▼
Output captured → written to internal/scan-results/{file}
          │
          ▼
Runner normalizes findings → saves to Supabase (scan_runs table)
          │
          ▼
Dashboard reads from Supabase → RunHistoryPanel updates live via Realtime
```

---

## Starting everything (run in this order)

```powershell
# Terminal 1 — Runner API
cd internal\aisec\runner
uvicorn main:app --reload --port 8002

# Terminal 2 — Dashboard
cd internal\aisec\dashboard
npm run dev   # starts on :3002 by default

# Terminal 3 — (for DAST scanners only) Pursh frontend
cd pursh\frontend
npm run dev   # starts on :3000

# Terminal 4 — (for DAST scanners only) Pursh backend
cd pursh\backend
uvicorn main:app --port 8001
```

**Runner health check:**
```
GET http://localhost:8002/healthz
→ {"status": "ok"}
```

**Dashboard live URL:** [http://localhost:3002](http://localhost:3002)

---

## Key files quick reference

| File | Purpose |
|---|---|
| [internal/aisec/runner/main.py](../aisec/runner/main.py) | Runner API — all endpoints, normalizers, DeepSeek intelligence |
| [internal/aisec/runner/scanners.py](../aisec/runner/scanners.py) | All 28 scanner definitions — command, result file, type |
| [internal/aisec/runner/storage.py](../aisec/runner/storage.py) | Supabase storage adapter — circuit breaker, upsert, history |
| [internal/aisec/.env](../aisec/.env) | SUPABASE_URL, SUPABASE_JWT_SECRET, DEEPSEEK_API_KEY |
| [internal/aisec/supabase-schema.sql](../aisec/supabase-schema.sql) | SQL DDL to run in Supabase — creates scan_runs, ai_analyses, triage_notes |
| [internal/scan-results/](../scan-results/) | All scanner output JSON/XML files land here |
| [internal/aisec/dashboard/](../aisec/dashboard/) | Next.js dashboard source |
| [internal/scanners/semgrep/custom-rules.yaml](../scanners/semgrep/custom-rules.yaml) | Custom Semgrep rules for Pursh |
| [internal/scanners/gitleaks/.gitleaks.toml](../scanners/gitleaks/.gitleaks.toml) | Gitleaks allowlist and custom rules |
| [internal/infra/terraform/](../infra/terraform/) | Terraform configs that Checkov and tfsec scan |
| [pursh/](../../pursh/) | Target application — all scanners point here |

---

## Scanner Categories Overview

```
28 Scanners Total
├── SAST (Source Code)          semgrep
├── SCA (Dependencies)          trivy-sca, grype, dependency-check
├── Container Security          trivy-image
├── Secrets Detection           gitleaks, trufflehog, detect-secrets
├── SBOM                        syft
├── IaC Security                checkov, tfsec, kics
├── DAST (Running App)          zap, nikto, schemathesis, nuclei
├── Network Security            nmap, suricata, zeek, openvas
├── CloudSec (AWS) — stubs      prowler, scoutsuite, guardduty, inspector, macie, iam-access-analyzer
└── AI Security — stubs         promptfoo, garak
```

---

---

# SAST — Static Application Security Testing

---

## Scanner 1: Semgrep

**What it does:** Reads source code without running it. Finds injection, auth bugs, hardcoded secrets, insecure patterns using AST pattern matching + taint analysis.

**Target:** `pursh/` directory — all Python + JavaScript/TypeScript source files.

**Pre-checks:**
```powershell
semgrep --version   # must return a version number
```

**How to run (dashboard):**
1. Open [http://localhost:3002](http://localhost:3002)
2. Find "Semgrep (SAST)" card → click Pre-check → all green → click Run

**How to run (terminal):**
```powershell
semgrep scan `
  --config internal\scanners\semgrep\custom-rules.yaml `
  --config p/owasp-top-ten `
  pursh\ `
  --json > internal\scan-results\semgrep-pursh.json
```

**Result file:** [internal/scan-results/semgrep-pursh.json](../scan-results/semgrep-pursh.json)

**Runner API (test live):**
```
GET  http://localhost:8002/precheck/semgrep
GET  http://localhost:8002/stream/semgrep        ← SSE stream (open in browser for live output)
GET  http://localhost:8002/results/semgrep       ← normalized findings + Supabase data
GET  http://localhost:8002/intelligence/semgrep  ← DeepSeek AI analysis
```

**Output shape (normalized finding):**
```json
{
  "severity": "HIGH",
  "rule": "python.django.security.injection.sql-injection",
  "file": "pursh/backend/api/patients.py",
  "line": 47,
  "message": "SQL injection via string formatting",
  "cwe": "CWE-89",
  "fix": "Use parameterized queries or ORM"
}
```

**Normalizer in main.py:** `_norm_semgrep()` — reads `raw["results"]` array, maps `extra.severity`, `check_id`, `path`, `start.line`, `extra.message`, `extra.metadata.cwe`.

**How it stores to Supabase:**
- `start_run()` called when SSE stream opens → `status=running` row in `scan_runs`
- `finish_run()` called when process exits → `status=completed`, full findings JSONB, risk_score, compliance, delta, effort_minutes

**What shows in dashboard:**
- Findings panel: severity badges, file:line, rule ID, remediation text
- History panel: run timestamp, counts (CRITICAL/HIGH/MEDIUM/LOW), risk grade (A–F)
- Intelligence: DeepSeek summary, attack paths, 3-week remediation plan

---

---

# SCA — Software Composition Analysis

---

## Scanner 2: Trivy SCA

**What it does:** Scans `pursh/` for known CVEs in Python packages (`requirements.txt`), Node packages (`package.json`), and other package manifests. Pulls from NVD + GitHub Advisory + RedHat databases.

**Target:** `pursh/` filesystem (not a running container — filesystem scan).

**Pre-checks:**
```powershell
trivy --version
```

**How to run (terminal):**
```powershell
trivy fs pursh\ `
  --format json `
  --severity CRITICAL,HIGH,MEDIUM `
  --quiet `
  > internal\scan-results\trivy-pursh-sca.json
```

**Result file:** [internal/scan-results/trivy-pursh-sca.json](../scan-results/trivy-pursh-sca.json)

**Runner API:**
```
GET http://localhost:8002/stream/trivy-sca
GET http://localhost:8002/results/trivy-sca
```

**Output shape (normalized):**
```json
{
  "severity": "CRITICAL",
  "rule": "CVE-2023-44271",
  "file": "pursh/backend/requirements.txt",
  "message": "Pillow: uncontrolled resource consumption via crafted file",
  "cwe": "CWE-400",
  "fix": "10.0.1"
}
```

**Normalizer:** `_norm_trivy()` — iterates `raw["Results"]`, each result has `Vulnerabilities` array. Maps `Severity`, `VulnerabilityID`, `Target`, `Title`, `CweIDs`, `FixedVersion`.

---

## Scanner 3: Trivy Image

**What it does:** Scans a Docker image (not source code) for OS-level CVEs (Alpine packages, Debian packages, etc.) and language-level CVEs inside the image layers.

**Target:** A built Docker image tag. You build the image first via the dashboard "Build Image" button, then scan it.

**Pre-checks:** Docker Desktop must be running.

**How to run (terminal):**
```powershell
# First build the image from Pursh Dockerfile
docker build -f internal\aisec\Dockerfile -t pursh-scan-target:latest .

# Then scan it
trivy image pursh-scan-target:latest `
  --format json `
  --severity CRITICAL,HIGH `
  > internal\scan-results\trivy-env.json
```

**Via runner API with image tag:**
```
GET http://localhost:8002/stream/trivy-image?image=pursh-scan-target:latest
```

**Result file:** [internal/scan-results/trivy-env.json](../scan-results/trivy-env.json)

**Normalizer:** Same `_norm_trivy()` — handles both fs and image output (same JSON schema).

---

## Scanner 4: Grype

**What it does:** Anchore's vulnerability scanner. Uses its own DB (grypedb). Scans a directory for SCA findings — cross-validates Trivy results. Good for second-opinion CVE coverage.

**Binary location:** [internal/scanners/grype-bin/grype.exe](../scanners/grype-bin/grype.exe) (Windows) or `grype` (Linux)

**How to run (terminal):**
```powershell
.\internal\scanners\grype-bin\grype.exe `
  dir:pursh `
  --name pursh `
  -o json `
  > internal\scan-results\grype-pursh.json
```

**Result file:** [internal/scan-results/grype-pursh.json](../scan-results/grype-pursh.json)

**Normalizer:** `_norm_grype()` — reads `raw["matches"]`, each match has `vulnerability.id`, `vulnerability.severity`, `artifact.name`, `vulnerability.description`, `vulnerability.fix.versions`.

---

## Scanner 5: OWASP Dependency-Check

**What it does:** OWASP's own SCA scanner. Uses the NVD database directly (requires NVD API key or local DB). More thorough than Trivy for Java/Python ecosystems. Runs via Docker.

**Pre-checks:** Docker Desktop running.

**How to run (terminal):**
```powershell
docker run --rm `
  -v "${PWD}\pursh:/src:ro" `
  -v "${PWD}\internal\scan-results:/report" `
  owasp/dependency-check `
  --scan /src `
  --project pursh `
  --format JSON `
  --out /report `
  --nvdApiDelay 6000
```

**Result file:** [internal/scan-results/dependency-check-report.json](../scan-results/dependency-check-report.json)

**Normalizer:** `_norm_dependency_check()` — iterates `raw["dependencies"]`, each has `vulnerabilities` array with `severity`, `cvssv3.baseSeverity`, `cwes`, `description`.

**Note:** First run downloads the NVD database (~500MB). Subsequent runs use cached DB.

---

---

# Container Security

---

*(Trivy Image covered above — see Scanner 3)*

---

# Secrets Detection

---

## Scanner 6: Gitleaks

**What it does:** Scans `pursh/` for accidentally committed secrets — API keys, passwords, tokens, connection strings — using regex patterns for 130+ secret types. Works without git history (no-git mode) so it catches secrets in current working files.

**Binary location:** [internal/scanners/gitleaks-bin/gitleaks.exe](../scanners/gitleaks-bin/gitleaks.exe)

**Config file:** [internal/scanners/gitleaks/.gitleaks.toml](../scanners/gitleaks/.gitleaks.toml)

**How to run (terminal):**
```powershell
.\internal\scanners\gitleaks-bin\gitleaks.exe detect `
  --source pursh `
  --config internal\scanners\gitleaks\.gitleaks.toml `
  --report-format json `
  --report-path internal\scan-results\gitleaks-clean.json `
  --no-git
```

**Result file:** [internal/scan-results/gitleaks-clean.json](../scan-results/gitleaks-clean.json)

**Note on exit codes:** Gitleaks exits 1 if secrets are found (this is normal — not a scan failure). The runner handles this: exit 1 → `status=completed`, exit 127 → `status=failed`.

**Normalizer:** `_norm_gitleaks()` — reads raw list of leak objects, each has `RuleID`, `File`, `StartLine`, `Description`. Hardcodes severity to CRITICAL (all secret leaks are critical).

**Output shape:**
```json
{
  "severity": "CRITICAL",
  "rule": "aws-access-key",
  "file": "pursh/backend/config.py",
  "line": 12,
  "message": "AWS Access Key",
  "cwe": "CWE-798",
  "fix": "Rotate the secret immediately and remove from history"
}
```

---

## Scanner 7: TruffleHog

**What it does:** Regex + entropy-based secret scanning. Unique feature: **verifies secrets are live** by actually calling the API they belong to. A "VERIFIED LIVE" finding means the key is still working. Runs via Docker.

**Pre-checks:** Docker Desktop running.

**How to run (terminal):**
```powershell
docker run --rm `
  -v "${PWD}:/repo:ro" `
  trufflesecurity/trufflehog:latest `
  filesystem /repo/pursh `
  --json `
  --no-update `
  > internal\scan-results\trufflehog-pursh.json
```

**Result file:** [internal/scan-results/trufflehog-pursh.json](../scan-results/trufflehog-pursh.json)

**Output format:** NDJSON (one JSON object per line, not a JSON array). The runner's `_parse_result_file()` handles this with `_NDJSON_TYPES`.

**Normalizer:** `_norm_trufflehog()` — reads list of records, checks `Verified` boolean → CRITICAL if verified, HIGH if not. Extracts `DetectorName`, `SourceMetadata.Data.Filesystem.file`.

**Key difference from Gitleaks:** TruffleHog confirms whether secrets are still active. A verified finding is an active incident.

---

## Scanner 8: detect-secrets

**What it does:** Yelp's secret scanner. Pattern-based, similar to Gitleaks. Useful as a third-opinion cross-validator. Outputs a baseline file format.

**Install:**
```powershell
pip install detect-secrets
```

**How to run (terminal):**
```powershell
detect-secrets scan pursh\ --all-files > internal\scan-results\detect-secrets.json
```

**Result file:** [internal/scan-results/detect-secrets.json](../scan-results/detect-secrets.json)

**Output format:**
```json
{
  "version": "1.4.0",
  "results": {
    "pursh/backend/config.py": [
      {"type": "AWS Access Key", "line_number": 15, "hashed_secret": "..."}
    ]
  }
}
```

**Normalizer:** `_norm_detect_secrets()` — iterates `raw["results"]` keyed by filepath, each value is a list of secret objects with `type` and `line_number`.

---

---

# SBOM — Software Bill of Materials

---

## Scanner 9: Syft

**What it does:** Generates a Software Bill of Materials (SBOM) — a complete inventory of all packages, libraries, and their versions in `pursh/`. Output format: CycloneDX 1.5 JSON. SBOM is the foundation for SCA — you scan the SBOM with Grype to find CVEs.

**Install:**
```powershell
# Download from https://github.com/anchore/syft/releases
# Or: winget install anchore.syft
syft --version
```

**How to run (terminal):**
```powershell
syft pursh\ `
  --source-name pursh `
  --source-version 0.0.0-dev `
  -o cyclonedx-json `
  > internal\scan-results\pursh.cyclonedx.json
```

**Result file:** [internal/scan-results/pursh.cyclonedx.json](../scan-results/pursh.cyclonedx.json)

**CycloneDX format:**
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "components": [
    {"type": "library", "name": "fastapi", "version": "0.104.1", "purl": "pkg:pypi/fastapi@0.104.1"}
  ]
}
```

**Normalizer:** `_scan_summary()` for `cyclonedx` type counts `raw["components"]` and returns component count. Syft itself doesn't produce "findings" — it produces an inventory. The intelligence endpoint can analyze the SBOM component list.

---

---

# IaC Security — Infrastructure as Code

---

## Scanner 10: Checkov

**What it does:** Scans Terraform, CloudFormation, K8s manifests for security misconfigurations. 2000+ built-in checks covering CIS, HIPAA, NIST, SOC2. Checks things like: S3 bucket public access, security groups open to 0.0.0.0/0, unencrypted RDS, missing MFA.

**Target:** [internal/infra/terraform/](../infra/terraform/)

**Install:**
```powershell
pip install checkov
```

**How to run (terminal):**
```powershell
python -m checkov.main `
  -d internal\infra\terraform `
  --output json `
  --skip-check CKV_TF_1 `
  --compact `
  --quiet `
  > internal\scan-results\checkov.json
```

**Result file:** [internal/scan-results/checkov.json](../scan-results/checkov.json)

**Note on `write_stdout: true`:** Checkov writes JSON to stdout. The runner captures stdout and writes it to the result file directly (unlike Gitleaks which writes its own file).

**Normalizer:** `_norm_checkov()` — handles both single dict and list (Checkov can output multiple framework blocks). Iterates `results.failed_checks`, maps `check_id`, `repo_file_path`, `file_line_range`, `check.name`, `guideline`.

**Output shape:**
```json
{
  "severity": "HIGH",
  "rule": "CKV_AWS_18",
  "file": "internal/infra/terraform/s3.tf",
  "line": 23,
  "message": "Ensure the S3 bucket has access logging enabled",
  "fix": "https://docs.bridgecrew.io/docs/s3_15-s3-bucket-logging"
}
```

---

## Scanner 11: tfsec

**What it does:** Another Terraform security scanner (Aqua Security). Focuses specifically on Terraform. Faster than Checkov for Terraform-only repos. Good for cross-validating Checkov results.

**Install:**
```powershell
# Download from https://github.com/aquasecurity/tfsec/releases
# Or: winget install aquasecurity.tfsec
tfsec --version
```

**How to run (terminal):**
```powershell
tfsec internal\infra\terraform `
  --format json `
  --soft-fail `
  --out internal\scan-results\tfsec-pursh.json
```

**Result file:** [internal/scan-results/tfsec-pursh.json](../scan-results/tfsec-pursh.json)

**Normalizer:** `_norm_tfsec()` — reads `raw["results"]`, each has `rule_id`, `severity`, `description`, `location.filename`, `location.start_line`, `resolution`.

---

## Scanner 12: KICS

**What it does:** Checkmarx IaC scanner. Supports Terraform, Ansible, CloudFormation, Kubernetes, Dockerfile, Docker Compose. Broader IaC coverage than Checkov for mixed environments. Runs via Docker.

**Pre-checks:** Docker Desktop running.

**How to run (terminal):**
```powershell
docker run --rm `
  -v "${PWD}:/path:ro" `
  -v "${PWD}\internal\scan-results:/output" `
  checkmarx/kics:latest scan `
  -p /path/internal/infra/terraform `
  -o /output `
  --report-formats json `
  --output-name kics-pursh `
  --no-progress
```

**Result file:** [internal/scan-results/kics-pursh.json](../scan-results/kics-pursh.json)

**Normalizer:** `_norm_kics()` — reads `raw["queries"]`, each query has `query_name`, `severity`, `files` array. Maps `cwe_ids`, creates one finding per affected file per query.

---

---

# DAST — Dynamic Application Security Testing

> These scanners require Pursh to be running. Start `pursh/frontend` on :3000 and `pursh/backend` on :8001 first.

---

## Scanner 13: ZAP (OWASP ZAP)

**What it does:** The most comprehensive DAST scanner. Sends real HTTP requests to the running Pursh app. Passive scan (just watches traffic) + active scan (injects payloads: SQL injection, XSS, path traversal, CSRF, etc.). Requires Docker.

**Pre-checks:**
- Docker Desktop running
- Pursh frontend: `http://localhost:3000`
- Pursh backend: `http://localhost:8001`

**How to run manually (full command):**
```powershell
docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py `
  -t http://host.docker.internal:3000 `
  -J zap-report.json
# then copy result from container
```

**Via dashboard:** ZAP shows a setup instruction card (target requires running app).

**Result file:** [internal/scan-results/zap-report.json](../scan-results/zap-report.json)

**Result format (ZAP JSON schema):**
```json
{
  "site": [{
    "@name": "http://localhost:3000",
    "alerts": [{
      "alert": "Missing Anti-clickjacking Header",
      "riskdesc": "Medium (Medium)",
      "cweid": "1021",
      "solution": "Modern Web browsers support X-Frame-Options HTTP header...",
      "instances": [{"uri": "http://localhost:3000/login"}]
    }]
  }]
}
```

**Normalizer:** `_norm_zap()` — maps `riskdesc` first word to severity, `alertRef`, `cweid`, `solution`, `instances[0].uri`.

---

## Scanner 14: Nikto

**What it does:** Web server scanner. Focuses on server-level issues: outdated server software, dangerous HTTP methods (PUT/DELETE enabled), known vulnerable files, misconfigured headers, SSL issues. Less comprehensive than ZAP for app logic but very fast. Runs via Docker.

**How to run (terminal):**
```powershell
docker run --rm --network=host frapsoft/nikto `
  -h http://localhost:3000 `
  -o /tmp/nikto-pursh.xml `
  -Format xml
# Result is in the container — mount volume to capture:
docker run --rm --network=host `
  -v "${PWD}\internal\scan-results:/output" `
  frapsoft/nikto `
  -h http://localhost:3000 `
  -o /output/nikto-pursh.xml `
  -Format xml
```

**Result file:** [internal/scan-results/nikto-pursh.xml](../scan-results/nikto-pursh.xml)

**Output format:** XML (not JSON). The runner's `_parse_result_file()` handles this with `_XML_TYPES` → parses with `xml.etree.ElementTree`.

**Normalizer:** `_norm_nikto()` — iterates `<item>` elements, checks for CVE/OSVDB references to set severity HIGH vs MEDIUM. Extracts `<uri>`, `<description>`, `<solution>`.

---

## Scanner 15: Schemathesis

**What it does:** API fuzzer. Reads the OpenAPI spec from Pursh's backend (`/openapi.json`) and automatically generates hundreds of test cases for every endpoint and parameter. Finds: invalid input handling (5xx errors), authentication bypasses, schema violations.

**Install:**
```powershell
pip install schemathesis
```

**Pre-checks:** Pursh backend running at `http://localhost:8001/openapi.json`

**How to run (terminal):**
```powershell
schemathesis run `
  http://localhost:8001/openapi.json `
  --checks all `
  --hypothesis-max-examples 50 `
  --report internal\scan-results\schemathesis-pursh.json
```

**Result file:** [internal/scan-results/schemathesis-pursh.json](../scan-results/schemathesis-pursh.json)

**Normalizer:** `_norm_schemathesis()` — reads results list, filters for status codes ≥ 400. HIGH for 5xx (server error = bug), MEDIUM for 4xx (unexpected handling). Maps `method`, `path`, `checks` failures.

---

## Scanner 16: Nuclei

**What it does:** ProjectDiscovery's template-based vulnerability scanner. Has 5000+ templates for CVEs, misconfigurations, exposed panels, API keys in responses, default credentials. Runs via Docker. Targets running HTTP services.

**How to run (terminal):**
```powershell
docker run --rm --network=host `
  -v "${PWD}\internal\scan-results:/output" `
  projectdiscovery/nuclei:latest `
  -u http://localhost:3000 `
  -t cves/ `
  -t misconfiguration/ `
  -json-export /output/nuclei-pursh.json `
  -silent
```

**Result file:** [internal/scan-results/nuclei-pursh.json](../scan-results/nuclei-pursh.json)

**Output format:** NDJSON (one JSON object per matched template).

**Normalizer:** `_norm_nuclei()` — reads list of records, maps `info.severity`, `template-id`, `matched-at` (the URL), `info.name`, `info.remediation`.

---

---

# Network Security

---

## Scanner 17: Nmap

**What it does:** Port scanner + service fingerprinter. Finds open ports on localhost, identifies running services and versions. When run with NSE scripts, can detect specific vulnerabilities. Used in AppSec to check: is anything exposed that shouldn't be? Is the service version outdated?

**Install:**
```powershell
# Download from https://nmap.org/download.html
nmap --version
```

**How to run (terminal):**
```powershell
nmap -sV --open -oX internal\scan-results\nmap-pursh.xml localhost
```

**Result file:** [internal/scan-results/nmap-pursh.xml](../scan-results/nmap-pursh.xml)

**Output format:** XML. Parsed with `xml.etree.ElementTree`.

**Normalizer:** `_norm_nmap()` — iterates `<host>` → `<port>` where `<state state="open">`. Extracts `portid`, `protocol`, `service name/product/version`. Checks NSE `<script>` output for "vuln" → HIGH, otherwise INFO.

---

## Scanner 18: Suricata

**What it does:** Network IDS/IPS (Intrusion Detection System). Watches live network traffic and fires alerts when it sees attack patterns — port scans, exploit attempts, known malware C2 traffic, protocol anomalies. Requires a running sensor capturing traffic.

**Setup required (not built-in — requires external infra):**
```bash
# Linux only
sudo apt install suricata
sudo suricata-update   # download rule sets
sudo suricata -i eth0  # start monitoring interface eth0
# Copy logs:
cp /var/log/suricata/eve.json internal/scan-results/suricata-eve.json
```

**Result file:** [internal/scan-results/suricata-eve.json](../scan-results/suricata-eve.json)

**Output format:** NDJSON EVE log format. Each line is a JSON event. Runner filters for `event_type == "alert"`.

**Normalizer:** `_norm_suricata()` — reads list of EVE records, filters `event_type=alert`, maps `alert.signature`, `alert.category`, `alert.severity` (1=HIGH, 2=MEDIUM, 3=LOW), `src_ip`, `dest_ip`, `proto`.

---

## Scanner 19: Zeek

**What it does:** Network Security Monitor. More passive than Suricata — captures and logs all network activity without blocking. Generates structured logs: `conn.log`, `dns.log`, `http.log`, `notice.log`. The `notice.log` is what we ingest — it contains analyst-relevant alerts.

**Setup required:**
```bash
sudo apt install zeek
zeek -i eth0   # start on interface
# Copy notice log:
cp /opt/zeek/logs/current/notice.log internal/scan-results/zeek-notice.log
```

**Result file:** [internal/scan-results/zeek-notice.log](../scan-results/zeek-notice.log)

**Output format:** TSV (tab-separated) with `#fields` header line. Runner's `_parse_result_file()` parses TSV into list of dicts using `_TSV_TYPES` handler.

**Normalizer:** `_norm_zeek()` — reads rows, checks `note` field for keywords: "scan"/"bruteforce"/"attack" → HIGH, "weird"/"protocol" → MEDIUM, else LOW.

---

## Scanner 20: OpenVAS (Greenbone)

**What it does:** Full vulnerability scanner suite. Does authenticated network scanning, service enumeration, CVE checking at the network level. Enterprise-grade. Requires the Greenbone Community Edition running as a separate service.

**Setup required:**
```bash
docker run -d --name greenbone-community-edition \
  -p 9390:9390 greenbone/community-edition
# Then: run a task in the Greenbone web UI at http://localhost:9392
# Export results XML to:
# internal/scan-results/openvas-report.xml
```

**Result file:** [internal/scan-results/openvas-report.xml](../scan-results/openvas-report.xml)

**Output format:** XML. Parsed with `xml.etree.ElementTree`.

**Normalizer:** `_norm_openvas()` — iterates `<result>` elements, reads `<threat>` (Critical/High/Medium/Low/Log), `<name>`, `<description>`, `<host>`, `<nvt>` attributes.

---

---

# CloudSec — AWS Security (Stubs)

> These scanners require AWS credentials and a live AWS account. They output an INFO-level setup instruction finding explaining the required setup. Run them with your own AWS credentials to get real findings.

---

## Scanner 21: Prowler

**What it does:** AWS CSPM (Cloud Security Posture Management). Runs 300+ checks against your AWS account: IAM misconfigurations, S3 public buckets, CloudTrail disabled, unencrypted EBS, security group rules open to internet. Maps findings to CIS AWS Foundations, NIST 800-53, HIPAA, GDPR.

**Setup:**
```powershell
docker run --rm `
  -e AWS_ACCESS_KEY_ID `
  -e AWS_SECRET_ACCESS_KEY `
  -e AWS_DEFAULT_REGION `
  prowler/prowler -M json `
  -o /tmp/prowler-output.json
# Copy result to internal/scan-results/prowler-output.json
```

**Result file:** [internal/scan-results/prowler-output.json](../scan-results/prowler-output.json)

**Live link:** [https://github.com/prowler-cloud/prowler](https://github.com/prowler-cloud/prowler)

---

## Scanner 22: ScoutSuite

**What it does:** Multi-cloud CSPM. Cross-validates Prowler findings. Also covers GCP and Azure.

**Setup:**
```bash
pip install scoutsuite
scout aws --report-dir /tmp/scoutsuite
# Copy last_run.json to internal/scan-results/scoutsuite-results.json
```

**Result file:** [internal/scan-results/scoutsuite-results.json](../scan-results/scoutsuite-results.json)

---

## Scanner 23: GuardDuty

**What it does:** AWS native threat detection. Analyzes CloudTrail, VPC Flow Logs, DNS logs for: unusual API calls, compromised credentials, cryptomining, lateral movement.

**Setup:**
```powershell
aws guardduty list-findings --detector-id <id>
aws guardduty get-findings --detector-id <id> --finding-ids <ids>
# Save JSON to internal/scan-results/guardduty-findings.json
```

---

## Scanner 24: AWS Inspector v2

**What it does:** AWS-native CVE scanner for EC2 instances, ECR container images, Lambda functions. Automatically discovers workloads and scans continuously.

**Setup:**
```powershell
aws inspectorv2 list-findings --output json > internal\scan-results\inspector-findings.json
```

---

## Scanner 25: AWS Macie

**What it does:** S3 data classification service. Scans S3 buckets for sensitive data: credit cards, SSNs, AWS credentials, HIPAA-related patterns. Critical for Pursh's lab results bucket (even with synthetic data).

**Setup:**
```powershell
aws macie2 list-findings
aws macie2 get-findings --finding-ids <ids>
# Save to internal/scan-results/macie-findings.json
```

---

## Scanner 26: IAM Access Analyzer

**What it does:** Finds IAM policies that allow access from outside your AWS account (external access), unused IAM roles, over-permissive role trust policies.

**Setup:**
```powershell
aws accessanalyzer list-findings --analyzer-arn <arn> --output json `
  > internal\scan-results\iam-analyzer-findings.json
```

---

---

# AI Security (Stubs)

> Require Pursh's AI endpoints running (doctor-matching, visit summarization, symptom checker) and respective tool installs.

---

## Scanner 27: promptfoo (LLM Red-Team)

**What it does:** Tests LLM integrations against the OWASP LLM Top 10. Runs automated prompt injection attacks, jailbreak attempts, PHI leak tests. Config-driven — you write test cases in YAML.

**Config file:** [internal/scanners/promptfoo/config.yaml](../scanners/promptfoo/config.yaml) *(to be created in Phase 10)*

**Setup:**
```powershell
# Requires Pursh AI endpoints running
npx promptfoo eval `
  -c internal\scanners\promptfoo\config.yaml `
  -o internal\scan-results\promptfoo-results.json
```

**Live link:** [https://www.promptfoo.dev/](https://www.promptfoo.dev/)

---

## Scanner 28: Garak (LLM Vulnerability Scanner)

**What it does:** DeepMind-inspired LLM red-teaming. Tests: prompt injection, jailbreaks, data exfiltration, toxicity, hallucination exploits. Generates a full probe report.

**Setup:**
```bash
pip install garak
python -m garak \
  --model_type rest \
  --model_name pursh-llm \
  --report_prefix internal/scan-results/garak-results
```

**Live link:** [https://github.com/leondz/garak](https://github.com/leondz/garak)

---

---

# Intelligence Engine (DeepSeek AI)

Every scanner has an `/intelligence/{scanner_id}` endpoint powered by DeepSeek's `deepseek-chat` model.

**What it generates:**
```json
{
  "summary": "3-4 sentence executive risk summary",
  "attack_paths": [
    {
      "title": "SQL Injection → Patient Record Exfiltration",
      "steps": ["Submit crafted search param", "Bypass WHERE clause", "Return all patient rows"],
      "impact": "HIPAA breach — all patient records exposed",
      "severity": "CRITICAL"
    }
  ],
  "remediation_plan": {
    "week1": ["Parameterize all queries", "Add input validation middleware"],
    "week2": ["Deploy WAF rule for SQL injection patterns"],
    "week3": ["Re-run SAST + DAST to verify all findings closed"]
  },
  "exploitability": "High",
  "top_priority": "Fix SQL injection in patient search before any other work"
}
```

**2-hour cache logic:**
```
Request → check ai_analyses table for entry < 2 hours old
    ├── Found → return cached (no DeepSeek API call)
    └── Not found → call DeepSeek → save to ai_analyses → return
```

**How to test:**
```
GET http://localhost:8002/intelligence/semgrep
```

**Cost:** DeepSeek API is ~$0.001 per analysis. Cache ensures you're not calling on every page refresh.

---

# Supabase Data Flow

```
Every scan run:
    scan_runs table:
        run_id (UUID)
        scanner_id (e.g. "semgrep")
        scanner_name ("Semgrep (SAST)")
        started_at, finished_at (ISO timestamps)
        exit_code (integer)
        status ("running" → "completed" / "failed")
        counts ({"CRITICAL": 2, "HIGH": 5, "MEDIUM": 12, "LOW": 3})
        findings_count (22)
        findings (JSONB array of normalized finding objects)
        raw_output (last 200 lines of stdout)
        fingerprints (["rule|file|severity", ...])
        risk_score ({"score": 42, "grade": "C", "trend": "worse"})
        compliance ({"owasp": {...}, "hipaa": 3, "pci_dss": 2})
        delta ({"new": 4, "fixed": 2, "unchanged": 18, "new_critical": 1})
        effort_minutes (total estimated fix time)

Every AI analysis:
    ai_analyses table:
        scanner_id
        run_id (null if triggered separately)
        model ("deepseek-chat")
        prompt (full text sent to DeepSeek)
        response_raw (full response text)
        response_parsed (JSONB — the structured JSON)
        prompt_chars, response_chars
        latency_ms
        cached (false = real call, true = served from cache)
        error (null if success)
```

**View live in Supabase:**
[https://supabase.com/dashboard](https://supabase.com/dashboard) → your project → Table Editor → `scan_runs`

---

# Runner API — Complete Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/healthz` | Liveness probe |
| GET | `/scanners` | List all 28 scanners |
| GET | `/precheck/{scanner_id}` | Run pre-flight checks |
| GET | `/stream/{scanner_id}` | SSE — live scanner output |
| GET | `/results/{scanner_id}` | Parsed findings (Supabase first, file fallback) |
| GET | `/history/{scanner_id}` | Last 10 runs from Supabase |
| POST | `/run/{scanner_id}` | Fire-and-forget background run |
| POST | `/stop/{scanner_id}` | Terminate running scanner |
| GET | `/intelligence/{scanner_id}` | DeepSeek AI analysis |
| GET | `/risk-score/{scanner_id}` | Fast risk score (no AI call) |
| GET | `/findings` | Aggregate findings across all scanners |
| POST | `/build-image` | Queue Docker image build |
| GET | `/stream/build-image` | SSE — live Docker build output |

**Test all scanners are registered:**
```
GET http://localhost:8002/scanners
→ Returns all 28 scanner IDs with labels and result file names
```

---

# Troubleshooting Quick Reference

| Problem | Cause | Fix |
|---|---|---|
| `curl: (7) Failed to connect to localhost:8002` | Runner not started | `uvicorn main:app --reload --port 8002` from `internal/aisec/runner/` |
| Precheck fails: `semgrep not found` | Not installed | `pip install semgrep` |
| History empty after scan | Supabase circuit breaker open | Check `SUPABASE_URL` and `SUPABASE_JWT_SECRET` in `internal/aisec/.env` |
| Docker scanner fails | Docker Desktop not running | Start Docker Desktop |
| ZAP fails: target unreachable | Pursh not running | Start frontend + backend (see top of this doc) |
| Intelligence returns `{"status": "no_data"}` | Result file doesn't exist yet | Run the scanner first |
| Intelligence returns error | `DEEPSEEK_API_KEY` missing | Add to `internal/aisec/.env` |
| `status=failed` in history | Scanner binary not found (exit 127) | Check binary path in `scanners.py`, install the tool |
| Dashboard shows "Supabase · live" but history empty | Realtime not enabled | Supabase Dashboard → Database → Replication → enable `scan_runs` |
