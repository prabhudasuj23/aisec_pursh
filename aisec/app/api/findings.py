"""
GET /api/v1/findings        — paginated, filterable list of all findings
GET /api/v1/findings/{id}   — single finding with full compliance mapping

Why a separate findings router?
The ingest endpoint writes data; this router reads it. Keeping them separate
enforces the hexagonal-architecture rule: no business logic in routes, and
read paths are independently testable without side effects.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthenticatedUser
from app.auth.oidc import require_authenticated_user
from app.core.database import get_db
from app.models.finding import Discipline, Finding, FindingStatus, Severity

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


# ── Response models ───────────────────────────────────────────────────────────

class FindingLocationOut(BaseModel):
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    snippet: str | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    region: str | None = None


class FindingOut(BaseModel):
    id: uuid.UUID
    scanner: str
    scanner_rule_id: str
    discipline: str
    severity: str
    target: str
    cwe: list[str]
    owasp_top10_2021: str | None
    owasp_llm_top10: str | None
    asvs_v4_controls: list[str]
    hipaa_security_rule: list[str]
    gdpr_art32_subclauses: list[str]
    title: str
    description: str
    remediation: str | None
    status: str
    first_seen: str
    last_seen: str
    location: FindingLocationOut | None = None

    @classmethod
    def from_orm(cls, f: Finding) -> "FindingOut":
        loc = None
        if f.location:
            loc = FindingLocationOut(
                file_path=f.location.file_path,
                start_line=f.location.start_line,
                end_line=f.location.end_line,
                snippet=f.location.snippet,
                resource_id=f.location.resource_id,
                resource_type=f.location.resource_type,
                region=f.location.region,
            )
        return cls(
            id=f.id,
            scanner=f.scanner.value,
            scanner_rule_id=f.scanner_rule_id,
            discipline=f.discipline.value,
            severity=f.severity.value,
            target=f.target,
            cwe=f.cwe,
            owasp_top10_2021=f.owasp_top10_2021,
            owasp_llm_top10=f.owasp_llm_top10,
            asvs_v4_controls=f.asvs_v4_controls,
            hipaa_security_rule=f.hipaa_security_rule,
            gdpr_art32_subclauses=f.gdpr_art32_subclauses,
            title=f.title,
            description=f.description,
            remediation=f.remediation,
            status=f.status.value,
            first_seen=f.first_seen.isoformat(),
            last_seen=f.last_seen.isoformat(),
            location=loc,
        )


class FindingListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[FindingOut]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=FindingListOut)
async def list_findings(
    target: str | None = Query(None, description="Filter by repo/target name"),
    severity: Severity | None = Query(None, description="Filter by severity"),
    status: FindingStatus | None = Query(None, description="Filter by triage status"),
    scanner: str | None = Query(None, description="Filter by scanner name"),
    discipline: Discipline | None = Query(None, description="Filter by discipline"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db),
    _user: AuthenticatedUser = Depends(require_authenticated_user),
) -> FindingListOut:
    """
    List findings with optional filters. Requires authentication.
    Results are ordered newest-first (last_seen DESC).
    """
    stmt = select(Finding)
    count_stmt = select(func.count()).select_from(Finding)

    if target:
        stmt = stmt.where(Finding.target == target)
        count_stmt = count_stmt.where(Finding.target == target)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
        count_stmt = count_stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
        count_stmt = count_stmt.where(Finding.status == status)
    if scanner:
        stmt = stmt.where(Finding.scanner == scanner)
        count_stmt = count_stmt.where(Finding.scanner == scanner)
    if discipline:
        stmt = stmt.where(Finding.discipline == discipline)
        count_stmt = count_stmt.where(Finding.discipline == discipline)

    stmt = stmt.order_by(Finding.last_seen.desc()).limit(limit).offset(offset)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    result = await db.execute(stmt)
    findings = result.scalars().all()

    return FindingListOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[FindingOut.from_orm(f) for f in findings],
    )


@router.get("/{finding_id}", response_model=FindingOut)
async def get_finding(
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: AuthenticatedUser = Depends(require_authenticated_user),
) -> FindingOut:
    """
    Return a single finding by ID, including full compliance mapping
    (OWASP, ASVS, HIPAA, GDPR) and location details. Requires authentication.
    """
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return FindingOut.from_orm(finding)
