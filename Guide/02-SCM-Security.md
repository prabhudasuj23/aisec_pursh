# Chapter 2: Git & Source Code Management (SCM) Security

> **Goal:** Understand how attackers exploit Git repositories and CI/CD integrations, and how to harden them. In enterprises, the repository platform is a critical attack surface — it holds your source code, secrets, deployment scripts, and CI credentials.

---

## 2.1 Why SCM Security Matters

Your Git repository is not just code storage. It holds:
- **Application source code** (the blueprints of your system)
- **CI/CD pipeline definitions** (the automation that deploys to production)
- **Infrastructure-as-Code** (the definition of your cloud resources)
- **Secrets** (API keys, database passwords — if developers commit them accidentally)
- **Configuration files** (application settings, sometimes with credentials)

If an attacker controls your repository or CI/CD system, they can:
1. Read all your source code and find vulnerabilities
2. Modify code before it reaches production (supply chain attack)
3. Steal credentials that were committed by accident
4. Use CI runner access to pivot into production environments

### Real-World Case Study: Samsung GitHub Leak (2022)

Samsung developers accidentally pushed 190GB of proprietary source code to **public** GitHub repositories. This included:
- Samsung's Galaxy source code
- Security and encryption algorithms
- Qualcomm source code

**How it happened:** Developers used personal GitHub accounts, created repositories without checking visibility settings, and pushed code without any automated detection or alerts.

**What would have prevented it:**
- Organization-level policy requiring all repos to be private by default
- Automated secret and sensitive data scanning (GitHub Advanced Security)
- Training on proper use of personal vs. corporate accounts
- CODEOWNERS to prevent unknown repos from being created under the org

---

## 2.2 Git Fundamentals for Security Engineers

You do not need to be a Git expert, but you need to understand these concepts for security discussions.

### Key Concepts

**Branch:** An independent line of development. `main` is the production branch. Feature branches (`feature/add-login`) are where developers work.

**Pull Request (PR) / Merge Request (MR):** A request to merge changes from a feature branch into `main`. This is where security review and automated checks happen.

**Commit:** A snapshot of changes. Every commit has an author, timestamp, and unique hash (SHA).

**Tag:** A named pointer to a specific commit. Used to mark releases (`v1.2.3`).

**Protected branch:** A branch with rules enforced — required reviews, required checks, no force pushes.

### Branch Strategies and Their Security Implications

| Strategy | How It Works | Security Implication |
|---|---|---|
| **Trunk-based development** | Everyone commits to `main` directly (or via very short-lived branches) | Fast, but requires very strong automated gates — humans review less |
| **GitFlow** | `main`, `develop`, `release`, `hotfix` branches | More manual checkpoints; complex but more audit points |
| **GitHub Flow** | `main` + feature branches + PRs | Simple, works well with automated PR checks |

Most enterprises use **GitHub Flow** or a variation. The PR is the primary checkpoint for security gates.

---

## 2.3 Branch Protection Rules

Branch protection rules are settings that prevent bad things from happening to important branches (like `main`).

### The Essential Branch Protection Rules

**1. Require pull request reviews**
- At least 1 (ideally 2) approving reviews before merge
- Prevents developers from merging their own code without peer review

**2. Require status checks to pass**
- CI checks (SAST, SCA, tests) must all pass before merge
- If Semgrep finds a critical vulnerability, the PR cannot merge until it is fixed

**3. Require signed commits**
- Commits must be cryptographically signed (GPG or SSH key)
- Proves the commit actually came from the claimed author
- Prevents commit author spoofing

**4. Disable force pushes**
- Prevents history rewriting on protected branches
- Ensures the audit trail is immutable — you cannot erase evidence

**5. Require linear history**
- No merge commits — only squash or rebase
- Cleaner history, easier to bisect for security issues

**6. CODEOWNERS review required**
- Certain files require review from specific people
- Example: Any change to `auth/` requires approval from the security team

### Setting Up Branch Protection in GitHub

```
Repository Settings → Branches → Add rule → Branch name pattern: main

Check:
✅ Require a pull request before merging
  ✅ Require approvals: 2
  ✅ Dismiss stale pull request approvals when new commits are pushed
  ✅ Require review from Code Owners
✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging
  Status checks: semgrep, trivy-sca, test-suite
✅ Require signed commits
✅ Do not allow bypassing the above settings
✅ Restrict who can push to matching branches: [security-team, release-managers]
```

### CODEOWNERS File

The `CODEOWNERS` file defines who must approve changes to specific paths:

```
# .github/CODEOWNERS

# Authentication code — security team must approve
/src/auth/                @company/security-team

# Infrastructure code — platform team must approve
/infra/terraform/          @company/platform-team

# Payment processing — security + payments team
/src/payments/             @company/security-team @company/payments-team

# CI/CD pipelines — DevOps and security
/.github/workflows/        @company/devops @company/security-team

# This CODEOWNERS file itself
/.github/CODEOWNERS        @company/security-team
```

When a PR touches `/src/auth/`, GitHub automatically requests a review from `@company/security-team`. The PR cannot merge without their approval.

---

## 2.4 Security-Focused Code Review

Code review is not just about functionality. As an AppSec engineer reviewing a PR, look for:

### Security Review Checklist

**Authentication and Authorization:**
- [ ] Is every API endpoint protected? No anonymous access to protected resources?
- [ ] Are authorization checks done server-side? (Never trust client-supplied user IDs)
- [ ] Are privilege checks in place before sensitive operations?

**Input Handling:**
- [ ] Is user input validated before use?
- [ ] Are database queries parameterized? No string concatenation into SQL?
- [ ] Is output encoded before rendering in HTML/JS?

**Secrets and Sensitive Data:**
- [ ] Are credentials, API keys, or passwords hardcoded anywhere?
- [ ] Are sensitive values logged anywhere (passwords, SSNs, credit card numbers)?
- [ ] Are secrets loaded from environment variables or secret management systems?

**Error Handling:**
- [ ] Do error responses reveal internal details (stack traces, file paths, SQL errors)?
- [ ] Does the app fail closed (deny by default) on error?

**Crypto:**
- [ ] Is encryption used for sensitive data at rest and in transit?
- [ ] Are approved algorithms used? (AES-256, RSA-2048+, SHA-256+, bcrypt for passwords)
- [ ] Are there any custom cryptography implementations? (Red flag — use libraries)

**Dependencies:**
- [ ] Are new dependencies added? Do they have known vulnerabilities (CVEs)?
- [ ] Are dependency versions pinned?

---

## 2.5 Secrets Detection and Repository Hygiene

Developers accidentally commit secrets more often than you'd think. Common causes:
- `.env` file committed instead of `.env.example`
- Hardcoded credentials during local development, forgotten before push
- Copy-paste of example code that included real credentials
- Debugging code left in (`print(api_key)` in a commit)

### What Gets Committed Accidentally

- AWS access keys (`AKIA...`)
- Database connection strings with passwords
- Private keys (`.pem`, `.key` files)
- OAuth tokens and JWT secrets
- API keys for third-party services (Stripe, Twilio, Sendgrid)
- Slack webhook URLs
- Docker registry credentials

### The Problem: Git History Is Forever

Even if you delete the secret in a new commit, **it still exists in Git history**. Anyone who clones the repo can see it:

```bash
git log --all -p | grep -i "password\|secret\|key\|token"
```

This is why detection must happen **before** the commit reaches the remote repository.

### Secrets Detection Tools

**1. Gitleaks (pre-commit + CI)**
Gitleaks scans for secrets using pattern matching and entropy analysis.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
```

This runs locally before every commit. If it detects a secret, the commit is blocked.

**2. detect-secrets (baseline approach)**
Creates a baseline of known "false positives" (like test data that looks like secrets but isn't) so you can suppress known safe patterns.

**3. GitHub Secret Scanning (native)**
GitHub automatically scans all pushes for known secret patterns (AWS keys, Stripe keys, etc.) and notifies repository admins. For public repositories, this is free.

**4. Trufflehog (entropy-based scanning)**
Finds secrets even without known patterns by looking for high-entropy strings.

### What to Do When a Secret Is Found

1. **Immediately revoke/rotate the credential** — assume it was already stolen
2. **Remove from all branches** (use `git filter-repo` or BFG Repo Cleaner)
3. **Check audit logs** for unauthorized use of the credential
4. **Post-mortem:** How did this happen? Add prevention controls

### .gitignore Best Practices

```gitignore
# NEVER commit these
.env
.env.local
.env.production
*.pem
*.key
*.p12
secrets/
credentials/
.aws/credentials
terraform.tfvars       # often contains sensitive variables
*.tfstate              # terraform state may contain sensitive values
```

---

## 2.6 Repository Access Control

### Principle of Least Privilege for Repo Access

Not everyone needs write access to every repository:

| Role | Access Level | Rationale |
|---|---|---|
| Read-only auditors | `Read` | Can see code for audit purposes, cannot modify |
| External contractors | `Read` (specific repos only) | Scoped to what they need |
| Developers | `Write` (via PR only) — cannot push directly to `main` | Branch protection enforces PR workflow |
| DevOps | `Write` to infra repos | Scoped to their domain |
| Admins | `Admin` on their team's repos | Not organization-wide admin |

### Service Account and Bot Access

CI/CD pipelines need a token to interact with Git. Options:

**Personal Access Tokens (PATs) — avoid**
- If the developer leaves, the token may be revoked unexpectedly, breaking CI
- PATs often have broader permissions than needed
- Hard to rotate across many pipelines

**GitHub Apps — preferred for CI/CD**
- Organization-level identity (not tied to a person)
- Fine-grained permissions (read PR, write commit status — not full repo access)
- Easy to rotate

**OIDC (OpenID Connect) — best for cloud deployments**
- No static credentials at all
- The CI runner proves its identity to AWS/Azure/GCP via a short-lived token
- Token cannot be stolen and reused (expires in minutes)

```yaml
# GitHub Actions with OIDC to AWS — no secrets needed
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
    aws-region: us-east-1
    # No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed!
```

### Multi-Repository Management at Enterprise Scale

**The problem:** An enterprise with 200+ repositories cannot rely on individual teams to configure security settings manually. Some will forget CODEOWNERS. Some will allow direct pushes to `main`.

**The solution:** Org-level policies and automation

- **GitHub:** Organization settings enforce baseline rules (e.g., MFA required for all members)
- **GitLab:** Group-level policies apply to all projects in the group
- **Automated compliance checks:** Tools like `github-org-manager` or custom scripts verify that every repo has branch protection, CODEOWNERS, and required checks configured
- **Repository templates:** When a new repo is created, it starts from a template with security settings pre-configured

---

## 2.7 Secure Branching for Release Management

### Hotfix Flow and Security

When a critical vulnerability is found in production:

```
main (production) ──────────────────────────────────────────────────────
        │                                                           ↑
        └── hotfix/cve-2024-1234 ──[fix]──[security review]──[test]──┘
```

Security considerations:
- Even emergency hotfixes must go through at least one security review
- The security team approves the fix is complete and does not introduce new issues
- The fix is cherry-picked back to any development branches

### Release Branches

```
main ────────────────────────────────────────────────────────────
  │
  └── release/v2.1 ──[final security scan]──[pen test]──[sign-off]──[tag v2.1.0]
```

Before tagging a release:
1. Full SAST + SCA + DAST run (not just on changed files — full scan)
2. Penetration test (for major releases)
3. Security engineer sign-off confirming all critical/high findings resolved
4. Generate SBOM (Software Bill of Materials) for the release

---

## 2.8 Comparing Platforms: GitHub vs GitLab vs Bitbucket

| Feature | GitHub | GitLab | Bitbucket |
|---|---|---|---|
| Branch protection | Excellent | Excellent | Good |
| Secret scanning | Native (Advanced Security) | Native | Via integrations |
| SAST/DAST built-in | GitHub Advanced Security | GitLab Ultimate (built-in) | Via integrations |
| CODEOWNERS | Yes | Yes | Yes |
| OIDC for CI/CD | Yes | Yes | Limited |
| Self-hosted option | GitHub Enterprise Server | GitLab Self-Managed | Bitbucket Server |
| Audit logs | Yes (Enterprise) | Yes | Yes (Enterprise) |

Most enterprises choose GitHub or GitLab for their security feature sets. GitLab has a strong built-in DevSecOps platform (SAST, DAST, dependency scanning all included). GitHub + GitHub Advanced Security is the other leading option.

---

## Chapter 2 Summary

| Topic | Key Takeaway |
|---|---|
| Why SCM security | Repos hold code, secrets, and pipeline definitions — high-value targets |
| Branch protection | Required reviews, signed commits, status checks, no force push |
| CODEOWNERS | Sensitive paths require specialist review — enforced automatically |
| Secrets detection | Pre-commit hooks + CI scanning + GitHub secret scanning |
| .gitignore | Prevent `.env` and key files from ever being committed |
| Access control | Least privilege, use GitHub Apps/OIDC instead of personal tokens |
| Org-level policies | Enforce baseline security across all repos automatically |

---

*Next: [Chapter 3 — SAST: Static Application Security Testing](03-SAST.md)*
