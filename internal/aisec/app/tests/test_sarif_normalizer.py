"""
Golden-file contract tests for the SARIF normalizer.

These tests assert the exact output of normalize_sarif() against a known-good
SARIF input. If a normalizer change causes a different mapping, the test fails —
forcing the developer to consciously update the golden file.

Why golden-file tests for normalizers?
The normalizer is the trust boundary between raw scanner output and the compliance
mapping layer. Silent mapping changes can cause findings to silently drop OWASP or
HIPAA tags — which would be invisible until an auditor noticed. Golden files make
those changes visible at CI time.
"""

import json
from pathlib import Path

import pytest

from app.ingest.sarif.normalizer import normalize_sarif
from app.ingest.sarif.schema import SarifDocument
from app.models.finding import Discipline, Severity, ScannerName

GOLDEN_SARIF = Path(__file__).parent / "contracts" / "semgrep_golden.sarif.json"


@pytest.fixture(scope="module")
def golden_sarif() -> dict:
    return json.loads(GOLDEN_SARIF.read_text())


def test_sarif_schema_validates(golden_sarif: dict) -> None:
    """Golden file must pass schema validation."""
    doc = SarifDocument.model_validate(golden_sarif)
    assert doc.version == "2.1.0"
    assert len(doc.runs) == 1
    assert len(doc.runs[0].results) == 2


def test_normalizer_produces_correct_count(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    assert len(findings) == 2


def test_sql_injection_finding_severity(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    sql_finding = next(f for f in findings if "sql" in f.scanner_rule_id.lower())
    assert sql_finding.severity == Severity.HIGH  # SARIF "error" → HIGH


def test_sql_injection_owasp_mapping(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    sql_finding = next(f for f in findings if "sql" in f.scanner_rule_id.lower())
    assert sql_finding.owasp_top10_2021 == "A03:2021"
    assert "CWE-89" in sql_finding.cwe


def test_sql_injection_hipaa_mapping(golden_sarif: dict) -> None:
    """SQL injection maps to HIPAA §164.312(b) audit controls."""
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    sql_finding = next(f for f in findings if "sql" in f.scanner_rule_id.lower())
    assert "164.312(b)" in sql_finding.hipaa_security_rule


def test_sql_injection_asvs_mapping(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    sql_finding = next(f for f in findings if "sql" in f.scanner_rule_id.lower())
    assert "V5.3.4" in sql_finding.asvs_v4_controls


def test_xss_finding_severity(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    xss_finding = next(f for f in findings if "jinja2" in f.scanner_rule_id.lower())
    assert xss_finding.severity == Severity.MEDIUM  # SARIF "warning" → MEDIUM


def test_xss_finding_owasp_mapping(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    xss_finding = next(f for f in findings if "jinja2" in f.scanner_rule_id.lower())
    assert xss_finding.owasp_top10_2021 == "A03:2021"
    assert "CWE-79" in xss_finding.cwe


def test_finding_location_extracted(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    sql_finding = next(f for f in findings if "sql" in f.scanner_rule_id.lower())
    assert sql_finding.location is not None
    assert sql_finding.location.file_path == "pursh/backend/api/patients.py"
    assert sql_finding.location.start_line == 42


def test_scanner_detected_as_semgrep(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    assert all(f.scanner == ScannerName.SEMGREP for f in findings)


def test_target_propagated(golden_sarif: dict) -> None:
    findings = normalize_sarif(golden_sarif, target="pursh-test", discipline=Discipline.APPSEC)
    assert all(f.target == "pursh-test" for f in findings)


def test_raw_preserved(golden_sarif: dict) -> None:
    """Raw scanner output must be preserved for audit / re-normalization."""
    findings = normalize_sarif(golden_sarif, target="pursh", discipline=Discipline.APPSEC)
    sql_finding = next(f for f in findings if "sql" in f.scanner_rule_id.lower())
    assert sql_finding.raw.get("ruleId") == "python.sqlalchemy.security.audit.raw-query.raw-query"
