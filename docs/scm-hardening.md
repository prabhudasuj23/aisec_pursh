# SCM Security Hardening — AISec + Pursh Monorepo

This document is the master reference for source-code-management security in
this repository. It maps to the JD responsibility "Review and enhance SCM
security practices" (CLAUDE.md §1.6).

---

## 1. Artifact inventory

| File | Status | Purpose |
|---|---|---|
| `CODEOWNERS` | ✅ Phase 0 | Sensitive paths require security review on every PR |
| `.github/branch-protection.md` | ✅ Phase 0 | Documents + tracks branch protection rules on `main` |
| `.github/pull_request_template.md` | ✅ Phase 0 | Security checklist injected into every PR |
| `.github/dependabot.yml` | ✅ Phase 0 | Automated dependency updates (daily prod, weekly dev) |
| `.github/SECURITY.md` | ✅ Phase 0 | Vulnerability disclosure policy |
| `.gitignore` | ✅ Phase 0 | Strict: no `.env`, `.pem`, `*.key`, Terraform state |
| `.pre-commit-config.yaml` | ✅ Phase 0 | Gitleaks, detect-secrets, ruff, black, mypy, yamllint, terraform fmt, tflint, checkov |
| `.github/workflows/secret-scan.yml` | ✅ Phase 0 | Gitleaks on every PR + full-history scan weekly |
| `commit-signing-policy.md` | ✅ Phase 0 | GPG/SSH signing setup + rationale |
| `docs/scm-hardening.md` | ✅ Phase 0 | This document |

---

## 2. Branch protection (`main`)

See [`.github/branch-protection.md`](../.github/branch-protection.md) for the
full rule table and CLI commands to apply them.

Summary:
- Signed commits required
- Linear history (rebase/squash only)
- 1 approving review + CODEOWNERS review on sensitive paths
- All CI checks must pass
- Force-push and branch deletion are blocked
- Admins cannot bypass

---

## 3. Secrets management posture

### What never enters the repo

- Environment variables (`.env.*` in `.gitignore`)
- Private keys, certificates, API tokens
- Terraform state files (contain resource IDs + outputs)
- AWS credentials of any kind

### How secrets reach running services

| Secret type | Storage | Access mechanism |
|---|---|---|
| AWS resource credentials | Not stored — OIDC from GitHub Actions to AWS | Ephemeral role assumption |
| Runtime app secrets (DB URLs, API keys) | AWS Secrets Manager | ECS task role reads at startup |
| Non-sensitive config (region, env name) | AWS Parameter Store (SSM) | ECS task role reads at startup |
| Supabase keys (for local dev) | `.env.local` (gitignored) | Developer reads from Supabase dashboard |

### Pre-commit defense layers

1. **`gitleaks`** — pattern-based scanning for 200+ secret types (AWS keys, GitHub tokens, etc.)
2. **`detect-secrets`** — entropy-based scanning for high-entropy strings
3. **`detect-private-key`** (pre-commit-hooks) — catches PEM blocks
4. **`.gitignore`** — prevents `.env` and key files from even reaching staging

### CI defense layer

`.github/workflows/secret-scan.yml` runs Gitleaks on:
- Every PR (HEAD diff only — fast)
- Every push to `main`
- Full git history weekly (catches old leaks if a hook was bypassed)

---

## 4. Dependency security

Dependabot is configured in `.github/dependabot.yml` to:
- Update Python deps **daily** for AISec backend and Pursh backend
- Update npm deps **weekly** for both Next.js frontends
- Update GitHub Actions **weekly**
- Major version bumps are blocked from auto-PR — reviewed manually

SCA scanning (Trivy + Grype) is added in Phase 3/4 and will gate on critical CVEs.

---

## 5. CODEOWNERS — sensitive path coverage

Paths that require explicit security review on every PR:

| Path | Why sensitive |
|---|---|
| `/aisec/app/auth/` | OIDC JWT verification — auth bypass risk |
| `/pursh/backend/auth/` | Supabase Auth integration — session security |
| `/aisec/app/mappings/` | OWASP/HIPAA/GDPR mappings — compliance accuracy |
| `/docs/compliance/` | Compliance documentation — legal accuracy |
| `/infra/terraform/` | IaC — AWS resource creation, IAM policies |
| `/.github/workflows/` | CI pipelines — supply chain attack surface |
| `/pipelines/` | Scanner composite actions — same risk as above |
| `/docs/runbooks/` | Incident response procedures |
| `/docs/threat-models/` | Threat model accuracy |
| `/pursh/backend/llm/` | PHI redaction layer before LLM calls |
| `/pursh/backend/audit/` | HIPAA §164.312(b) audit log writes |
| `/pursh/backend/storage/` | S3 + KMS PHI file handling |

---

## 6. Commit signing rationale

Unsigned commits can be forged by anyone with repository access. A commit
bearing your name and email proves nothing about authorship unless it is
cryptographically signed. Signed commits bind the commit content to your GPG
or SSH private key.

Enforcement: branch protection on `main` requires signed commits. Pre-commit
hook `no-commit-to-branch` prevents direct pushes to `main` from local machines.

Setup instructions: [`commit-signing-policy.md`](../commit-signing-policy.md).

---

## 7. Supply chain (v1 scope)

Current posture:
- Dependabot tracks all direct dependencies
- Gitleaks scans for leaked tokens in third-party-adjacent code
- SBOM generated per build in Phase 4 (Syft → CycloneDX)
- GitHub Actions pinned to commit SHA (enforced starting Phase 2)

Future (documented, not implemented in v1):
- SLSA Level 3 provenance
- Sigstore signing for container images
- In-toto attestations for build steps
- See `/docs/architecture/future-supply-chain.md` (created Phase 4)

---

## 8. Developer setup checklist

Before your first commit to this repo:

```bash
# 1. Install pre-commit
pip install pre-commit
pre-commit install

# 2. Set up commit signing (see commit-signing-policy.md)
git config --global commit.gpgsign true

# 3. Initialize detect-secrets baseline (first time only)
detect-secrets scan > .secrets.baseline
git add .secrets.baseline

# 4. Verify hooks run cleanly
pre-commit run --all-files

# 5. Install Terraform toolchain (for IaC work)
# terraform >= 1.7, tflint, checkov
```
