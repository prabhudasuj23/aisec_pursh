## Description

<!-- What does this PR do? 2–4 sentences max. -->

## CLAUDE.md Phase

Phase <!-- N --> — <!-- phase name -->

## Exit criteria met

<!-- Copy the exit criteria from CLAUDE.md §7 for this phase and check each one -->

- [ ] ...

## Security checklist

<!-- Every PR must answer these. "N/A" is a valid answer with a reason. -->

### Threat model
- [ ] Does this PR add a new service, endpoint, or data flow?
  - If yes: has `/docs/threat-models/<service>.md` been created or updated?
- [ ] Does this PR modify an existing service's trust boundary?
  - If yes: has the relevant threat model been reviewed and updated?

### Authentication & authorization
- [ ] Does this PR touch auth code (`/auth/`, OIDC, Supabase Auth, JWT)?
  - If yes: has the auth logic been reviewed for bypass conditions?
- [ ] Does this PR add or modify API endpoints?
  - If yes: are all endpoints protected by the correct RBAC dependency?

### Secrets & credentials
- [ ] Are there any new environment variables or config values in this PR?
  - If yes: are they sourced from AWS Secrets Manager / Parameter Store, not hardcoded?
- [ ] Has `gitleaks` / `detect-secrets` pre-commit hook passed cleanly?
- [ ] Does this PR add new AWS resources?
  - If yes: do they follow least-privilege IAM (no `*` actions without justification)?

### Pursh PHI surface (only if Pursh files changed)
- [ ] Do any new functions touch patient data?
  - If yes: do they carry `# PHI-SAFE` annotation and have a corresponding RLS test?
- [ ] Are LLM calls PHI-free at the boundary (redaction layer in place)?
- [ ] Does the UI show the two required disclaimers on every page that touches patient data?
- [ ] Does no code path, log line, or comment claim Pursh is "HIPAA-compliant"?

### Scanner & pipeline
- [ ] Does this PR add or modify a scanner integration?
  - If yes: are contract tests updated and schema validator in place?
- [ ] Does this PR change CI workflows?
  - If yes: does it maintain OIDC-to-AWS (no long-lived keys)?

### Dependencies
- [ ] Does this PR add new Python packages?
  - If yes: have they been checked with `pip-audit` or Trivy fs?
- [ ] Does this PR add new npm packages?
  - If yes: have they been checked with `npm audit`?

## How to test

```bash
# Replace with concrete commands for this PR
pytest aisec/app/tests/ -v
```

## Known limitations / follow-ups

<!-- Honest list. Nothing is too small to mention. -->

- N/A
