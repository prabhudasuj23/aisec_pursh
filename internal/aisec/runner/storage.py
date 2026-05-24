"""Supabase storage adapter for AISec Runner.

Uses Supabase PostgREST REST API (stdlib urllib — no SDK) to persist:
  - scan_runs    : every scan execution with findings as JSONB
  - ai_analyses  : every DeepSeek prompt/response pair (immutable audit log)

Enterprise patterns:
  - Idempotent upserts via PostgREST on_conflict (run_id, scanner_id)
  - Circuit breaker: 3 consecutive failures → skip Supabase for 60 s
  - Graceful degradation: all methods return False/None on failure so
    callers transparently fall back to local filesystem storage
  - Env loading: reads internal/aisec/.env, overridden by os.environ
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── Configuration constants ────────────────────────────────────────────────────

# .env lives one level above runner/ (i.e. internal/aisec/.env)
_ENV_FILE = Path(__file__).parent.parent / ".env"

_CB_THRESHOLD = 3        # consecutive failures before circuit opens
_CB_RESET_SECONDS = 60   # seconds before circuit moves to half-open
_HTTP_TIMEOUT = 10       # seconds per PostgREST request


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_env_file() -> dict[str, str]:
    """Parse a simple KEY=value .env file; ignores comments and blank lines."""
    env: dict[str, str] = {}
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip()
    except Exception:
        pass
    return env


# ── Circuit breaker ────────────────────────────────────────────────────────────

class _CircuitBreaker:
    """Simple three-state circuit breaker (closed → open → half-open).

    Closed  : requests flow normally
    Open    : requests are skipped until reset_seconds have elapsed
    Half-open : one probe allowed; success → closed, failure → re-open
    """

    def __init__(self, threshold: int, reset_seconds: float) -> None:
        self._threshold = threshold
        self._reset = reset_seconds
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        elapsed = time.monotonic() - self._opened_at
        if elapsed >= self._reset:
            # Transition to half-open: reset counters, allow one probe
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold and self._opened_at is None:
            self._opened_at = time.monotonic()
            print(
                f"[storage] Circuit opened after {self._failures} failures — "
                f"skipping Supabase for {self._reset:.0f}s"
            )


# ── SupabaseStorage ────────────────────────────────────────────────────────────

class SupabaseStorage:
    """PostgREST-backed storage for scan runs and AI analyses.

    Instantiate once at module level.  All public methods return True/dict
    on success and False/None on failure.

    Why PostgREST instead of supabase-py?
      The runner is a thin local process.  stdlib urllib keeps zero extra
      dependencies while giving full access to the PostgREST HTTP API.
    """

    def __init__(self) -> None:
        # os.environ takes precedence over .env file values
        env = {**_load_env_file(), **os.environ}
        self.url = env.get("SUPABASE_URL", "").rstrip("/")
        # SUPABASE_JWT_SECRET in .env holds the service_role JWT — it bypasses RLS
        self.service_key = env.get("SUPABASE_JWT_SECRET", "")
        self._cb = _CircuitBreaker(_CB_THRESHOLD, _CB_RESET_SECONDS)
        self._ssl = ssl.create_default_context()

        if not self.url or not self.service_key:
            print(
                "[storage] SUPABASE_URL or SUPABASE_JWT_SECRET not set — "
                "Supabase storage disabled, using local filesystem only"
            )
        else:
            self._cleanup_stale_runs()

    def _cleanup_stale_runs(self) -> None:
        """On startup, mark any rows still in 'running' status as 'failed'.

        Rows get stuck as 'running' when the runner process was killed mid-scan
        (ctrl-C, crash, uvicorn --reload restart) before finish_run() was called.
        This prevents the history panel from showing permanent 'Scanning...' spinners.
        """
        if not self.healthy:
            return
        url = f"{self.url}/rest/v1/scan_runs?status=eq.running"
        body = json.dumps({"status": "failed", "exit_code": -1}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="PATCH",
            headers=self._headers({"Prefer": "return=minimal"}),
        )
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT, context=self._ssl) as resp:
                print(f"[storage] Cleaned up stale running rows (HTTP {resp.status})")
        except Exception as exc:
            print(f"[storage] Stale-run cleanup error (non-fatal): {exc}")

    # ── Health check ───────────────────────────────────────────────────────────

    @property
    def healthy(self) -> bool:
        """True when credentials are present and circuit breaker is closed."""
        return bool(self.url and self.service_key and not self._cb.is_open)

    # ── Internal request primitives ────────────────────────────────────────────

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _get(self, table: str, params: dict[str, str]) -> list[dict] | None:
        """HTTP GET against a PostgREST table with query params.

        Returns a list of row dicts, or None on any error.
        """
        if not self.healthy:
            return None
        url = f"{self.url}/rest/v1/{table}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT, context=self._ssl) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._cb.record_success()
                return data if isinstance(data, list) else [data]
        except Exception as exc:
            self._cb.record_failure()
            print(f"[storage] GET {table} error: {exc}")
            return None

    def _upsert(self, table: str, payload: dict, on_conflict: str) -> dict | None:
        """POST to PostgREST with merge-duplicates resolution (idempotent write).

        on_conflict: comma-separated column names forming the unique constraint.
        PostgREST v10+ requires on_conflict as a URL query parameter, not in Prefer.
        Returns the upserted row dict, or None on error.
        """
        if not self.healthy:
            return None
        # on_conflict MUST be a query param — putting it in Prefer causes HTTP 409
        url = f"{self.url}/rest/v1/{table}?on_conflict={urllib.parse.quote(on_conflict)}"
        prefer = "resolution=merge-duplicates,return=representation"
        body = json.dumps(payload, default=str).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers=self._headers({"Prefer": prefer}),
        )
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT, context=self._ssl) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._cb.record_success()
                return data[0] if isinstance(data, list) and data else (data or {})
        except Exception as exc:
            self._cb.record_failure()
            print(f"[storage] UPSERT {table} error: {exc}")
            return None

    def _insert(self, table: str, payload: dict) -> dict | None:
        """POST to PostgREST — insert only (no conflict resolution).

        Returns the inserted row dict, or None on error.
        """
        if not self.healthy:
            return None
        url = f"{self.url}/rest/v1/{table}"
        body = json.dumps(payload, default=str).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers=self._headers({"Prefer": "return=representation"}),
        )
        try:
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT, context=self._ssl) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._cb.record_success()
                return data[0] if isinstance(data, list) and data else (data or {})
        except Exception as exc:
            self._cb.record_failure()
            print(f"[storage] INSERT {table} error: {exc}")
            return None

    # ── Scan runs ──────────────────────────────────────────────────────────────

    def start_run(
        self,
        scanner_id: str,
        run_id: str,
        started_at: str,
        scanner_name: str = "",
    ) -> bool:
        """Insert a 'running' placeholder row at scan start.

        Writing this row immediately means the row exists in Supabase even
        if the runner crashes mid-scan — useful for auditing incomplete runs.
        """
        row: dict = {
            "run_id": run_id,
            "scanner_id": scanner_id,
            "scanner_name": scanner_name or scanner_id,
            "started_at": started_at,
            "status": "running",
            "counts": {},
            "findings_count": 0,
            "findings": [],
            "fingerprints": [],
        }
        return self._upsert("scan_runs", row, "run_id,scanner_id") is not None

    def finish_run(self, scanner_id: str, run_id: str, payload: dict) -> bool:
        """Upsert the completed scan run with all findings and intelligence.

        payload keys (all optional except run_id/scanner_id):
          started_at, finished_at, exit_code, counts, findings_count,
          findings (list[dict]), raw_output (str), fingerprints (list[str]),
          risk_score, compliance, delta, effort_minutes
        """
        exit_code = payload.get("exit_code")
        # Scanners exit 1 when they find issues — that is a successful run, not a failure.
        # Reserve 'failed' for cases where the tool itself couldn't start (exit 127, None).
        status = "failed" if exit_code in (127, None) else "completed"
        row: dict = {
            "run_id": run_id,
            "scanner_id": scanner_id,
            "scanner_name": payload.get("scanner_name", scanner_id),
            "started_at": payload.get("started_at"),
            "finished_at": payload.get("finished_at"),
            "exit_code": exit_code,
            "status": status,
            "counts": payload.get("counts", {}),
            "findings_count": payload.get("findings_count", 0),
            "findings": payload.get("findings", []),
            "raw_output": payload.get("raw_output"),
            "fingerprints": payload.get("fingerprints", []),
            "risk_score": payload.get("risk_score"),
            "compliance": payload.get("compliance"),
            "delta": payload.get("delta"),
            "effort_minutes": payload.get("effort_minutes"),
        }
        result = self._upsert("scan_runs", row, "run_id,scanner_id")
        if result is not None:
            print(f"[storage] Saved run {run_id[:8]} for {scanner_id} status={status}")
        return result is not None

    def get_latest_run(self, scanner_id: str) -> dict | None:
        """Return the most recent non-running scan for a scanner, or None.

        Accepts both 'completed' and 'failed' so a scan with findings
        (which exits 1) is still returned and shown in the dashboard.
        Falls back to local file parsing if None is returned.
        """
        rows = self._get("scan_runs", {
            "scanner_id": f"eq.{scanner_id}",
            "status": "neq.running",    # any terminal status
            "order": "created_at.desc",
            "limit": "1",
        })
        return rows[0] if rows else None

    def get_history(self, scanner_id: str, limit: int = 10) -> list[dict]:
        """Return the last N runs for a scanner, newest first.

        Selects only the columns needed for history display to minimise
        payload size (findings JSONB can be large).
        """
        rows = self._get("scan_runs", {
            "scanner_id": f"eq.{scanner_id}",
            "order": "created_at.desc",
            "limit": str(limit),
            "select": (
                "run_id,scanner_id,scanner_name,started_at,finished_at,"
                "exit_code,status,counts,findings_count,risk_score,delta,effort_minutes"
            ),
        })
        return rows or []

    # ── AI analyses ────────────────────────────────────────────────────────────

    def save_ai_analysis(
        self,
        scanner_id: str,
        run_id: str | None,
        prompt: str,
        response_raw: str,
        response_parsed: dict,
        latency_ms: int,
        cached: bool = False,
        error: str | None = None,
    ) -> bool:
        """Insert one AI analysis record.

        This table is append-only (immutable audit log).  Every call to
        DeepSeek — hit or miss — is recorded with its full prompt and
        response so you can audit what the model said and when.
        """
        row: dict = {
            "scanner_id": scanner_id,
            "run_id": run_id,
            "model": "deepseek-chat",
            "prompt": prompt,
            "response_raw": response_raw,
            "response_parsed": response_parsed,
            "prompt_chars": len(prompt),
            "response_chars": len(response_raw),
            "latency_ms": latency_ms,
            "cached": cached,
            "error": error,
        }
        return self._insert("ai_analyses", row) is not None

    def get_latest_ai_analysis(self, scanner_id: str) -> dict | None:
        """Return the most recent AI analysis row for a scanner.

        Used as a persistent cache layer: if the result file mtime matches
        the DB record's created_at scan context, skip a fresh DeepSeek call.
        """
        rows = self._get("ai_analyses", {
            "scanner_id": f"eq.{scanner_id}",
            "cached": "is.false",           # only fetch real (non-cached) analyses
            "error": "is.null",             # skip errored rows
            "order": "created_at.desc",
            "limit": "1",
        })
        return rows[0] if rows else None
