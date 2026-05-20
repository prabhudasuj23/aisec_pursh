"""
GET /api/v1/reports/posture — security posture summary (public, no auth required)

Why public?
The posture report shows only aggregate counts — no finding details, no code
snippets, no file paths. Safe to expose publicly as a demo surface. A hiring
manager, auditor, or CISO can see the overall security health of the platform
without needing to log in.

Authenticated detail is available via GET /api/v1/findings.
"""

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import Finding, FindingStatus, Severity

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# ── Response model ────────────────────────────────────────────────────────────

class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class CWECount(BaseModel):
    cwe: str
    count: int


class PostureReport(BaseModel):
    generated_at: str
    summary: SeveritySummary
    open_findings: int
    fixed_findings: int
    owasp_coverage: dict[str, int]
    scanner_coverage: list[str]
    top_cwes: list[CWECount]
    hipaa_sections_covered: list[str]
    gdpr_subclauses_covered: list[str]


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/posture", response_model=PostureReport)
async def posture_report(db: AsyncSession = Depends(get_db)) -> PostureReport:
    """
    Aggregated security posture report. No authentication required.

    Shows counts only — no finding details, file paths, or code snippets.
    Suitable as a public-facing demo surface (aisec.aivistix.com/posture).

    For full finding details: GET /api/v1/findings (auth required).
    """
    result = await db.execute(select(Finding))
    findings = result.scalars().all()

    if not findings:
        return PostureReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary=SeveritySummary(),
            open_findings=0,
            fixed_findings=0,
            owasp_coverage={},
            scanner_coverage=[],
            top_cwes=[],
            hipaa_sections_covered=[],
            gdpr_subclauses_covered=[],
        )

    # Severity counts
    sev_counter: Counter = Counter(f.severity.value for f in findings)
    summary = SeveritySummary(
        critical=sev_counter.get("critical", 0),
        high=sev_counter.get("high", 0),
        medium=sev_counter.get("medium", 0),
        low=sev_counter.get("low", 0),
        info=sev_counter.get("info", 0),
    )

    # Open vs fixed
    open_findings = sum(1 for f in findings if f.status == FindingStatus.OPEN)
    fixed_findings = sum(1 for f in findings if f.status == FindingStatus.FIXED)

    # OWASP Top 10 coverage (A01–A10 hit counts)
    owasp_counter: Counter = Counter()
    for f in findings:
        if f.owasp_top10_2021:
            owasp_counter[f.owasp_top10_2021] += 1
    owasp_coverage = dict(sorted(owasp_counter.items()))

    # Scanners that have reported findings
    scanner_coverage = sorted(set(f.scanner.value for f in findings))

    # Top CWEs by frequency
    cwe_counter: Counter = Counter()
    for f in findings:
        for cwe in f.cwe:
            cwe_counter[cwe] += 1
    top_cwes = [
        CWECount(cwe=cwe, count=count)
        for cwe, count in cwe_counter.most_common(5)
    ]

    # HIPAA sections covered across all findings
    hipaa_covered: set[str] = set()
    for f in findings:
        hipaa_covered.update(f.hipaa_security_rule)

    # GDPR sub-clauses covered
    gdpr_covered: set[str] = set()
    for f in findings:
        gdpr_covered.update(f.gdpr_art32_subclauses)

    return PostureReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        open_findings=open_findings,
        fixed_findings=fixed_findings,
        owasp_coverage=owasp_coverage,
        scanner_coverage=scanner_coverage,
        top_cwes=top_cwes,
        hipaa_sections_covered=sorted(hipaa_covered),
        gdpr_subclauses_covered=sorted(gdpr_covered),
    )
