"""
Golden-file contract tests for the Checkov IaC SARIF normalizer path.

Checkov scans Terraform, CloudFormation, and Kubernetes manifests and emits
SARIF. Its dialect uses 'tags' in rule properties (not a 'cwe' key), carrying
values like "CWE-16" or "CWE-284" without the colon-description suffix.

The tests verify:
  - CKV_AWS_53 (public S3 bucket) → CWE-16 → A05:2021 Security Misconfiguration
  - CKV_AWS_111 (broad IAM policy) → CWE-284 → A01:2021 Broken Access Control
  - CKV_AWS_18 (missing S3 logging) → CWE-778 → A09:2021 Logging Failures
  - discipline=DEVSECOPS propagated for IaC findings
  - scanner detected as CHECKOV

Checkov SARIF dialect notes:
- CWE IDs are in properties.tags as plain strings ("CWE-16"), not "CWE-16: Desc"
  The normalizer's _extract_cwes() handles this via the "CWE" substring check.
- Rule IDs follow the CKV_<PROVIDER>_<NUMBER> pattern.
"""

import json
from pathlib import Path

import pytest

from app.ingest.sarif.normalizer import normalize_sarif
from app.ingest.sarif.schema import SarifDocument
from app.models.finding import Discipline, Severity, ScannerName

GOLDEN = Path(__file__).parent / "contracts" / "checkov_golden.sarif.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(GOLDEN.read_text())


def test_checkov_sarif_schema_validates(golden: dict) -> None:
    doc = SarifDocument.model_validate(golden)
    assert doc.version == "2.1.0"
    assert len(doc.runs) == 1
    assert len(doc.runs[0].results) == 3


def test_checkov_finding_count(golden: dict) -> None:
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    assert len(findings) == 3


def test_checkov_scanner_detected(golden: dict) -> None:
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    assert all(f.scanner == ScannerName.CHECKOV for f in findings)


def test_checkov_discipline_devsecops(golden: dict) -> None:
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    assert all(f.discipline == Discipline.DEVSECOPS for f in findings)


def test_s3_logging_severity_medium(golden: dict) -> None:
    """CKV_AWS_18 is SARIF 'warning' → MEDIUM."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    logging_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_18")
    assert logging_finding.severity == Severity.MEDIUM


def test_s3_public_acl_severity_high(golden: dict) -> None:
    """CKV_AWS_53 is SARIF 'error' → HIGH."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    acl_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_53")
    assert acl_finding.severity == Severity.HIGH


def test_iam_policy_severity_high(golden: dict) -> None:
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    iam_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_111")
    assert iam_finding.severity == Severity.HIGH


def test_cwe_16_extracted_from_tags(golden: dict) -> None:
    """Checkov puts CWEs in tags field without descriptions; normalizer must handle this."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    acl_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_53")
    assert "CWE-16" in acl_finding.cwe


def test_cwe_284_extracted_from_tags(golden: dict) -> None:
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    iam_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_111")
    assert "CWE-284" in iam_finding.cwe


def test_s3_misconfig_owasp_a05(golden: dict) -> None:
    """CWE-16 (configuration) → A05:2021 Security Misconfiguration."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    acl_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_53")
    assert acl_finding.owasp_top10_2021 == "A05:2021"


def test_iam_finding_owasp_a01(golden: dict) -> None:
    """CWE-284 (improper access control) → A01:2021 Broken Access Control."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    iam_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_111")
    assert iam_finding.owasp_top10_2021 == "A01:2021"


def test_s3_logging_owasp_a09(golden: dict) -> None:
    """CWE-778 (insufficient logging) → A09:2021 Logging and Monitoring Failures."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    logging_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_18")
    assert logging_finding.owasp_top10_2021 == "A09:2021"


def test_iam_finding_hipaa_access_control(golden: dict) -> None:
    """CWE-284 (access control) → HIPAA §164.312(a)(1)."""
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    iam_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_111")
    assert "164.312(a)(1)" in iam_finding.hipaa_security_rule


def test_checkov_locations_extracted(golden: dict) -> None:
    findings = normalize_sarif(golden, target="aisec-internal", discipline=Discipline.DEVSECOPS)
    s3_findings = [f for f in findings if "s3.tf" in (f.location.file_path or "")]
    assert len(s3_findings) == 2
    iam_finding = next(f for f in findings if f.scanner_rule_id == "CKV_AWS_111")
    assert iam_finding.location is not None
    assert iam_finding.location.file_path == "infra/terraform/pursh/iam.tf"
    assert iam_finding.location.start_line == 12
