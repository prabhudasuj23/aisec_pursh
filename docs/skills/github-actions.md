# Skill File — GitHub Actions (CI/CD pipelines)

## Phase 0 patterns

### OIDC from GitHub Actions to AWS (no long-lived keys)

**Why:** Storing AWS access keys as GitHub secrets is a supply-chain risk.
If the secret leaks (e.g., logged in CI output), the key has unlimited
lifetime until manually rotated. GitHub OIDC instead issues a short-lived
token that AWS exchanges for ephemeral credentials — no secret to leak.

**Setup:**
1. Create `github-actions-oidc-role` in `infra/terraform/aisec/iam.tf` with
   trust policy allowing `token.actions.githubusercontent.com` as IdP.
2. In the workflow, use:
   ```yaml
   permissions:
     id-token: write
     contents: read
   steps:
     - uses: aws-actions/configure-aws-credentials@v4
       with:
         role-to-assume: arn:aws:iam::ACCOUNT_ID:role/github-actions-oidc-role
         aws-region: us-east-1
   ```
3. Role policy should be least-privilege for what that workflow actually does.

### Secret scanning workflow pattern

`secret-scan.yml` runs two modes:
- **PR mode:** `--log-opts="HEAD^..HEAD"` — scans only the diff, fast
- **Scheduled mode:** full repo history — catches old leaks

SARIF output uploaded to GitHub Security tab via `github/codeql-action/upload-sarif`.
Failures are blocking on PRs; scheduled failures create Security alerts.

### Composite action structure (scanner pattern)

Every scanner integration lives in `pipelines/github-actions/<scanner>/action.yml`.
Each composite action:
- Has its own `README.md` with input/output contract
- Accepts `severity-threshold` input (default `HIGH`)
- Outputs `sarif-file` path for the calling workflow to upload
- Is versioned independently (semver tag on the composite action)

This means replacing Semgrep with SonarQube = write one new composite action,
update one `uses:` line in the calling workflow. AISec's scanner adapters follow
the same swap-path principle.

### GitHub Actions pin-to-SHA (supply chain)

Starting Phase 2, all `uses:` references are pinned to a commit SHA:
```yaml
# Bad (mutable tag):
uses: actions/checkout@v4

# Good (immutable SHA):
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

Dependabot keeps these SHA pins up to date automatically.

### Gitleaks composite action stub (Phase 0)

`pipelines/github-actions/gitleaks/action.yml` — stub created in Phase 0.
Full implementation: the secret-scan workflow calls the official `gitleaks-action`
directly for now; the composite action stub is for future wrapping with
project-specific allowlist rules.

## Known gotchas

- `GITLEAKS_LICENSE` secret is required for org-level repos (not personal repos).
  For a personal repo, omit the env var — the free version covers it.
- `security-events: write` permission is required to upload SARIF. Add it to the
  job-level permissions block, not the workflow level, to keep least privilege.
- Pre-commit hooks run in the author's local environment. CI re-runs the same
  checks as a safety net — do not assume pre-commit passing locally means CI passes.
