# Secure Coding: Hardcoded Secrets (CWE-798)

**Audience:** All developers working on Pursh or AISec  
**OWASP:** A07:2021 — Identification and Authentication Failures  
**ASVS:** V2.10.1  
**HIPAA:** §164.312(d) — Person or entity authentication  
**Gitleaks rules:** `supabase-service-role-key`, `aws-aisec-access-key`, `postgres-dsn-with-password`  
**Remediation card:** [aisec/app/mappings/remediation/CWE-798.md](../../aisec/app/mappings/remediation/CWE-798.md)

---

## What the weakness is

A hardcoded secret is any credential — API key, password, token, private key —
embedded as a string literal in source code. The danger is permanent and
multi-dimensional:

1. **Git history is forever.** Even if you delete the secret in a later commit,
   anyone with `git log` or `git show` can find it in the original commit.
2. **Repos get shared.** A private repo can become public, be forked, be cloned
   to a laptop that gets stolen, or be included in a GitHub export.
3. **Supply chain risk.** Every developer's machine, CI runner, and IDE plugin
   that clones the repo now holds the credential.

For HIPAA: a hardcoded Supabase service-role key bypasses RLS entirely — an
attacker can read every patient record in the database, violating §164.312(d).

---

## Vulnerable code

```python
# NEVER commit this
SUPABASE_URL = "https://abcdefghijklmnopqrst.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.XXXXXXXX"
DATABASE_URL = "postgresql://aisec:Sup3rS3cret@prod.rds.amazonaws.com/aisec"
```

Even this is dangerous:
```python
# Still wrong — the value is in git history
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Sup3rS3cret")
#                                             ^^^^^^^^^^^^^ hardcoded fallback
```

---

## Fixed code

**Runtime: AWS Secrets Manager (production)**

```python
import boto3, json
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_secret(secret_id: str) -> dict:
    client = boto3.client("secretsmanager", region_name="us-east-2")
    response = client.get_secret_value(SecretId=secret_id)
    return json.loads(response["SecretString"])

def get_database_url() -> str:
    return _get_secret("prod/aisec/database")["url"]

def get_supabase_key() -> str:
    return _get_secret("prod/pursh/supabase")["service_role_key"]
```

**Local dev: `.env.local` (git-ignored)**

```bash
# .gitignore already excludes .env and .env.*
# .env.local is safe for local dev only

DATABASE_URL=postgresql+asyncpg://aisec:localpass@localhost:5432/aisec
SUPABASE_URL=https://your-local-project.supabase.co
SUPABASE_KEY=your-local-anon-key
```

The app reads it via Pydantic `BaseSettings` (see `aisec/app/core/config.py`).
The `env_file=".env.local"` setting means no `.env` is ever loaded in production.

---

## How Gitleaks detects it

Gitleaks runs in two places:

1. **Pre-commit hook** (`.pre-commit-config.yaml`) — blocks the commit locally before
   it ever leaves the developer's machine.
2. **CI pipeline** (Jenkins `Secrets — Gitleaks` stage + `.github/workflows/secret-scan.yml`)
   — scans the full repo history on a schedule.

Custom rules for this repo (`scanners/gitleaks/.gitleaks.toml`):

```toml
[[rules]]
id = "supabase-service-role-key"
regex = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{43}'
severity = "critical"

[[rules]]
id = "postgres-dsn-with-password"
regex = 'postgres(?:ql)?://[^:]+:[^@]{6,}@'
severity = "critical"
```

When Gitleaks fires:
```
finding: postgres-dsn-with-password
severity: critical
file: pursh/backend/core/config.py
line: 14
secret: postgresql://aisec:Sup3rS3cret@prod.rds...
```

---

## If a secret is already committed

Do NOT just delete the file and commit again. The secret is permanently in history.

```bash
# Step 1 — rotate the credential immediately
# Log into Supabase / AWS / etc. and rotate before doing anything else

# Step 2 — remove from code
git rm pursh/backend/config.py
# or edit the file to remove the secret

# Step 3 — rewrite history (removes the secret from all past commits)
git filter-repo --path pursh/backend/config.py --invert-paths
# or target just the string: git filter-repo --replace-text <(echo "secret_value==>REMOVED")

# Step 4 — force push (coordinate with team)
git push origin main --force-with-lease

# Step 5 — verify
gitleaks detect --source . --no-git
```

---

## How to fix it next time

- **Never use a real credential as a default value** in `os.environ.get("KEY", "default")`.
- **Keep `.env.local` in `.gitignore`** — this repo's `.gitignore` already does this.
- **Use placeholder values in `.env.example`**: `SUPABASE_KEY=your-key-here` (never real).
- **Check before committing**: `gitleaks detect --source . --staged` runs automatically
  via the pre-commit hook in this repo.

---

## Compliance reference

| Framework | Control | Requirement |
|---|---|---|
| OWASP Top 10 2021 | A07:2021 | Identification and authentication failures |
| OWASP ASVS v4.0.3 | V2.10.1 | No hardcoded credentials |
| HIPAA Security Rule | §164.312(d) | Person or entity authentication |
| GDPR Art. 32 | Art32(1)(a) | Pseudonymisation and encryption |
