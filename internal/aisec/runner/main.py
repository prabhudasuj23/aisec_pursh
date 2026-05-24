"""AISec Runner — FastAPI backend for the DevSec dashboard.

Endpoints:
  GET  /healthz                — liveness probe
  GET  /scanners               — list available scanners
  GET  /results/{scanner_id}   — return parsed scan results JSON
  POST /run/{scanner_id}       — start scanner subprocess (background, no stream)
  POST /stop/{scanner_id}      — terminate running scanner
  GET  /stream/{scanner_id}    — SSE stream of live scanner stdout; ?image= for image scanners
  GET  /precheck/{scanner_id}  — run prerequisite checks, return pass/fail list
  GET  /history/{scanner_id}   — return last 5 run summaries
  POST /build-image            — queue a docker build (stores params for stream)
  GET  /stream/build-image     — SSE stream of docker build output
"""
import asyncio
import datetime
import json
import os
import shutil
import time
import urllib.request
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from scanners import SCANNERS, SCAN_RESULTS_DIR
from storage import SupabaseStorage

app = FastAPI(title="AISec Runner", version="2.0.0")

# Module-level storage singleton — all endpoints share one circuit breaker
_storage = SupabaseStorage()


def _parse_json_from_mixed_output(text: str) -> object:
    """Parse JSON from output that may contain leading log lines or multiple JSON objects.
    Finds the first { or [ that starts at a line boundary, then uses raw_decode so trailing
    log lines (a second JSON block, progress output) don't cause parse failures."""
    import re as _re
    m = _re.search(r"(?:^|\n)(\{|\[)", text)
    start = m.start(1) if m else next((i for i, ch in enumerate(text) if ch in ("{", "[")), 0)
    obj, _ = json.JSONDecoder().raw_decode(text, start)
    return obj

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000", "http://localhost:3001"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── State ──────────────────────────────────────────────────────────────────────

# Track running scanner processes: scanner_id → asyncio subprocess
_running: dict[str, asyncio.subprocess.Process] = {}

# Pending docker build params set by POST /build-image, consumed by GET /stream/build-image
_pending_build: dict[str, str] = {}

# ── History helpers ────────────────────────────────────────────────────────────

HISTORY_DIR = SCAN_RESULTS_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)
MAX_HISTORY = 5


def _load_history(scanner_id: str) -> list[dict]:
    p = HISTORY_DIR / f"{scanner_id}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    except Exception:
        return []


def _save_history(scanner_id: str, entry: dict) -> None:
    history = _load_history(scanner_id)
    history.insert(0, entry)
    (HISTORY_DIR / f"{scanner_id}.json").write_text(
        json.dumps(history[:MAX_HISTORY], indent=2), encoding="utf-8"
    )


# ── Pre-check helpers ──────────────────────────────────────────────────────────

# Root of the monorepo (four levels up from internal/aisec/runner/)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
EXE = ".exe" if os.name == "nt" else ""


def _pc(name: str, status: str, message: str, blocking: bool = True) -> dict:
    return {"name": name, "status": status, "message": message, "blocking": blocking}


async def _check_tool_on_path(tool: str, name: str) -> dict:
    found = shutil.which(tool)
    if found:
        return _pc(name, "pass", f"Found: {found}")
    return _pc(name, "fail", f"'{tool}' not found on PATH. Install it and restart the runner.")


async def _check_python_module(module: str, name: str) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", module, "--version",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=10)
        ok = proc.returncode == 0
    except Exception:
        ok = False
    return _pc(name, "pass" if ok else "fail",
               "Module is available." if ok else f"Run: pip install {module.split('.')[0]}")


async def _check_docker_daemon() -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=6)
        ok = proc.returncode == 0
    except Exception:
        ok = False
    return _pc("Docker daemon reachable",
               "pass" if ok else "fail",
               "Docker Desktop is running." if ok else "Start Docker Desktop and try again.")


async def _check_http(url: str, name: str, error_hint: str) -> dict:
    try:
        urllib.request.urlopen(url, timeout=3)
        return _pc(name, "pass", f"Reachable at {url}")
    except Exception:
        return _pc(name, "fail", error_hint)


async def _check_path_exists(path: str, name: str) -> dict:
    exists = Path(path).exists()
    return _pc(name,
               "pass" if exists else "fail",
               f"Found: {path}" if exists else f"Not found: {path}")


# Per-scanner pre-check registry: list of async callables → PreCheckItem dict
PRECHECKS: dict[str, list] = {
    "semgrep": [
        lambda: _check_tool_on_path("semgrep", "semgrep on PATH"),
        lambda: _check_path_exists(
            str(REPO_ROOT / "internal" / "scanners" / "semgrep" / "custom-rules.yaml"),
            "Custom rules YAML present",
        ),
        lambda: _check_path_exists(str(REPO_ROOT / "pursh"), "pursh/ target directory present"),
    ],
    "trivy-sca": [
        lambda: _check_tool_on_path("trivy", "trivy on PATH"),
        lambda: _check_path_exists(str(REPO_ROOT / "pursh"), "pursh/ target directory present"),
    ],
    "trivy-image": [
        lambda: _check_tool_on_path("trivy", "trivy on PATH"),
        lambda: _check_docker_daemon(),
    ],
    "gitleaks": [
        lambda: _check_path_exists(
            str(REPO_ROOT / "internal" / "scanners" / "gitleaks-bin" / f"gitleaks{EXE}"),
            f"gitleaks{EXE} binary present",
        ),
        lambda: _check_path_exists(
            str(REPO_ROOT / "internal" / "scanners" / "gitleaks" / ".gitleaks.toml"),
            ".gitleaks.toml config present",
        ),
    ],
    "grype": [
        lambda: _check_path_exists(
            str(REPO_ROOT / "internal" / "scanners" / "grype-bin" / f"grype{EXE}"),
            f"grype{EXE} binary present",
        ),
        lambda: _check_path_exists(str(REPO_ROOT / "pursh"), "pursh/ target directory present"),
    ],
    "checkov": [
        lambda: _check_tool_on_path("python", "Python on PATH"),
        lambda: _check_python_module("checkov.main", "checkov Python module installed"),
        lambda: _check_path_exists(
            str(REPO_ROOT / "internal" / "infra" / "terraform"),
            "internal/infra/terraform/ directory present",
        ),
    ],
    "syft": [
        lambda: _check_tool_on_path("syft", "syft on PATH"),
        lambda: _check_path_exists(str(REPO_ROOT / "pursh"), "pursh/ target directory present"),
    ],
    "zap": [
        lambda: _check_docker_daemon(),
        lambda: _check_http(
            "http://localhost:3000",
            "Pursh frontend reachable on :3000",
            "Start Pursh frontend: cd pursh/frontend && npm run dev",
        ),
        lambda: _check_http(
            "http://localhost:8001",
            "Pursh backend reachable on :8001",
            "Start Pursh backend: cd pursh/backend && uvicorn main:app --port 8001",
        ),
    ],
    "nikto": [
        lambda: _check_docker_daemon(),
        lambda: _check_http(
            "http://localhost:3000",
            "Pursh frontend reachable on :3000",
            "Start Pursh frontend: cd pursh/frontend && npm run dev",
        ),
    ],
    "schemathesis": [
        lambda: _check_tool_on_path("schemathesis", "schemathesis on PATH"),
        lambda: _check_http(
            "http://localhost:8001/openapi.json",
            "Pursh OpenAPI schema reachable on :8001",
            "Start Pursh backend: cd pursh/backend && uvicorn main:app --port 8001",
        ),
    ],
    "trufflehog": [
        lambda: _check_docker_daemon(),
        lambda: _check_path_exists(str(REPO_ROOT / "pursh"), "pursh/ target directory present"),
    ],
    "dependency-check": [
        lambda: _check_docker_daemon(),
        lambda: _check_path_exists(str(REPO_ROOT / "pursh"), "pursh/ target directory present"),
    ],
    "kics": [
        lambda: _check_docker_daemon(),
        lambda: _check_path_exists(
            str(REPO_ROOT / "internal" / "infra" / "terraform"),
            "internal/infra/terraform/ directory present",
        ),
    ],
    "nuclei": [
        lambda: _check_docker_daemon(),
        lambda: _check_http(
            "http://localhost:3000",
            "Pursh frontend reachable on :3000",
            "Start Pursh frontend: cd pursh/frontend && npm run dev",
        ),
    ],
    "nmap": [
        lambda: _check_tool_on_path("nmap", "nmap on PATH"),
    ],
    "openvas": [
        lambda: _check_path_exists(
            str(SCAN_RESULTS_DIR / "openvas-report.xml"),
            "openvas-report.xml present (export from Greenbone UI)",
        ),
    ],
    "suricata": [
        lambda: _check_path_exists(
            str(SCAN_RESULTS_DIR / "suricata-eve.json"),
            "suricata-eve.json present (copy from /var/log/suricata/eve.json)",
        ),
    ],
    "zeek": [
        lambda: _check_path_exists(
            str(SCAN_RESULTS_DIR / "zeek-notice.log"),
            "zeek-notice.log present (copy from /opt/zeek/logs/current/notice.log)",
        ),
    ],
}

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/scanners")
async def list_scanners():
    return {
        sid: {"label": s["label"], "result_file": s["result_file"], "type": s["type"]}
        for sid, s in SCANNERS.items()
    }


def _to_finding(scanner_id: str, raw_f: dict, scanned_at: str | None) -> dict:
    """Map the runner normalizer dict → Finding shape expected by the dashboard."""
    cwe_raw = raw_f.get("cwe", "")
    cwe_list = [c.strip() for c in cwe_raw.split(",") if c.strip()] if cwe_raw else []
    sev = (raw_f.get("severity") or "INFO").upper()
    if sev not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        sev = "INFO"
    message = raw_f.get("message") or raw_f.get("rule") or "Finding"
    return {
        "id": str(uuid.uuid4()),
        "scanner": scanner_id,
        "rule_id": raw_f.get("rule", ""),
        "severity": sev,
        "title": message[:120],
        "description": message,
        "file": raw_f.get("file") or None,
        "line": raw_f.get("line") or None,
        "cwe": cwe_list,
        "owasp_top10": None,
        "asvs": [],
        "hipaa": [],
        "gdpr": [],
        "remediation": raw_f.get("fix") or None,
        "status": "open",
        "scanned_at": scanned_at,
    }


@app.get("/findings")
async def get_findings(scanner: str | None = Query(default=None)):
    """Aggregate findings across all (or one) scanner result files."""
    scanner_ids = [scanner] if scanner and scanner in SCANNERS else list(SCANNERS.keys())
    all_findings: list[dict] = []
    for sid in scanner_ids:
        result_file = SCAN_RESULTS_DIR / SCANNERS[sid]["result_file"]
        if not result_file.exists():
            continue
        try:
            raw = _parse_result_file(sid, result_file)
        except Exception:
            continue
        scanned_at = _mtime(result_file)
        raw_findings = _normalise(sid, raw)
        all_findings.extend(_to_finding(sid, f, scanned_at) for f in raw_findings)
    return {"findings": all_findings, "total": len(all_findings)}


@app.get("/results/{scanner_id}")
async def get_results(scanner_id: str):
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")

    # Primary source: Supabase — returns the last completed run with all fields pre-computed
    db_run = _storage.get_latest_run(scanner_id)
    if db_run:
        return {
            "scanner": scanner_id,
            "status": db_run.get("status", "ok"),
            "counts": db_run.get("counts", {}),
            "findings": db_run.get("findings", []),
            "scanned_at": db_run.get("finished_at"),
            "scan_meta": {},
            "risk_score": db_run.get("risk_score"),
            "compliance": db_run.get("compliance"),
            "delta": db_run.get("delta"),
            "raw": None,
            "_source": "supabase",
        }

    # Fallback: parse local result file (existing behaviour unchanged)
    result_file = SCAN_RESULTS_DIR / SCANNERS[scanner_id]["result_file"]
    if not result_file.exists():
        return {"scanner": scanner_id, "status": "no_data", "findings": [], "raw": None}

    try:
        raw = _parse_result_file(scanner_id, result_file)
    except Exception:
        return {"scanner": scanner_id, "status": "parse_error", "findings": [], "raw": None}

    raw_findings = _normalise(scanner_id, raw)
    scanned_at = _mtime(result_file)
    counts = _count_severities(raw_findings)
    status = _derive_status(counts)
    scan_meta = _scan_summary(scanner_id, raw)

    history = _load_history(scanner_id)
    risk_score = _calc_risk_score(counts, history)
    compliance = _compliance_impact(raw_findings)
    delta = _delta_vs_last_scan(scanner_id, raw_findings)
    findings_with_effort = [_to_finding(scanner_id, f, scanned_at) for f in _annotate_findings_with_effort(raw_findings)]

    return {
        "scanner": scanner_id,
        "status": status,
        "counts": counts,
        "findings": findings_with_effort,
        "scanned_at": scanned_at,
        "scan_meta": scan_meta,
        "risk_score": risk_score,
        "compliance": compliance,
        "delta": delta,
        "raw": raw,
    }


@app.get("/scanners-status")
async def scanners_status():
    """Batch endpoint — returns status + counts for ALL scanners in one call.

    The dashboard home page calls this once instead of making 28 individual
    /results/{id} calls.  Results are computed from local result files only
    (no Supabase round-trip per scanner) and cached for 30 seconds.
    """
    import time as _time
    now = _time.monotonic()
    cached = getattr(app.state, "_status_cache", None)
    if cached and now - cached["ts"] < 30:
        return cached["data"]

    out: dict[str, dict] = {}
    for sid, scanner in SCANNERS.items():
        result_file = SCAN_RESULTS_DIR / scanner["result_file"]
        if not result_file.exists():
            out[sid] = {"status": "no_data", "counts": {}, "scanned_at": None}
            continue
        try:
            raw = _parse_result_file(sid, result_file)
            findings = _normalise(sid, raw)
            counts = _count_severities(findings)
            status = _derive_status(counts)
            out[sid] = {"status": status, "counts": counts, "scanned_at": _mtime(result_file)}
        except Exception:
            out[sid] = {"status": "parse_error", "counts": {}, "scanned_at": None}

    payload = {"scanners": out}
    app.state._status_cache = {"ts": now, "data": payload}
    return payload


@app.get("/history/{scanner_id}")
async def get_history(scanner_id: str):
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")
    # History is authoritative in Supabase — the dashboard queries Supabase
    # directly via its own API route (/api/history/[scanner]) with auth.
    # This runner endpoint exists for debugging/tooling only.
    runs = _storage.get_history(scanner_id, limit=10)
    return {"scanner_id": scanner_id, "source": "supabase", "history": runs}


@app.get("/precheck/{scanner_id}")
async def precheck(scanner_id: str):
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")
    check_fns = PRECHECKS.get(scanner_id, [])

    async def _safe_check(fn) -> dict:
        try:
            return await fn()
        except Exception as exc:
            return _pc("check (error)", "fail", str(exc))

    # Run all pre-checks in parallel — sequential await meant 3-12s for scanners
    # with multiple timeout-based checks (docker ping, HTTP reachability, etc.)
    results: list[dict] = await asyncio.gather(*[_safe_check(fn) for fn in check_fns])
    all_pass = all(c["status"] == "pass" for c in results if c.get("blocking", True))
    return {"scanner_id": scanner_id, "checks": results, "all_pass": all_pass}


@app.post("/run/{scanner_id}")
async def run_scanner(scanner_id: str):
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")
    if scanner_id in _running and _running[scanner_id].returncode is None:
        return {"status": "already_running"}

    scanner = SCANNERS[scanner_id]
    result_file = SCAN_RESULTS_DIR / scanner["result_file"]
    cmd = scanner["command"]
    write_stdout = scanner.get("write_stdout", scanner_id not in ("gitleaks",))

    async def _run():
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(REPO_ROOT),
            )
        except Exception:
            return
        _running[scanner_id] = proc
        output_lines: list[str] = []
        async for line in proc.stdout:  # type: ignore[union-attr]
            output_lines.append(line.decode(errors="replace").rstrip())
        await proc.wait()
        if write_stdout and output_lines:
            try:
                result_file.write_text("\n".join(output_lines), encoding="utf-8")
            except Exception:
                pass

    asyncio.create_task(_run())
    return {"status": "started", "scanner": scanner_id}


@app.post("/stop/{scanner_id}")
async def stop_scanner(scanner_id: str):
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")
    proc = _running.get(scanner_id)
    if proc is None or proc.returncode is not None:
        return {"status": "not_running"}
    try:
        proc.terminate()
        await asyncio.wait_for(proc.wait(), timeout=5)
    except asyncio.TimeoutError:
        proc.kill()
    _running.pop(scanner_id, None)
    return {"status": "stopped", "scanner": scanner_id}


@app.post("/build-image")
async def queue_build(request: Request):
    body = await request.json()
    dockerfile_path = body.get("dockerfile_path", "")
    tag = body.get("tag", "aisec-scan-target:latest")
    abs_dockerfile = REPO_ROOT / dockerfile_path
    if not abs_dockerfile.exists():
        raise HTTPException(status_code=400, detail=f"Dockerfile not found: {dockerfile_path}")
    _pending_build["dockerfile"] = str(abs_dockerfile)
    _pending_build["context"] = str(abs_dockerfile.parent)
    _pending_build["tag"] = tag
    return {"status": "build_queued", "tag": tag, "dockerfile": dockerfile_path}


@app.get("/stream/build-image")
async def stream_build():
    """SSE stream — runs docker build for the params set by POST /build-image."""
    dockerfile = _pending_build.get("dockerfile")
    context = _pending_build.get("context")
    tag = _pending_build.get("tag", "aisec-scan-target:latest")

    async def build_gen():
        if not dockerfile:
            yield {"data": "[error] No build queued. Call POST /build-image first."}
            yield {"event": "done", "data": json.dumps({"exit_code": 1, "tag": None})}
            return

        yield {"data": f"[AISec Runner] Building Docker image {tag}..."}
        yield {"data": f"[AISec Runner] Dockerfile: {dockerfile}"}

        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "build", "-f", dockerfile, "-t", tag, context,  # type: ignore[arg-type]
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            yield {"data": "[error] 'docker' not found. Is Docker Desktop running?"}
            yield {"event": "done", "data": json.dumps({"exit_code": 127, "tag": None})}
            return
        except Exception as exc:
            yield {"data": f"[error] Failed to start build: {exc}"}
            yield {"event": "done", "data": json.dumps({"exit_code": 1, "tag": None})}
            return

        async for raw in proc.stdout:  # type: ignore[union-attr]
            yield {"data": raw.decode(errors="replace").rstrip()}
            await asyncio.sleep(0)

        await proc.wait()
        rc = proc.returncode
        result_tag = tag if rc == 0 else None
        yield {"data": f"[AISec Runner] Build exit {rc} — {'Done' if rc == 0 else 'Build failed'}"}
        yield {"event": "done", "data": json.dumps({"exit_code": rc, "tag": result_tag})}

    return EventSourceResponse(build_gen())


@app.get("/stream/{scanner_id}")
async def stream_output(scanner_id: str, image: str | None = Query(default=None)):
    """SSE endpoint — streams live stdout of the running scanner.
    For trivy-image, pass ?image=<tag> to scan a specific Docker image instead of fs.
    """
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")

    # Guard: reject if this scanner is already running — prevents duplicate start_run() rows
    # (caused by React StrictMode double-invoke or EventSource auto-reconnect)
    if scanner_id in _running and _running[scanner_id].returncode is None:
        async def _already_running():
            yield {"data": f"[AISec Runner] {SCANNERS[scanner_id]['label']} is already running. Wait for it to finish."}
            yield {"event": "done", "data": json.dumps({"exit_code": 0})}
        return EventSourceResponse(_already_running())

    scanner = SCANNERS[scanner_id]
    result_file = SCAN_RESULTS_DIR / scanner["result_file"]
    write_stdout = scanner.get("write_stdout", scanner_id not in ("gitleaks",))

    # Resolve the command — trivy-image with a built image uses image scan mode
    if scanner_id == "trivy-image" and image:
        cmd = ["trivy", "image", image, "--format", "json", "--severity", "CRITICAL,HIGH"]
    else:
        cmd = scanner["command"]

    async def event_generator():
        run_id = str(uuid.uuid4())
        started_at = datetime.datetime.utcnow().isoformat()

        # Write a 'running' row immediately so the run is visible in Supabase
        # even if the process crashes before finishing
        _storage.start_run(scanner_id, run_id, started_at, scanner.get("label", scanner_id))

        yield {"data": f"[AISec Runner] Starting {scanner['label']}..."}
        if scanner_id == "trivy-image" and image:
            yield {"data": f"[AISec Runner] Scanning image: {image}"}

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(REPO_ROOT),
            )
        except FileNotFoundError:
            yield {"data": f"[error] Tool not found: '{cmd[0]}'. Is it installed and on PATH?"}
            yield {"data": "[AISec Runner] Exit code 127 — Tool missing"}
            yield {"event": "done", "data": json.dumps({"exit_code": 127})}
            return
        except Exception as exc:
            yield {"data": f"[error] Failed to start scanner: {exc}"}
            yield {"data": "[AISec Runner] Exit code 1 — Launch error"}
            yield {"event": "done", "data": json.dumps({"exit_code": 1})}
            return

        _running[scanner_id] = proc
        output_lines: list[str] = []

        async for raw_line in proc.stdout:  # type: ignore[union-attr]
            line = raw_line.decode(errors="replace").rstrip()
            output_lines.append(line)
            yield {"data": line}
            await asyncio.sleep(0)

        await proc.wait()
        rc = proc.returncode

        if write_stdout and output_lines:
            try:
                result_file.write_text("\n".join(output_lines), encoding="utf-8")
            except Exception:
                pass

        # Derive counts for history entry
        raw_data: object = {}
        try:
            raw_data = _parse_result_file(scanner_id, result_file) if result_file.exists() else {}
            findings = _normalise(scanner_id, raw_data)
            counts = _count_severities(findings)
        except Exception:
            counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        finished_at = datetime.datetime.utcnow().isoformat()

        # Build enriched history entry — same shape as before, so local fallback works
        entry: dict = {
            "run_id": run_id,
            "scanner_id": scanner_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": rc,
            "counts": counts,
            "findings_count": sum(counts.values()),
        }
        if scanner_id == "trivy-image" and image:
            entry["image_tag"] = image

        # Compute intelligence fields so the finished run is fully enriched in Supabase
        try:
            history_so_far = _load_history(scanner_id)
            risk_score = _calc_risk_score(counts, history_so_far)
            raw_findings_full = _normalise(scanner_id, raw_data) if raw_data else []
            compliance = _compliance_impact(raw_findings_full)
            delta = _delta_vs_last_scan(scanner_id, raw_findings_full)
            annotated = _annotate_findings_with_effort(raw_findings_full)
            effort_minutes = sum(f.get("fix_effort", {}).get("minutes", 0) for f in annotated)
            fingerprints = [
                f"{f.get('rule', '')}|{f.get('file', '')}|{f.get('severity', '')}"
                for f in raw_findings_full
            ]
            normalized_findings = [_to_finding(scanner_id, f, finished_at) for f in annotated]
        except Exception as _enrich_err:
            import traceback as _tb
            print(f"[runner] WARNING: post-scan enrichment failed for {scanner_id}: {_enrich_err}")
            _tb.print_exc()
            risk_score = None
            compliance = None
            delta = None
            effort_minutes = 0
            fingerprints = []
            normalized_findings = []

        # Persist to Supabase — falls back silently to local if Supabase is down
        supabase_payload = {
            **entry,
            "scanner_name": scanner.get("label", scanner_id),
            "findings": normalized_findings,
            "raw_output": "\n".join(output_lines[-200:]),  # last 200 lines to cap size
            "fingerprints": fingerprints,
            "risk_score": risk_score,
            "compliance": compliance,
            "delta": delta,
            "effort_minutes": effort_minutes,
        }
        saved = _storage.finish_run(scanner_id, run_id, supabase_payload)

        # Local filesystem fallback — always write so the runner works offline
        _save_history(scanner_id, entry)
        if not saved:
            print(f"[runner] Supabase unavailable — run {run_id[:8]}… saved locally only")

        yield {"data": f"[AISec Runner] Exit code {rc} — {'Done' if rc == 0 else 'Completed with warnings'}"}
        yield {"event": "done", "data": json.dumps({"exit_code": rc})}

    return EventSourceResponse(event_generator())


# ── Normalisers ────────────────────────────────────────────────────────────────

def _normalise(scanner_id: str, raw: object) -> list[dict]:
    stype = SCANNERS[scanner_id]["type"]
    try:
        if stype == "semgrep":          return _norm_semgrep(raw)
        if stype == "trivy":            return _norm_trivy(raw)
        if stype == "gitleaks":         return _norm_gitleaks(raw)
        if stype == "grype":            return _norm_grype(raw)
        if stype == "checkov":          return _norm_checkov(raw)
        if stype == "zap":              return _norm_zap(raw)
        if stype == "nikto":            return _norm_nikto(raw)
        if stype == "schemathesis":     return _norm_schemathesis(raw)
        if stype == "trufflehog":       return _norm_trufflehog(raw)
        if stype == "dependency_check": return _norm_dependency_check(raw)
        if stype == "kics":             return _norm_kics(raw)
        if stype == "nuclei":           return _norm_nuclei(raw)
        if stype == "nmap":             return _norm_nmap(raw)
        if stype == "openvas":          return _norm_openvas(raw)
        if stype == "suricata":            return _norm_suricata(raw)
        if stype == "zeek":               return _norm_zeek(raw)
        if stype == "detect_secrets":     return _norm_detect_secrets(raw)
        if stype == "tfsec":              return _norm_tfsec(raw)
        # CloudSec stubs — return info message as a single INFO finding
        if stype in ("prowler","scoutsuite","guardduty","inspector",
                     "macie","iam_access_analyzer","promptfoo","garak"):
            return _norm_stub_info(raw, stype)
    except Exception:
        pass
    return []


def _sev(s: str) -> str:
    return (s or "info").upper()


def _norm_semgrep(raw: object) -> list[dict]:
    results = raw.get("results", []) if isinstance(raw, dict) else []  # type: ignore[union-attr]
    return [{
        "severity": _sev(r.get("extra", {}).get("severity", "info")),
        "rule": r.get("check_id", ""),
        "file": r.get("path", ""),
        "line": r.get("start", {}).get("line", ""),
        "message": r.get("extra", {}).get("message", ""),
        "cwe": ", ".join(r.get("extra", {}).get("metadata", {}).get("cwe", [])),
        "fix": r.get("extra", {}).get("fix", ""),
    } for r in results]


def _norm_trivy(raw: object) -> list[dict]:
    out = []
    if not isinstance(raw, dict):
        return out
    for result in raw.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            out.append({
                "severity": _sev(vuln.get("Severity", "info")),
                "rule": vuln.get("VulnerabilityID", ""),
                "file": result.get("Target", ""),
                "line": "",
                "message": vuln.get("Title", vuln.get("Description", ""))[:200],
                "cwe": ", ".join(vuln.get("CweIDs", [])),
                "fix": vuln.get("FixedVersion", ""),
            })
    return out


def _norm_gitleaks(raw: object) -> list[dict]:
    return [{
        "severity": "CRITICAL",
        "rule": r.get("RuleID", r.get("Description", "")),
        "file": r.get("File", ""),
        "line": r.get("StartLine", ""),
        "message": r.get("Description", ""),
        "cwe": "CWE-798",
        "fix": "Rotate the secret immediately and remove from history",
    } for r in (raw if isinstance(raw, list) else [])]


def _norm_grype(raw: object) -> list[dict]:
    out = []
    if not isinstance(raw, dict):
        return out
    for match in raw.get("matches", []):
        vuln = match.get("vulnerability", {})
        fix_versions = vuln.get("fix", {}).get("versions", [])
        out.append({
            "severity": _sev(vuln.get("severity", "info")),
            "rule": vuln.get("id", ""),
            "file": match.get("artifact", {}).get("name", ""),
            "line": "",
            "message": (vuln.get("description") or "")[:200],
            "cwe": ", ".join(vuln.get("cpes", [])[:2]),
            "fix": fix_versions[0] if fix_versions else "",
        })
    return out


def _norm_checkov(raw: object) -> list[dict]:
    if isinstance(raw, dict):
        checks = raw.get("results", {}).get("failed_checks", [])
    elif isinstance(raw, list):
        checks = []
        for block in raw:
            if isinstance(block, dict):
                checks.extend(block.get("results", {}).get("failed_checks", []))
    else:
        return []
    return [{
        "severity": "HIGH",
        "rule": c.get("check_id", ""),
        "file": c.get("repo_file_path", c.get("file_path", "")),
        "line": c.get("file_line_range", [""])[0],
        "message": (c.get("check", {}).get("name", "") if isinstance(c.get("check"), dict)
                    else str(c.get("check_id", ""))),
        "cwe": "",
        "fix": c.get("guideline", ""),
    } for c in checks]


def _norm_zap(raw: object) -> list[dict]:
    out = []
    if not isinstance(raw, dict):
        return out
    sev_map = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW", "INFORMATIONAL": "INFO"}
    for site in raw.get("site", []):
        for alert in site.get("alerts", []):
            risk = alert.get("riskdesc", "Info ").split(" ")[0].upper()
            out.append({
                "severity": sev_map.get(risk, "INFO"),
                "rule": alert.get("alertRef", alert.get("pluginid", "")),
                "file": alert.get("instances", [{}])[0].get("uri", site.get("@name", "")),
                "line": "",
                "message": alert.get("alert", alert.get("name", "")),
                "cwe": f"CWE-{alert['cweid']}" if alert.get("cweid") else "",
                "fix": alert.get("solution", ""),
            })
    return out


# ── Result file parser dispatcher ─────────────────────────────────────────────
# XML-output scanners
_XML_TYPES = {"nikto", "nmap", "openvas"}
# TSV log scanners
_TSV_TYPES = {"zeek"}
# NDJSON (one JSON object per line) scanners
_NDJSON_TYPES = {"trufflehog", "nuclei", "suricata"}


def _parse_result_file(scanner_id: str, result_file: "Path") -> object:
    """Read and parse a result file according to its scanner output format."""
    import xml.etree.ElementTree as ET  # stdlib
    stype = SCANNERS[scanner_id]["type"]
    text = result_file.read_text(encoding="utf-8", errors="replace")

    if stype in _XML_TYPES:
        return ET.parse(str(result_file)).getroot()

    if stype in _TSV_TYPES:
        lines = text.splitlines()
        headers: list[str] = []
        rows: list[dict] = []
        for line in lines:
            if line.startswith("#fields"):
                headers = line.replace("#fields", "").strip().split("\t")
            elif line.startswith("#"):
                continue
            elif headers and line.strip():
                parts = line.split("\t")
                rows.append(dict(zip(headers, parts)))
        return rows

    if stype in _NDJSON_TYPES:
        records: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    records.append(obj)
            except Exception:
                continue
        return records

    # Default: JSON (possibly with log-line prefix)
    return _parse_json_from_mixed_output(text)


# ── New normalizers ────────────────────────────────────────────────────────────

def _norm_nikto(raw: object) -> list[dict]:
    """Parse Nikto XML output (xml.etree.ElementTree root element)."""
    import xml.etree.ElementTree as ET
    out: list[dict] = []
    if not isinstance(raw, ET.Element):
        return out
    for item in raw.iter("item"):
        desc = (item.findtext("description") or item.get("message", "") or "").strip()
        uri = item.findtext("uri") or item.get("uri", "")
        ref = item.get("id", "")
        # Items with CVE/OSVDB references are HIGH; general findings are MEDIUM
        sev = "HIGH" if ("CVE" in desc.upper() or "OSVDB" in ref) else "MEDIUM"
        out.append({
            "severity": sev,
            "rule": ref or "nikto",
            "file": uri,
            "line": "",
            "message": desc[:300],
            "cwe": "",
            "fix": item.findtext("solution") or "",
        })
    return out


def _norm_schemathesis(raw: object) -> list[dict]:
    """Parse Schemathesis JSON report — failures become findings."""
    out: list[dict] = []
    if not isinstance(raw, (list, dict)):
        return out
    results = raw if isinstance(raw, list) else raw.get("results", [])  # type: ignore[union-attr]
    for r in results:
        if not isinstance(r, dict):
            continue
        status = r.get("status_code", 0)
        if isinstance(status, int) and status < 400:
            continue
        method = r.get("method", "").upper()
        path = r.get("path", "")
        sev = "HIGH" if isinstance(status, int) and status >= 500 else "MEDIUM"
        checks_failed = [c.get("name", "") for c in r.get("checks", []) if c.get("value") == "failure"]
        out.append({
            "severity": sev,
            "rule": f"{method} {path}",
            "file": path,
            "line": "",
            "message": f"HTTP {status} on {method} {path}" + (
                f" — failed checks: {', '.join(checks_failed)}" if checks_failed else ""
            ),
            "cwe": "CWE-20",
            "fix": "Validate and sanitize API inputs; handle unexpected input without 5xx errors",
        })
    return out


def _norm_trufflehog(raw: object) -> list[dict]:
    """Parse TruffleHog NDJSON output (list of dicts after NDJSON parse)."""
    out: list[dict] = []
    records = raw if isinstance(raw, list) else []
    for r in records:
        if not isinstance(r, dict):
            continue
        detector = r.get("DetectorName") or r.get("detectorName", "")
        meta = r.get("SourceMetadata", {}).get("Data", {})
        fs_meta = meta.get("Filesystem", meta.get("Git", {}))
        file_path = fs_meta.get("file", fs_meta.get("filename", ""))
        line = fs_meta.get("line", "")
        verified = r.get("Verified", False)
        out.append({
            "severity": "CRITICAL" if verified else "HIGH",
            "rule": detector or "trufflehog",
            "file": file_path,
            "line": line,
            "message": f"{'VERIFIED LIVE' if verified else 'Potential'} secret: {detector}",
            "cwe": "CWE-798",
            "fix": "Rotate the credential immediately, remove from code and Git history",
        })
    return out


def _norm_dependency_check(raw: object) -> list[dict]:
    """Parse OWASP Dependency-Check JSON report."""
    out: list[dict] = []
    if not isinstance(raw, dict):
        return out
    _sev_map = {
        "CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM",
        "LOW": "LOW", "MODERATE": "MEDIUM", "INFO": "INFO",
    }
    for dep in raw.get("dependencies", []):
        file_name = dep.get("fileName", dep.get("filePath", ""))
        for vuln in dep.get("vulnerabilities", []):
            sev_raw = (vuln.get("severity") or "medium").upper()
            # Prefer CVSS v3 severity over raw field
            cv3 = vuln.get("cvssv3", {})
            if cv3:
                sev_raw = (cv3.get("baseSeverity") or sev_raw).upper()
            cwe_ids = [c.get("cweId", "") for c in vuln.get("cwes", [])]
            out.append({
                "severity": _sev_map.get(sev_raw, "MEDIUM"),
                "rule": vuln.get("name", ""),
                "file": file_name,
                "line": "",
                "message": (vuln.get("description") or vuln.get("name", ""))[:300],
                "cwe": ", ".join(c for c in cwe_ids if c),
                "fix": vuln.get("recommendedCpe", "") or "Update to a patched version",
            })
    return out


def _norm_kics(raw: object) -> list[dict]:
    """Parse KICS JSON report."""
    out: list[dict] = []
    if not isinstance(raw, dict):
        return out
    _sev_map = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW", "info": "INFO"}
    for query in raw.get("queries", []):
        query_name = query.get("query_name", "")
        sev = _sev_map.get((query.get("severity") or "medium").lower(), "MEDIUM")
        cwe = query.get("cwe_ids", [])
        for f in query.get("files", []):
            out.append({
                "severity": sev,
                "rule": query.get("query_id", query_name),
                "file": f.get("file_name", ""),
                "line": f.get("line", ""),
                "message": f"{query_name}: {f.get('issue_type', '')}",
                "cwe": ", ".join(str(c) for c in cwe) if isinstance(cwe, list) else str(cwe),
                "fix": query.get("description", ""),
            })
    return out


def _norm_nuclei(raw: object) -> list[dict]:
    """Parse Nuclei NDJSON output (list of dicts after NDJSON parse)."""
    out: list[dict] = []
    _sev_map = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW", "info": "INFO"}
    records = raw if isinstance(raw, list) else []
    for r in records:
        if not isinstance(r, dict):
            continue
        info = r.get("info", {})
        sev = _sev_map.get((info.get("severity") or "info").lower(), "INFO")
        out.append({
            "severity": sev,
            "rule": r.get("template-id", r.get("templateID", "")),
            "file": r.get("matched-at", r.get("host", "")),
            "line": "",
            "message": info.get("name", r.get("template-id", "")),
            "cwe": "",
            "fix": (info.get("remediation") or info.get("description") or "")[:300],
        })
    return out


def _norm_nmap(raw: object) -> list[dict]:
    """Parse Nmap XML output (xml.etree.ElementTree root element)."""
    import xml.etree.ElementTree as ET
    out: list[dict] = []
    if not isinstance(raw, ET.Element):
        return out
    for host in raw.iter("host"):
        addr = host.find("address")
        ip = addr.get("addr", "unknown") if addr is not None else "unknown"
        hostname_el = host.find("hostnames/hostname")
        hostname = hostname_el.get("name", ip) if hostname_el is not None else ip
        for port in host.iter("port"):
            state = port.find("state")
            if state is None or state.get("state") != "open":
                continue
            portid = port.get("portid", "")
            proto = port.get("protocol", "tcp")
            svc = port.find("service")
            svc_name = svc.get("name", "") if svc is not None else ""
            svc_product = svc.get("product", "") if svc is not None else ""
            svc_version = svc.get("version", "") if svc is not None else ""
            # Check NSE script output for vulnerability indicators
            vuln_scripts = [
                s for s in port.findall("script")
                if "vuln" in (s.get("id") or "").lower() or "exploit" in (s.get("output") or "").lower()
            ]
            sev = "HIGH" if vuln_scripts else "INFO"
            desc_parts = [f"Open {proto}/{portid}"]
            if svc_name:
                desc_parts.append(f"{svc_name} {svc_product} {svc_version}".strip())
            for vs in vuln_scripts:
                desc_parts.append(f"[{vs.get('id')}] {(vs.get('output') or '')[:200]}")
            out.append({
                "severity": sev,
                "rule": f"open-port-{portid}",
                "file": hostname,
                "line": "",
                "message": " — ".join(desc_parts),
                "cwe": "CWE-200" if sev == "INFO" else "CWE-287",
                "fix": "Close unnecessary ports; apply patches for detected service versions",
            })
    return out


def _norm_openvas(raw: object) -> list[dict]:
    """Parse OpenVAS/Greenbone XML export (xml.etree.ElementTree root element)."""
    import xml.etree.ElementTree as ET
    out: list[dict] = []
    if not isinstance(raw, ET.Element):
        return out
    _threat_map = {"Critical": "CRITICAL", "High": "HIGH", "Medium": "MEDIUM", "Low": "LOW", "Log": "INFO"}
    # OpenVAS XML: <report><results><result><nvt><name><cvss_base><threat><description><host>
    for result in raw.iter("result"):
        nvt = result.find("nvt")
        name = (result.findtext("name") or (nvt.findtext("name") if nvt is not None else "") or "").strip()
        threat = result.findtext("threat") or "Log"
        desc = (result.findtext("description") or "")[:300]
        host = result.findtext("host") or ""
        oid = nvt.get("oid", "") if nvt is not None else ""
        cvss = (nvt.findtext("cvss_base") if nvt is not None else "") or ""
        cve_refs = [r.get("id", "") for r in (nvt.findall("refs/ref") if nvt is not None else [])
                    if r.get("type") == "cve"]
        out.append({
            "severity": _threat_map.get(threat, "INFO"),
            "rule": oid or "openvas",
            "file": host,
            "line": "",
            "message": f"{name} (CVSS {cvss})" if cvss else name,
            "cwe": "",
            "fix": f"CVEs: {', '.join(cve_refs)}" if cve_refs else desc[:200],
        })
    return out


def _norm_suricata(raw: object) -> list[dict]:
    """Parse Suricata EVE JSON log (list of dicts after NDJSON parse)."""
    out: list[dict] = []
    _sev_map = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}
    records = raw if isinstance(raw, list) else []
    for r in records:
        if not isinstance(r, dict) or r.get("event_type") != "alert":
            continue
        alert = r.get("alert", {})
        sig = alert.get("signature", "")
        category = alert.get("category", "")
        sev_int = alert.get("severity", 2)
        src = r.get("src_ip", "")
        dst = r.get("dest_ip", "")
        proto = r.get("proto", "")
        out.append({
            "severity": _sev_map.get(sev_int, "MEDIUM"),
            "rule": alert.get("signature_id", sig),
            "file": f"{src} → {dst}" if src else dst,
            "line": "",
            "message": f"[{category}] {sig}" if category else sig,
            "cwe": "",
            "fix": f"Investigate traffic: {src} → {dst} ({proto})",
        })
    return out


def _norm_zeek(raw: object) -> list[dict]:
    """Parse Zeek notice.log (list of TSV row dicts after log parse)."""
    out: list[dict] = []
    rows = raw if isinstance(raw, list) else []
    for r in rows:
        if not isinstance(r, dict):
            continue
        note = r.get("note", "")
        msg = r.get("msg", "")
        src = r.get("src", r.get("id.orig_h", ""))
        dst = r.get("dst", r.get("id.resp_h", ""))
        # Zeek notice severity: Policy notices = LOW, Weird = MEDIUM, Scan/Attack = HIGH
        note_lower = note.lower()
        if any(k in note_lower for k in ("scan", "bruteforce", "attack", "exploit")):
            sev = "HIGH"
        elif any(k in note_lower for k in ("weird", "protocol", "violation")):
            sev = "MEDIUM"
        else:
            sev = "LOW"
        out.append({
            "severity": sev,
            "rule": note or "zeek-notice",
            "file": f"{src} → {dst}" if src else dst,
            "line": "",
            "message": msg or note,
            "cwe": "",
            "fix": "Investigate the flagged network activity",
        })
    return out


def _norm_detect_secrets(raw: object) -> list[dict]:
    """Parse detect-secrets JSON output ({version, results:{file:[{type,line_number}]}})."""
    if not isinstance(raw, dict):
        return []
    out: list[dict] = []
    for filepath, secrets in raw.get("results", {}).items():
        for s in (secrets or []):
            stype = s.get("type", "Secret")
            line = s.get("line_number", "")
            out.append({
                "severity": "HIGH",
                "rule": stype.lower().replace(" ", "-"),
                "file": filepath,
                "line": line,
                "message": f"{stype} detected at line {line}",
                "cwe": "CWE-798",
                "fix": "Rotate the credential and remove from source code",
            })
    return out


def _norm_tfsec(raw: object) -> list[dict]:
    """Parse tfsec JSON output ({results:[{rule_id,description,severity,location}]})."""
    if not isinstance(raw, dict):
        return []
    out: list[dict] = []
    for r in raw.get("results", []):
        sev_map = {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM",
                   "LOW": "LOW", "WARNING": "MEDIUM", "INFO": "INFO"}
        loc = r.get("location", {})
        out.append({
            "severity": sev_map.get((r.get("severity") or "").upper(), "MEDIUM"),
            "rule": r.get("rule_id", r.get("long_id", "")),
            "file": loc.get("filename", ""),
            "line": loc.get("start_line", ""),
            "message": r.get("description", r.get("long_description", "")),
            "cwe": ", ".join(r.get("links", [])[:1]),  # use first link as ref
            "fix": r.get("resolution", ""),
        })
    return out


def _norm_stub_info(raw: object, stype: str) -> list[dict]:
    """For AWS/AI stub scanners: return the setup info message as a single INFO finding."""
    if isinstance(raw, dict) and raw.get("info"):
        return [{
            "severity": "INFO",
            "rule": f"{stype}-setup-required",
            "file": "",
            "line": "",
            "message": raw["info"],
            "cwe": "",
            "fix": raw["info"],
        }]
    return []


def _scan_summary(scanner_id: str, raw: object) -> dict:
    """Return a human-readable summary of what the scanner checked (targets, packages, rules, etc.)."""
    stype = SCANNERS[scanner_id]["type"]
    try:
        if stype == "semgrep" and isinstance(raw, dict):
            paths = raw.get("paths", {})
            scanned = paths.get("scanned", [])
            skipped = paths.get("skipped", [])
            return {"files_scanned": len(scanned), "files_skipped": len(skipped),
                    "label": f"{len(scanned)} files scanned"}
        if stype == "trivy" and isinstance(raw, dict):
            results = raw.get("Results", [])
            total = sum(len(r.get("Vulnerabilities") or []) for r in results)
            targets = [r.get("Target", "") for r in results]
            pkg_count = sum(len(r.get("Packages") or []) for r in results)
            return {"targets": targets, "total_vulns": total, "packages_scanned": pkg_count,
                    "label": f"{len(targets)} target(s), {total} vulnerabilities"}
        if stype == "gitleaks" and isinstance(raw, list):
            return {"secrets_found": len(raw), "label": f"{len(raw)} secret(s) detected"}
        if stype == "grype" and isinstance(raw, dict):
            matches = raw.get("matches", [])
            source = raw.get("source", {}).get("target", "")
            return {"matches": len(matches), "source": source, "label": f"{len(matches)} vulnerability matches"}
        if stype == "checkov":
            blocks = raw if isinstance(raw, list) else [raw]  # type: ignore[list-item]
            total_pass = sum(b.get("summary", {}).get("passed", 0) for b in blocks if isinstance(b, dict))
            total_fail = sum(b.get("summary", {}).get("failed", 0) for b in blocks if isinstance(b, dict))
            check_types = [b.get("check_type", "") for b in blocks if isinstance(b, dict)]
            return {"passed": total_pass, "failed": total_fail, "check_types": check_types,
                    "label": f"{total_pass + total_fail} IaC checks: {total_pass} passed, {total_fail} failed"}
        if stype == "cyclonedx" and isinstance(raw, dict):
            comps = raw.get("components", [])
            return {"components": len(comps), "spec_version": raw.get("specVersion", ""),
                    "label": f"{len(comps)} components in SBOM"}
        if stype == "zap" and isinstance(raw, dict):
            sites = raw.get("site", [])
            alerts = sum(len(s.get("alerts", [])) for s in sites)
            return {"sites": len(sites), "alerts": alerts, "label": f"{len(sites)} site(s) scanned, {alerts} alerts"}
        if stype == "nikto":
            import xml.etree.ElementTree as ET
            if isinstance(raw, ET.Element):
                items = list(raw.iter("item"))
                return {"items_tested": len(items), "label": f"{len(items)} test items checked"}
            return {"label": "Nikto scan complete"}
        if stype == "schemathesis":
            results = raw if isinstance(raw, list) else (raw.get("results", []) if isinstance(raw, dict) else [])  # type: ignore[union-attr]
            failures = [r for r in results if isinstance(r, dict) and r.get("status_code", 0) >= 400]
            return {"endpoints_tested": len(results), "failures": len(failures),
                    "label": f"{len(results)} API endpoints tested, {len(failures)} failures"}
        if stype == "trufflehog" and isinstance(raw, list):
            verified = sum(1 for r in raw if isinstance(r, dict) and r.get("Verified"))
            return {"secrets_found": len(raw), "verified": verified,
                    "label": f"{len(raw)} secrets found ({verified} verified live)"}
        if stype == "dependency_check" and isinstance(raw, dict):
            deps = raw.get("dependencies", [])
            vulns = sum(len(d.get("vulnerabilities", [])) for d in deps)
            return {"dependencies_scanned": len(deps), "vulnerabilities": vulns,
                    "label": f"{len(deps)} dependencies scanned, {vulns} vulnerabilities"}
        if stype == "kics" and isinstance(raw, dict):
            queries = raw.get("queries", [])
            total_files = sum(len(q.get("files", [])) for q in queries)
            return {"queries_matched": len(queries), "affected_files": total_files,
                    "label": f"{len(queries)} IaC rules matched, {total_files} affected locations"}
        if stype == "nuclei" and isinstance(raw, list):
            by_sev: dict[str, int] = {}
            for r in raw:
                if isinstance(r, dict):
                    s = r.get("info", {}).get("severity", "info").upper()
                    by_sev[s] = by_sev.get(s, 0) + 1
            return {"templates_matched": len(raw), "by_severity": by_sev,
                    "label": f"{len(raw)} vulnerability templates matched"}
        if stype == "nmap":
            import xml.etree.ElementTree as ET
            if isinstance(raw, ET.Element):
                hosts = list(raw.iter("host"))
                open_ports = [p for h in hosts for p in h.iter("port")
                              if p.find("state") is not None and p.find("state").get("state") == "open"]  # type: ignore[union-attr]
                return {"hosts_scanned": len(hosts), "open_ports": len(open_ports),
                        "label": f"{len(hosts)} host(s) scanned, {len(open_ports)} open ports"}
            return {"label": "Nmap scan complete"}
        if stype == "openvas":
            import xml.etree.ElementTree as ET
            if isinstance(raw, ET.Element):
                results = list(raw.iter("result"))
                return {"results_count": len(results), "label": f"{len(results)} OpenVAS results"}
            return {"label": "OpenVAS scan complete"}
        if stype == "suricata" and isinstance(raw, list):
            alerts = [r for r in raw if isinstance(r, dict) and r.get("event_type") == "alert"]
            return {"events_total": len(raw), "alerts": len(alerts),
                    "label": f"{len(raw)} EVE events, {len(alerts)} alerts"}
        if stype == "zeek" and isinstance(raw, list):
            return {"notice_count": len(raw), "label": f"{len(raw)} Zeek notices"}
    except Exception:
        pass
    return {"label": "Scan complete"}


def _count_severities(findings: list[dict]) -> dict:
    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        sev = f.get("severity", "INFO").upper()
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _derive_status(counts: dict) -> str:
    if counts.get("CRITICAL", 0) > 0:
        return "fail"
    if counts.get("HIGH", 0) > 0:
        return "warn"
    return "pass"


def _mtime(p: Path) -> str | None:
    try:
        return datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat()
    except Exception:
        return None


# ── Intelligence helpers ───────────────────────────────────────────────────────

def _load_deepseek_key() -> str:
    """Load DEEPSEEK_API_KEY from env var or runner .env file."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


def _calc_risk_score(counts: dict, history: list[dict]) -> dict:
    """Calculate a 0-100 risk score with letter grade and trend vs last scan."""
    score = min(100, (
        counts.get("CRITICAL", 0) * 20 +
        counts.get("HIGH", 0) * 10 +
        counts.get("MEDIUM", 0) * 3 +
        counts.get("LOW", 0) * 1
    ))
    if score == 0:
        grade = "A+"
    elif score <= 10:
        grade = "A"
    elif score <= 25:
        grade = "B"
    elif score <= 45:
        grade = "C"
    elif score <= 65:
        grade = "D"
    else:
        grade = "F"

    prev_score: int | None = None
    trend: str = "stable"
    change: int = 0
    if history:
        prev_counts = history[0].get("counts", {})
        prev_score = min(100, (
            prev_counts.get("CRITICAL", 0) * 20 +
            prev_counts.get("HIGH", 0) * 10 +
            prev_counts.get("MEDIUM", 0) * 3 +
            prev_counts.get("LOW", 0) * 1
        ))
        change = score - prev_score
        if change > 5:
            trend = "worse"
        elif change < -5:
            trend = "better"

    return {
        "score": score,
        "grade": grade,
        "trend": trend,
        "change": change,
        "prev_score": prev_score,
    }


# CWE → compliance framework mapping (lightweight heuristic)
_CWE_OWASP: dict[str, str] = {
    "CWE-89": "A03: Injection", "CWE-79": "A03: Injection",
    "CWE-78": "A03: Injection", "CWE-94": "A03: Injection",
    "CWE-798": "A07: Auth Failures", "CWE-287": "A07: Auth Failures",
    "CWE-284": "A01: Broken Access Control", "CWE-200": "A02: Crypto Failures",
    "CWE-327": "A02: Crypto Failures", "CWE-295": "A02: Crypto Failures",
    "CWE-502": "A08: Software Integrity", "CWE-20": "A03: Injection",
}

_CWE_HIPAA: set[str] = {"CWE-89", "CWE-284", "CWE-200", "CWE-327", "CWE-295", "CWE-798", "CWE-287", "CWE-312"}
_CWE_PCI: set[str]  = {"CWE-89", "CWE-79", "CWE-798", "CWE-327", "CWE-200", "CWE-287", "CWE-20"}


def _compliance_impact(findings: list[dict]) -> dict:
    """Map findings to compliance frameworks and count violations per framework."""
    owasp_counts: dict[str, int] = {}
    hipaa = 0
    pci_dss = 0
    soc2 = 0
    nist = 0
    iso27001 = 0

    for f in findings:
        sev = f.get("severity", "INFO").upper()
        cwe_raw = f.get("cwe", "")
        cwes = [c.strip() for c in str(cwe_raw).split(",") if c.strip()]

        for cwe in cwes:
            owasp_cat = _CWE_OWASP.get(cwe)
            if owasp_cat:
                owasp_counts[owasp_cat] = owasp_counts.get(owasp_cat, 0) + 1
            if cwe in _CWE_HIPAA:
                hipaa += 1
            if cwe in _CWE_PCI:
                pci_dss += 1

        if sev in ("CRITICAL", "HIGH"):
            soc2 += 1
            nist += 1
            iso27001 += 1

    # Secrets / credential findings always map to HIPAA + PCI even without CWE tag
    for f in findings:
        rule = str(f.get("rule", "")).lower()
        msg = str(f.get("message", "")).lower()
        if any(k in rule or k in msg for k in ("secret", "credential", "key", "token", "password")):
            if f not in findings:
                continue
            hipaa = max(hipaa, hipaa)  # already counted via CWE path above; ensure non-zero
            if "CWE-798" not in str(f.get("cwe", "")):
                hipaa += 1
                pci_dss += 1

    return {
        "owasp": owasp_counts,
        "hipaa": hipaa,
        "pci_dss": pci_dss,
        "soc2": soc2,
        "nist_csf": nist,
        "iso27001": iso27001,
    }


_EFFORT_MAP = {
    "CRITICAL": {"label": "1–3 days", "minutes": 1440},
    "HIGH":     {"label": "2–8 hours", "minutes": 300},
    "MEDIUM":   {"label": "30–90 min", "minutes": 60},
    "LOW":      {"label": "5–30 min", "minutes": 15},
    "INFO":     {"label": "< 5 min", "minutes": 5},
}


def _annotate_findings_with_effort(findings: list[dict]) -> list[dict]:
    """Add fix_effort field to each finding dict."""
    out = []
    for f in findings:
        f = dict(f)
        sev = f.get("severity", "INFO").upper()
        f["fix_effort"] = _EFFORT_MAP.get(sev, _EFFORT_MAP["INFO"])
        out.append(f)
    return out


def _delta_vs_last_scan(scanner_id: str, current_findings: list[dict]) -> dict:
    """Compare current findings to the most recent history entry by rule+file fingerprint."""
    history = _load_history(scanner_id)
    if not history:
        return {"new": len(current_findings), "fixed": 0, "unchanged": 0,
                "new_critical": 0, "is_first_scan": True}

    prev_entry = history[0]
    prev_fp: set[str] = set(prev_entry.get("finding_fingerprints", []))
    curr_fp: dict[str, dict] = {}
    for f in current_findings:
        key = f"{f.get('rule', '')}|{f.get('file', '')}|{f.get('severity', '')}"
        curr_fp[key] = f

    new_keys = set(curr_fp.keys()) - prev_fp
    fixed_count = len(prev_fp - set(curr_fp.keys()))
    unchanged = len(set(curr_fp.keys()) & prev_fp)
    new_critical = sum(1 for k in new_keys if curr_fp[k].get("severity") == "CRITICAL")

    return {
        "new": len(new_keys),
        "fixed": fixed_count,
        "unchanged": unchanged,
        "new_critical": new_critical,
        "is_first_scan": False,
    }


def _save_history_with_fingerprints(scanner_id: str, entry: dict, findings: list[dict]) -> None:
    """Save history entry including finding fingerprints for delta calculation."""
    entry = dict(entry)
    entry["finding_fingerprints"] = [
        f"{f.get('rule', '')}|{f.get('file', '')}|{f.get('severity', '')}"
        for f in findings
    ]
    history = _load_history(scanner_id)
    history.insert(0, entry)
    (HISTORY_DIR / f"{scanner_id}.json").write_text(
        json.dumps(history[:MAX_HISTORY], indent=2), encoding="utf-8"
    )


async def _call_deepseek(prompt: str) -> str:
    """Call DeepSeek chat API with the given prompt. Returns response text."""
    import urllib.request as _req
    import ssl as _ssl

    key = _load_deepseek_key()
    if not key:
        return '{"error": "DEEPSEEK_API_KEY not configured"}'

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1200,
    }).encode("utf-8")

    request = _req.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )

    ctx = _ssl.create_default_context()
    loop = asyncio.get_event_loop()

    def _do_request() -> str:
        try:
            with _req.urlopen(request, context=ctx, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    return await loop.run_in_executor(None, _do_request)


def _build_intelligence_prompt(scanner_id: str, findings: list[dict], counts: dict) -> str:
    scanner_label = SCANNERS.get(scanner_id, {}).get("label", scanner_id)
    # Summarise findings — send only top 20 to stay within token budget
    top_findings = sorted(
        findings,
        key=lambda f: ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].index(
            f.get("severity", "INFO") if f.get("severity", "INFO") in
            ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] else "INFO"
        )
    )[:20]

    findings_text = json.dumps([
        {
            "severity": f.get("severity"),
            "rule": f.get("rule", "")[:60],
            "message": (f.get("message") or "")[:120],
            "file": (f.get("file") or "")[:80],
            "cwe": f.get("cwe", ""),
        }
        for f in top_findings
    ], indent=2)

    return f"""You are a senior application security engineer reviewing scan results for the Pursh telehealth application.

Scanner: {scanner_label}
Findings summary: CRITICAL={counts.get("CRITICAL",0)}, HIGH={counts.get("HIGH",0)}, MEDIUM={counts.get("MEDIUM",0)}, LOW={counts.get("LOW",0)}

Top findings (JSON):
{findings_text}

Provide a JSON response with EXACTLY this structure (no markdown, no extra keys):
{{
  "summary": "3-4 sentence executive summary of the most critical risks and overall posture",
  "attack_paths": [
    {{
      "title": "short attack path title",
      "steps": ["step 1", "step 2", "step 3"],
      "impact": "business/compliance impact",
      "severity": "CRITICAL|HIGH|MEDIUM"
    }}
  ],
  "remediation_plan": {{
    "week1": ["action 1", "action 2"],
    "week2": ["action 1", "action 2"],
    "week3": ["action 1", "action 2"]
  }},
  "exploitability": "High|Medium|Low",
  "top_priority": "one sentence: what to fix first and why"
}}

Limit to max 3 attack paths. Be specific to the actual findings above. No generic advice."""


# ── Intelligence endpoint ──────────────────────────────────────────────────────

# Simple in-process cache: {scanner_id: {mtime, result}}
_intel_cache: dict[str, dict] = {}


@app.get("/intelligence/{scanner_id}")
async def get_intelligence(scanner_id: str):
    """AI-powered security analysis: summary, attack paths, remediation plan.
    Result is cached until the result file is modified."""
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")

    result_file = SCAN_RESULTS_DIR / SCANNERS[scanner_id]["result_file"]
    if not result_file.exists():
        return {"scanner": scanner_id, "status": "no_data"}

    # Cache check
    current_mtime = _mtime(result_file)
    cached = _intel_cache.get(scanner_id)
    if cached and cached.get("mtime") == current_mtime:
        return {"scanner": scanner_id, "status": "ok", "cached": True, **cached["result"]}

    try:
        raw = _parse_result_file(scanner_id, result_file)
    except Exception:
        return {"scanner": scanner_id, "status": "parse_error"}

    raw_findings = _normalise(scanner_id, raw)
    findings = [_to_finding(scanner_id, f, current_mtime) for f in raw_findings]
    counts = _count_severities(raw_findings)

    if not findings:
        result = {
            "summary": "No findings detected. The scan passed cleanly with no security issues.",
            "attack_paths": [],
            "remediation_plan": {"week1": [], "week2": [], "week3": []},
            "exploitability": "Low",
            "top_priority": "Maintain current security posture and run scans regularly.",
        }
        _intel_cache[scanner_id] = {"mtime": current_mtime, "result": result}
        return {"scanner": scanner_id, "status": "ok", "cached": False, **result}

    # Also compute non-AI intelligence to bundle with response
    history = _load_history(scanner_id)
    risk = _calc_risk_score(counts, history)
    compliance = _compliance_impact(raw_findings)
    delta = _delta_vs_last_scan(scanner_id, raw_findings)

    prompt = _build_intelligence_prompt(scanner_id, raw_findings, counts)
    t0 = time.monotonic()
    ai_text = await _call_deepseek(prompt)
    latency_ms = int((time.monotonic() - t0) * 1000)

    ai_error: str | None = None
    try:
        ai_result = json.loads(ai_text)
    except Exception:
        import re as _re
        match = _re.search(r"```(?:json)?\s*(\{.*?\})\s*```", ai_text, _re.DOTALL)
        if match:
            try:
                ai_result = json.loads(match.group(1))
            except Exception:
                ai_result = {"summary": ai_text, "attack_paths": [], "remediation_plan": {}, "error": "parse_failed"}
                ai_error = "json_parse_failed"
        else:
            ai_result = {"summary": ai_text, "attack_paths": [], "remediation_plan": {}, "error": "parse_failed"}
            ai_error = "json_parse_failed"

    result = {
        "risk_score": risk,
        "compliance": compliance,
        "delta": delta,
        "summary": ai_result.get("summary", ""),
        "attack_paths": ai_result.get("attack_paths", []),
        "remediation_plan": ai_result.get("remediation_plan", {}),
        "exploitability": ai_result.get("exploitability", "Unknown"),
        "top_priority": ai_result.get("top_priority", ""),
    }
    _intel_cache[scanner_id] = {"mtime": current_mtime, "result": result}

    # Persist prompt + response to Supabase audit log (fire-and-forget; never blocks the response)
    _storage.save_ai_analysis(
        scanner_id=scanner_id,
        run_id=None,               # not tied to a specific run_id in this flow
        prompt=prompt,
        response_raw=ai_text,
        response_parsed=ai_result,
        latency_ms=latency_ms,
        cached=False,
        error=ai_error,
    )

    return {"scanner": scanner_id, "status": "ok", "cached": False, **result}


@app.get("/risk-score/{scanner_id}")
async def get_risk_score(scanner_id: str):
    """Fast risk score endpoint — no AI call, computed from current result file."""
    if scanner_id not in SCANNERS:
        raise HTTPException(status_code=404, detail="Unknown scanner")

    result_file = SCAN_RESULTS_DIR / SCANNERS[scanner_id]["result_file"]
    if not result_file.exists():
        return {"scanner": scanner_id, "status": "no_data"}

    try:
        raw = _parse_result_file(scanner_id, result_file)
    except Exception:
        return {"scanner": scanner_id, "status": "parse_error"}

    raw_findings = _normalise(scanner_id, raw)
    counts = _count_severities(raw_findings)
    history = _load_history(scanner_id)
    risk = _calc_risk_score(counts, history)
    compliance = _compliance_impact(raw_findings)
    delta = _delta_vs_last_scan(scanner_id, raw_findings)
    findings_with_effort = _annotate_findings_with_effort(raw_findings)

    return {
        "scanner": scanner_id,
        "status": "ok",
        "counts": counts,
        "risk_score": risk,
        "compliance": compliance,
        "delta": delta,
        "effort_total_minutes": sum(f.get("fix_effort", {}).get("minutes", 0) for f in findings_with_effort),
    }
