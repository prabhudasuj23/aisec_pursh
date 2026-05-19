"""
Unified Finding model — the canonical representation of every security finding
regardless of which scanner produced it.

All scanners (Semgrep, ZAP, Trivy, Gitleaks, Checkov, Prowler, promptfoo) are
normalized into this model at ingestion time. The normalizer lives in
aisec/app/ingest/<scanner>/normalizer.py and writes Finding rows via the
FindingRepository.

Why a unified model?
- One data structure for all five dashboard personas
- OWASP/HIPAA/GDPR compliance mapping happens once, against this model
- Scanner swap (replace Semgrep with SonarQube) = write one new normalizer,
  not rewrite the dashboard
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ScannerName(str, Enum):
    SEMGREP = "semgrep"
    ZAP = "zap"
    TRIVY_FS = "trivy_fs"
    TRIVY_IMAGE = "trivy_image"
    GRYPE = "grype"
    SYFT = "syft"
    GITLEAKS = "gitleaks"
    DETECT_SECRETS = "detect_secrets"
    CHECKOV = "checkov"
    TFSEC = "tfsec"
    PROWLER = "prowler"
    SCOUTSUITE = "scoutsuite"
    GUARDDUTY = "guardduty"
    INSPECTOR = "inspector"
    MACIE = "macie"
    IAM_ACCESS_ANALYZER = "iam_access_analyzer"
    PROMPTFOO = "promptfoo"
    GARAK = "garak"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    ACCEPTED_RISK = "accepted_risk"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"


class Discipline(str, Enum):
    APPSEC = "appsec"
    CLOUDSEC = "cloudsec"
    AISEC = "aisec"
    DEVSECOPS = "devsecops"


class FindingLocation(Base):
    __tablename__ = "finding_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str | None] = mapped_column(String(1024))
    start_line: Mapped[int | None]
    end_line: Mapped[int | None]
    snippet: Mapped[str | None] = mapped_column(Text)
    # For cloud findings: AWS resource ARN or ID
    resource_id: Mapped[str | None] = mapped_column(String(512))
    resource_type: Mapped[str | None] = mapped_column(String(256))
    region: Mapped[str | None] = mapped_column(String(64))


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Scanner identity ──────────────────────────────────────────────────────
    scanner: Mapped[ScannerName] = mapped_column(SAEnum(ScannerName), nullable=False, index=True)
    scanner_rule_id: Mapped[str] = mapped_column(String(256), nullable=False)

    # ── Classification ────────────────────────────────────────────────────────
    discipline: Mapped[Discipline] = mapped_column(SAEnum(Discipline), nullable=False, index=True)
    severity: Mapped[Severity] = mapped_column(SAEnum(Severity), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # ── Compliance mappings (stored as JSON arrays) ───────────────────────────
    # e.g. ["CWE-89", "CWE-564"]
    cwe: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # e.g. "A03:2021"
    owasp_top10_2021: Mapped[str | None] = mapped_column(String(32))
    # e.g. "LLM01"
    owasp_llm_top10: Mapped[str | None] = mapped_column(String(16))
    # e.g. ["V2.1.1", "V3.4.2"]
    asvs_v4_controls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # e.g. ["2.1", "2.2.1"]
    cis_aws_controls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # e.g. ["ID.AM-2", "PR.AC-1"]
    nist_csf_subcategories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # e.g. ["164.312(a)(1)", "164.312(b)"]
    hipaa_security_rule: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # e.g. ["Art32(1)(a)"]
    gdpr_art32_subclauses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # ── Human-readable content ────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str | None] = mapped_column(Text)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    status: Mapped[FindingStatus] = mapped_column(
        SAEnum(FindingStatus), nullable=False, default=FindingStatus.OPEN, index=True
    )

    # ── Raw scanner output (preserved for audit / re-normalization) ───────────
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # ── Relations ─────────────────────────────────────────────────────────────
    location: Mapped[FindingLocation | None] = relationship(
        "FindingLocation",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys=[FindingLocation.finding_id],
    )
