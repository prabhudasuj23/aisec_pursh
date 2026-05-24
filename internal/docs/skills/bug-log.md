# Bug Log — AISec + Pursh

Every bug fixed in this project is recorded here in the format below.
This log is read at the start of every Claude Code session and by the reviewer
agent to catch recurrence patterns.

## Format

```
### BUG-NNN — <short title>
- **Date:** YYYY-MM-DD
- **Phase:** N
- **File(s):** path/to/file.py:line
- **Bug:** What was wrong
- **Root cause:** Why it happened
- **Fix:** What was changed
- **Prevention:** How to avoid this class of bug in future
```

---

<!-- Entries are appended chronologically below this line -->

### BUG-001 — JWT issuer mismatch in auth tests
- **Date:** 2026-05-19
- **Phase:** 0
- **File(s):** `aisec/app/tests/test_auth.py`
- **Bug:** `test_valid_jwt_returns_200` returned 401 with `Invalid issuer` even though the JWT was correctly signed.
- **Root cause:** The test token had `iss = "https://test.supabase.co/auth/v1"` but `get_settings()` returns `supabase_url = ""` by default. The OIDC verifier constructs the expected issuer as `f"{supabase_url}/auth/v1"` = `"/auth/v1"`, which doesn't match.
- **Fix:** Added a `test_settings` fixture that constructs a `Settings` object with `supabase_url = "https://test.supabase.co"` and overrides the FastAPI `get_settings` dependency via `app.dependency_overrides[get_settings]`. Updated the token issuer constant `TEST_SUPABASE_URL` to be the single source of truth in the test file.
- **Prevention:** Any test that exercises code paths depending on `get_settings()` must override the dependency. Never rely on default empty-string settings values for auth-critical config. Add a startup validation in `create_app()` (Phase 1) that refuses to start if `supabase_url` is empty in non-local environments.
