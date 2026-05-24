"""
POST /api/v1/ingest/sarif  — ingest a SARIF 2.1.0 document.

Flow:
  1. Schema validate (SarifDocument) — reject malformed input at the boundary
  2. Normalize → list[Finding]
  3. Persist to Postgres via FindingRepository
  4. Return summary (count, severities)

Why validate before normalizing?
CWE-20 (Improper Input Validation): an attacker who controls the CI pipeline
could submit crafted SARIF to poison the finding database. Schema validation
ensures only structurally valid documents proceed.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthenticatedUser
from app.auth.oidc import require_authenticated_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.ingest.sarif.normalizer import normalize_sarif
from app.ingest.sarif.schema import SarifDocument
from app.models.finding import Discipline, Finding

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


class IngestSarifRequest(BaseModel):
    sarif: dict[str, Any]
    target: str          # e.g. "pursh", "aisec-internal"
    discipline: str = "appsec"


class IngestSarifResponse(BaseModel):
    ingested: int
    skipped: int
    severities: dict[str, int]


@router.post("/sarif", response_model=IngestSarifResponse, status_code=status.HTTP_201_CREATED)
async def ingest_sarif(
    body: IngestSarifRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> IngestSarifResponse:
    """
    Ingest a SARIF 2.1.0 document. Requires authentication.

    The caller (GitHub Actions workflow) posts the raw SARIF JSON along with
    the target repository name and discipline. AISec validates, normalizes, and
    persists the findings.
    """
    # 1. Schema validate
    try:
        SarifDocument.model_validate(body.sarif)
    except ValidationError as exc:
        logger.warning(
            "sarif_schema_validation_failed",
            target=body.target,
            errors=exc.error_count(),
        )
        raise HTTPException(
            status_code=422,
            detail=f"Invalid SARIF document: {exc.error_count()} validation error(s).",
        ) from exc

    # 2. Normalize
    try:
        discipline = Discipline(body.discipline)
    except ValueError:
        discipline = Discipline.APPSEC

    findings = normalize_sarif(body.sarif, target=body.target, discipline=discipline)

    # 3. Persist
    skipped = 0
    severity_counts: dict[str, int] = {}
    for finding in findings:
        try:
            db.add(finding)
            sev = finding.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        except Exception as exc:
            logger.warning("finding_persist_failed", rule_id=finding.scanner_rule_id, error=str(exc))
            skipped += 1

    logger.info(
        "sarif_ingested",
        target=body.target,
        ingested=len(findings) - skipped,
        skipped=skipped,
        actor=user.sub,
    )

    return IngestSarifResponse(
        ingested=len(findings) - skipped,
        skipped=skipped,
        severities=severity_counts,
    )
