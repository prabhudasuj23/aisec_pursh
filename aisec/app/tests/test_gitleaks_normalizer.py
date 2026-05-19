"""
Golden-file contract tests for the Gitleaks SARIF normalizer path.

Gitleaks emits SARIF with CWE-798 (hard-coded credentials). These tests
verify the normalizer maps secrets findings to:
  - OWASP A07:2021 (Identification and Authentication Failures)
  - ASVS V2.10.1 (hard-coded credentials control)
  - HIPAA §164.312(d) (person/entity authentication)

Why test the secrets path separately from Semgrep?
Gitleaks uses a different SARIF dialect: it includes a 'fingerprints' field
for deduplication and uses tags rather than 'cwe' in rule properties.
The normalizer's _extract_cwes() handles both, but a dedicated test suite
catches regressions if either format changes.
"""

import json
from pathlib import Path

import pytest

from app.ingest.sarif.normalizer import normalize_sarif
from app.ingest.sarif.schema import SarifDocument
from app.models.finding import Discipline, Severity, ScannerName

GOLDEN = Path(__file__).parent / "contracts" / "gitleaks_golden.sarif.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(GOLDEN.read_text())


def test_gitleaks_sarif_schema_validates(golden: dict) -> None:
    doc = SarifDocument.model_validate(golden)
    assert doc.version == "2.1.0"
    assert len(doc.runs) == 1
    assert len(doc.runs[0].results) == 2


def test_gitleaks_finding_count(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    assert len(findings) == 2


def test_gitleaks_scanner_detected(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    assert all(f.scanner == ScannerName.GITLEAKS for f in findings)


def test_aws_key_severity_is_high(golden: dict) -> None:
    """SARIF 'error' level → HIGH severity."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    aws_finding = next(f for f in findings if "aws-access-token" in f.scanner_rule_id)
    assert aws_finding.severity == Severity.HIGH


def test_generic_key_severity_is_medium(golden: dict) -> None:
    """SARIF 'warning' level → MEDIUM severity."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    api_finding = next(f for f in findings if "generic-api-key" in f.scanner_rule_id)
    assert api_finding.severity == Severity.MEDIUM


def test_cwe_798_extracted(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    aws_finding = next(f for f in findings if "aws-access-token" in f.scanner_rule_id)
    assert "CWE-798" in aws_finding.cwe


def test_owasp_a07_mapped(golden: dict) -> None:
    """CWE-798 hard-coded credentials → A07:2021 Identification and Authentication Failures."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    aws_finding = next(f for f in findings if "aws-access-token" in f.scanner_rule_id)
    assert aws_finding.owasp_top10_2021 == "A07:2021"


def test_asvs_v2_10_1_mapped(golden: dict) -> None:
    """CWE-798 → ASVS V2.10.1 (hard-coded credential control)."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    aws_finding = next(f for f in findings if "aws-access-token" in f.scanner_rule_id)
    assert "V2.10.1" in aws_finding.asvs_v4_controls


def test_discipline_devsecops_propagated(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    assert all(f.discipline == Discipline.DEVSECOPS for f in findings)


def test_aws_key_location_extracted(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    aws_finding = next(f for f in findings if "aws-access-token" in f.scanner_rule_id)
    assert aws_finding.location is not None
    assert aws_finding.location.file_path == "pursh/backend/core/config.py"
    assert aws_finding.location.start_line == 17


def test_raw_result_preserved(golden: dict) -> None:
    """Fingerprint data in raw must survive normalization for dedup logic."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.DEVSECOPS)
    aws_finding = next(f for f in findings if "aws-access-token" in f.scanner_rule_id)
    assert aws_finding.raw.get("fingerprints", {}).get("matchBasedId/v1") == "abc123def456"
