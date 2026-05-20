# Secure Coding: Broken Authentication (CWE-287)

**Audience:** Backend developers working on Pursh or AISec  
**OWASP:** A07:2021 — Identification and Authentication Failures  
**ASVS:** V2.1.1, V3.2.2, V3.3.1, V3.5.2  
**HIPAA:** §164.312(d) — Person or entity authentication  
**Semgrep rules:** `python.jwt.security.jwt-none-alg`, `python.jwt.security.unverified-jwt-decode`  
**Remediation card:** [aisec/app/mappings/remediation/CWE-287.md](../../aisec/app/mappings/remediation/CWE-287.md)

---

## What the weakness is

Broken authentication means the application fails to correctly verify who is making
a request. The most common JWT-specific failures are:

| Failure | What an attacker does | Impact |
|---|---|---|
| `alg: none` accepted | Strips the signature and changes claims | Full bypass — impersonate any user |
| No expiry check | Reuses a stolen token after it should have expired | Persistent access after logout or rotation |
| Wrong signing key | Signs with a different key (e.g. RS256 public key as HS256 secret) | Forges tokens if public key is known |
| Missing claim validation | Omits `sub` or `role` | Privilege escalation or identity confusion |
| JWKS not refreshed | Old key stays in cache after rotation | Valid tokens rejected, or compromised key stays trusted |

For HIPAA §164.312(d): if any of these allow an unauthenticated request to reach
patient data, it is a breach of the person/entity authentication requirement.

---

## Vulnerable code

```python
import jwt

# NEVER 1 — no signature verification
def get_user(token: str) -> dict:
    return jwt.decode(token, options={"verify_signature": False})

# NEVER 2 — accepts alg:none explicitly
def get_user(token: str) -> dict:
    return jwt.decode(token, key="", algorithms=["none", "RS256"])

# NEVER 3 — no expiry check
def get_user(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"],
                      options={"verify_exp": False})
```

---

## Fixed code (this repo's pattern — RS256 + JWKS)

```python
# aisec/app/auth/oidc.py — the canonical implementation
import httpx
from jose import jwt, JWTError
from functools import lru_cache
from datetime import datetime, timezone

_jwks_cache: dict = {}
_jwks_fetched_at: datetime | None = None
JWKS_TTL_SECONDS = 300


async def _get_jwks(jwks_url: str) -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = datetime.now(timezone.utc)
    if (
        _jwks_fetched_at is None
        or (now - _jwks_fetched_at).total_seconds() > JWKS_TTL_SECONDS
    ):
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(jwks_url)
            r.raise_for_status()
            _jwks_cache = r.json()
            _jwks_fetched_at = now
    return _jwks_cache


async def verify_token(token: str, jwks_url: str) -> dict:
    jwks = await _get_jwks(jwks_url)

    payload = jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],   # explicit allowlist — never ["*"] or ["none"]
        options={
            "verify_exp": True,   # expiry check always on (this is the default)
            "verify_aud": False,  # audience skipped — Supabase does not set it
        },
    )

    # Validate required claims explicitly
    for required in ("sub", "email"):
        if required not in payload:
            raise JWTError(f"Missing required claim: {required}")

    return payload
```

Key decisions in this pattern:
- `algorithms=["RS256"]` — explicit list; no wildcards; `none` impossible
- `verify_exp=True` — the default, but stated explicitly so a future reader cannot miss it
- JWKS cached for 300 s — avoids latency on every request; refreshed automatically
- Required claims validated after decode — missing `sub` is rejected with 401

---

## How Semgrep detects it

```
# Rule: python.jwt.security.jwt-none-alg
# Fires on: algorithms=["none"] or algorithms=["none", ...]
Finding: jwt-none-alg
File: pursh/backend/auth/supabase.py
Line: 22
Message: JWT decoded with "none" algorithm — signature is not verified.

# Rule: python.jwt.security.unverified-jwt-decode
# Fires on: options={"verify_signature": False}
Finding: unverified-jwt-decode
File: pursh/backend/auth/supabase.py
Line: 18
Message: JWT decoded without signature verification.
```

---

## How to fix it next time

- **Always specify `algorithms=["RS256"]`** — or whatever algorithm your IdP uses.
  Never omit it, never use a wildcard.
- **Never set `verify_exp=False`** — there is no legitimate reason to skip expiry.
- **Validate required claims after decode** — `sub` is the user identity; missing it
  means you do not know who is making the request.
- **Refresh JWKS on a TTL** — don't hardcode a public key; the IdP may rotate it.
- **Test the failure cases:**

```python
# Test: expired token must return 401
def test_expired_token(client):
    expired = make_token(exp=datetime.now() - timedelta(hours=1))
    resp = client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401

# Test: alg:none must return 401
def test_alg_none(client):
    crafted = jwt.encode({"sub": "hacker"}, "", algorithm="none")
    resp = client.get("/api/v1/me", headers={"Authorization": f"Bearer {crafted}"})
    assert resp.status_code == 401
```

Both tests exist in `aisec/app/tests/test_auth.py`.

---

## ASVS V3 session checklist

| Control | Requirement | Status |
|---|---|---|
| V3.2.2 | CSRF tokens on state-changing requests | ✅ Not applicable (JWT Bearer, no cookies) |
| V3.3.1 | Session timeout ≤ 30 min | ✅ Supabase: 15-min idle |
| V3.5.2 | Stateless session tokens use RS256/ES256 | ✅ RS256 enforced |
| V2.6.1 | MFA available | ✅ Supabase TOTP (enable in project settings) |

---

## Compliance reference

| Framework | Control | Requirement |
|---|---|---|
| OWASP Top 10 2021 | A07:2021 | Identification and authentication failures |
| OWASP ASVS v4.0.3 | V3.5.2 | Stateless token algorithms |
| HIPAA Security Rule | §164.312(d) | Person or entity authentication |
| HIPAA Security Rule | §164.312(a)(2)(iii) | Automatic logoff |
| GDPR Art. 32 | Art32(1)(b) | Confidentiality and integrity |
