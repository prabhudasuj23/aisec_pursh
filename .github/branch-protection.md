# Branch Protection Rules — `main`

This document records the branch protection configuration applied to the `main`
branch of this repository. Rules must be re-applied manually after a repo
transfer or fork. See CLAUDE.md §5.2.

## Rules in effect

| Rule | Setting | Reason |
|---|---|---|
| Require pull request before merging | ✅ Enabled | No direct pushes to `main` |
| Required approving reviews | **1** | At minimum the owner reviews every change |
| Require review from Code Owners | ✅ Enabled | CODEOWNERS enforced on sensitive paths |
| Dismiss stale pull request approvals when new commits are pushed | ✅ Enabled | Re-approval required after each push |
| Require status checks to pass before merging | ✅ Enabled | All CI checks must be green |
| Require branches to be up to date before merging | ✅ Enabled | No stale merges |
| Require conversation resolution before merging | ✅ Enabled | All review comments resolved |
| Require signed commits | ✅ Enabled | See `commit-signing-policy.md` |
| Require linear history | ✅ Enabled | No merge commits; rebase or squash only |
| Do not allow bypassing the above settings | ✅ Enabled | Admins cannot bypass |
| Allow force pushes | ❌ Disabled | Force-push to main is forbidden |
| Allow deletions | ❌ Disabled | Branch cannot be deleted |

## Required status checks

The following CI jobs must pass before merge (updated as workflows are added):

| Phase | Check name | Workflow |
|---|---|---|
| 0 | `secret-scan` | `.github/workflows/secret-scan.yml` |
| 2 | `semgrep` | `.github/workflows/semgrep.yml` (Phase 2) |
| 3 | `trivy-fs` | `.github/workflows/trivy-fs.yml` (Phase 3) |
| 6 | `gitleaks` | `.github/workflows/secret-scan.yml` |
| 6 | `checkov` | `.github/workflows/checkov.yml` (Phase 6) |
| 7 | `zap-baseline` | `.github/workflows/zap.yml` (Phase 7) |

## How to apply these rules via GitHub CLI

```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["secret-scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null \
  --field required_linear_history=true \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_conversation_resolution=true
```

> Note: `require_signed_commits` requires a separate API call:
> ```bash
> gh api repos/{owner}/{repo}/branches/main/protection/required_signatures \
>   --method POST
> ```
