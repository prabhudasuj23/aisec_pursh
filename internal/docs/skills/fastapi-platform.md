# Skill File — FastAPI Platform (AISec control plane)

## Architecture pattern (Phase 0)

AISec uses a **hexagonal architecture**:
```
HTTP request → Router (api/) → Service (services/) → Repository (repositories/)
                                      ↑
                              No business logic in routers.
                              No DB calls in services (only through repos).
```

FastAPI app is created in `aisec/app/main.py` via a factory function
`create_app()` — not at module level. This makes it testable (each test gets
a fresh app instance) and avoids import-time side effects.

## OIDC / Supabase JWT verification (Phase 0)

**Why:** AISec is an OIDC relying party. Supabase is the IdP (auth mechanism
confirmed in project setup). Every request to authenticated endpoints must carry
a valid Supabase JWT. The verification dependency is injected via FastAPI's
`Depends()` — no global state.

**How it works:**
1. Supabase issues JWTs signed with RS256 using a project-specific key pair.
2. The public key is exposed at:
   `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`
3. `aisec/app/auth/oidc.py` fetches the JWKS on startup (cached with TTL),
   verifies the JWT signature, and validates `iss`, `aud`, `exp`.
4. `require_authenticated_user` FastAPI dependency raises `HTTP 401` on any
   verification failure — never leaks details in the error body.

**Risk:** JWKS endpoint is external. If Supabase is unreachable at startup, the
app falls back to cached keys (5-min TTL). If no cache exists, startup fails
loudly rather than allowing unauthenticated access (fail closed).

**Env vars needed:**
- `SUPABASE_URL` — e.g., `https://xyzabcdef.supabase.co`
- `SUPABASE_ANON_KEY` — public anon key (safe to expose in frontend, not a secret)
- `SUPABASE_JWT_SECRET` — used for HS256 local validation fallback if RS256 fails

## Structured logging (Phase 0)

`structlog` with JSON output. Every log entry carries:
- `correlation_id` — UUID injected by middleware from `X-Request-ID` header or
  generated fresh if absent
- `environment` — from settings
- Additional context added per-module: `scanner`, `finding_id`, `repo`, `actor_id`

**Why structured JSON:** log aggregation in CloudWatch / OpenSearch requires
parseable fields. Free-text logs are unsearchable at scale.

**PHI in logs rule:** Pursh code must never log `patient_id_value`. Log the
hashed ID only. All functions touching patient data carry `# PHI-SAFE` comment.

## Settings management (Phase 0)

`pydantic-settings` reads from environment variables. No `os.getenv()` calls
outside `core/config.py`. Settings are validated at startup — the app refuses
to start with missing required config.

Local dev: `.env.local` (gitignored). Production: values injected by ECS task
definition from AWS Secrets Manager / Parameter Store.

## Known patterns to reuse

- `Depends(require_authenticated_user)` — inject on any endpoint needing auth
- `get_settings()` with `@lru_cache` — singleton settings object
- `bind_contextvars(correlation_id=...)` — add request-scoped log context
