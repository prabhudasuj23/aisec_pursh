"""
Golden-file contract tests for the Trivy filesystem SARIF normalizer path.

Trivy-fs produces two finding categories in a single SARIF run:
  1. CVE vulnerability findings (SCA — outdated components, CWE-1104 → A06:2021)
  2. Secret findings (hard-coded credentials, CWE-798 → A07:2021)

This tests the normalizer handles mixed-type SARIF correctly and that:
- CVE findings map to A06:2021 (Vulnerable and Outdated Components)
- Secret findings map to A07:2021 (Identification and Authentication Failures)
- severity levels from Trivy's 'level' field are mapped correctly
- scanner is detected as TRIVY_FS regardless of result type

Trivy SARIF dialect notes:
- CWE is in rule properties.cwe as ["CWE-NNN: Description"] (same pattern as Semgrep)
- security-severity (CVSS score) is a property, not used for our severity enum
  (we use SARIF 'level' which Trivy maps from CVSS: critical→error, high→error,
   medium→warning, low→note)
"""

import json
from pathlib import Path

import pytest

from app.ingest.sarif.normalizer import normalize_sarif
from app.ingest.sarif.schema import SarifDocument
from app.models.finding import Discipline, Severity, ScannerName

GOLDEN = Path(__file__).parent / "contracts" / "trivy_fs_golden.sarif.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(GOLDEN.read_text())


def test_trivy_fs_sarif_schema_validates(golden: dict) -> None:
    doc = SarifDocument.model_validate(golden)
    assert doc.version == "2.1.0"
    assert len(doc.runs) == 1
    assert len(doc.runs[0].results) == 3


def test_trivy_fs_finding_count(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    assert len(findings) == 3


def test_trivy_fs_scanner_detected(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    assert all(f.scanner == ScannerName.TRIVY_FS for f in findings)


def test_cve_severity_warning_maps_to_medium(golden: dict) -> None:
    """CVE-2023-32681 is SARIF 'warning' → MEDIUM severity."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    cve_finding = next(f for f in findings if f.scanner_rule_id == "CVE-2023-32681")
    assert cve_finding.severity == Severity.MEDIUM


def test_cve_severity_error_maps_to_high(golden: dict) -> None:
    """CVE-2024-35195 is SARIF 'error' → HIGH severity."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    cve_finding = next(f for f in findings if f.scanner_rule_id == "CVE-2024-35195")
    assert cve_finding.severity == Severity.HIGH


def test_cve_cwe_1104_extracted(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    cve_finding = next(f for f in findings if f.scanner_rule_id == "CVE-2023-32681")
    assert "CWE-1104" in cve_finding.cwe


def test_cve_owasp_a06_mapped(golden: dict) -> None:
    """CWE-1104 (outdated component) → A06:2021 Vulnerable and Outdated Components."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    cve_finding = next(f for f in findings if f.scanner_rule_id == "CVE-2023-32681")
    assert cve_finding.owasp_top10_2021 == "A06:2021"


def test_secret_finding_owasp_a07_mapped(golden: dict) -> None:
    """CWE-798 in Trivy secret finding → A07:2021."""
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    secret_finding = next(f for f in findings if "secret" in f.scanner_rule_id)
    assert secret_finding.owasp_top10_2021 == "A07:2021"


def test_secret_finding_severity_high(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    secret_finding = next(f for f in findings if "secret" in f.scanner_rule_id)
    assert secret_finding.severity == Severity.HIGH


def test_cve_location_points_to_requirements_txt(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    cve_finding = next(f for f in findings if f.scanner_rule_id == "CVE-2023-32681")
    assert cve_finding.location is not None
    assert cve_finding.location.file_path == "pursh/backend/requirements.txt"
    assert cve_finding.location.start_line == 3


def test_secret_location_points_to_terraform(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    secret_finding = next(f for f in findings if "secret" in f.scanner_rule_id)
    assert secret_finding.location is not None
    assert secret_finding.location.file_path == "infra/terraform/pursh/main.tf"
    assert secret_finding.location.start_line == 22


def test_mixed_types_all_have_raw_preserved(golden: dict) -> None:
    findings = normalize_sarif(golden, target="pursh", discipline=Discipline.APPSEC)
    for finding in findings:
        assert isinstance(finding.raw, dict)
        assert "ruleId" in finding.raw
