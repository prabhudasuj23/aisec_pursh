"""
SARIF 2.1.0 → unified Finding normalizer.

SARIF (Static Analysis Results Interchange Format) is the standard output format
for Semgrep, ZAP, Trivy, Gitleaks, Checkov, tfsec, Grype, Syft, detect-secrets,
Prowler, promptfoo, and Garak. Every scanner produces
slightly different SARIF dialects — this normalizer handles the common subset and
scanner-specific extensions.

Why normalize instead of storing raw SARIF?
- Dashboard queries run against one table, not scanner-specific schemas
- OWASP/HIPAA/GDPR mapping happens once, against the unified model
- Scanner swap = write one new normalizer, not touch the dashboard or mappings

SARIF spec: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from __future__ import annotations

import uuid
from typing import Any

from app.ingest.sarif.schema import SarifDocument
from app.models.finding import Discipline, Finding, FindingLocation, Severity, ScannerName
from app.mappings.owasp import cwe_to_owasp_top10, cwe_to_asvs, cwe_to_hipaa, cwe_to_gdpr
from app.core.logging import get_logger

logger = get_logger(__name__)

# Maps SARIF rule severity levels to our unified severity enum
_SARIF_SEVERITY_MAP: dict[str, Severity] = {
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "note": Severity.LOW,
    "none": Severity.INFO,
}

# Maps known scanner tool names to our ScannerName enum.
# _detect_scanner does substring matching on tool_name.lower(), so keys must be lowercase.
# Multiple keys per scanner handle real SARIF driver.name variants across versions.
_TOOL_NAME_MAP: dict[str, ScannerName] = {
    # ── AppSec (ACTIVE · AISec CI) ────────────────────────────────────────────
    "semgrep":              ScannerName.SEMGREP,
    "zap":                  ScannerName.ZAP,
    "trivy-image":          ScannerName.TRIVY_IMAGE,   # checked before "trivy" to avoid prefix match
    "trivy-fs":             ScannerName.TRIVY_FS,
    "trivy":                ScannerName.TRIVY_FS,
    "gitleaks":             ScannerName.GITLEAKS,
    "checkov":              ScannerName.CHECKOV,
    "tfsec":                ScannerName.TFSEC,
    # ── SCA / SBOM (Planned · Phase 4) ───────────────────────────────────────
    "grype":                ScannerName.GRYPE,
    "syft":                 ScannerName.SYFT,
    # ── Secrets (Planned · Phase 6) ──────────────────────────────────────────
    "detect-secrets":       ScannerName.DETECT_SECRETS,
    "detect_secrets":       ScannerName.DETECT_SECRETS,
    # ── CloudSec CSPM (Planned · Phase 8) ────────────────────────────────────
    "prowler":              ScannerName.PROWLER,
    "scoutsuite":           ScannerName.SCOUTSUITE,
    "scout suite":          ScannerName.SCOUTSUITE,
    # ── AWS native (Planned · Phase 9) — forward-compat for ASFF→SARIF path ──
    "amazon guardduty":     ScannerName.GUARDDUTY,
    "guardduty":            ScannerName.GUARDDUTY,
    "amazon inspector":     ScannerName.INSPECTOR,
    "inspector":            ScannerName.INSPECTOR,
    "amazon macie":         ScannerName.MACIE,
    "macie":                ScannerName.MACIE,
    "iam access analyzer":  ScannerName.IAM_ACCESS_ANALYZER,
    "iam-access-analyzer":  ScannerName.IAM_ACCESS_ANALYZER,
    # ── AI Security (Planned · Phase 10) ─────────────────────────────────────
    "promptfoo":            ScannerName.PROMPTFOO,
    "garak":                ScannerName.GARAK,
}


def _detect_scanner(tool_name: str) -> ScannerName:
    name_lower = tool_name.lower()
    for key, scanner in _TOOL_NAME_MAP.items():
        if key in name_lower:
            return scanner
    logger.warning("unknown_scanner_tool", tool_name=tool_name)
    return ScannerName.SEMGREP  # safe default — never silently drops findings


def _extract_cwes(rule: dict[str, Any]) -> list[str]:
    """Extract CWE IDs from SARIF rule properties. Handles multiple formats."""
    cwes: list[str] = []
    props = rule.get("properties", {})

    # Semgrep: properties.cwe = ["CWE-89: SQL Injection"]
    # Checkov: properties.tags = ["CWE-798"]
    for field in ("cwe", "cwe-id", "CWE", "tags"):
        raw = props.get(field, [])
        if isinstance(raw, str):
            raw = [raw]
        for item in raw:
            if "CWE" in str(item).upper():
                # Normalize to "CWE-NNN" format
                parts = str(item).split(":")
                cwe_id = parts[0].strip().upper()
                if not cwe_id.startswith("CWE-"):
                    cwe_id = f"CWE-{cwe_id}"
                cwes.append(cwe_id)

    return list(dict.fromkeys(cwes))  # deduplicate, preserve order


def _extract_severity(
    rule: dict[str, Any], result: dict[str, Any]
) -> Severity:
    """Determine severity from SARIF result or rule default configuration."""
    # Result-level override takes priority
    level = result.get("level") or rule.get("defaultConfiguration", {}).get("level", "warning")
    return _SARIF_SEVERITY_MAP.get(str(level).lower(), Severity.MEDIUM)


def normalize_sarif(
    sarif_json: dict[str, Any],
    target: str,
    discipline: Discipline = Discipline.APPSEC,
) -> list[Finding]:
    """
    Parse a SARIF document and return a list of Finding objects (not yet persisted).

    Args:
        sarif_json: Parsed SARIF 2.1.0 JSON dict
        target: Repository/target identifier, e.g. "pursh" or "aisec-internal"
        discipline: Security discipline (appsec, cloudsec, aisec, devsecops)

    Returns:
        List of Finding objects ready for database insertion.
        Never raises — invalid/unknown fields are logged and skipped gracefully.

    Schema validation happens upstream (in the API endpoint) before this function
    is called, so we can assume basic SARIF structure is present.
    """
    findings: list[Finding] = []

    runs = sarif_json.get("runs", [])
    for run in runs:
        tool_name: str = (
            run.get("tool", {}).get("driver", {}).get("name", "unknown")
        )
        scanner = _detect_scanner(tool_name)

        # Build a rule lookup dict: rule_id → rule dict
        rules: dict[str, dict[str, Any]] = {
            r["id"]: r
            for r in run.get("tool", {}).get("driver", {}).get("rules", [])
            if "id" in r
        }

        results = run.get("results", [])
        logger.info(
            "sarif_run_processing",
            tool=tool_name,
            scanner=scanner,
            result_count=len(results),
            target=target,
        )

        for result in results:
            try:
                rule_id: str = result.get("ruleId", "unknown")
                rule = rules.get(rule_id, {})

                cwes = _extract_cwes(rule)
                severity = _extract_severity(rule, result)

                # Extract location (first physical location if present)
                location: FindingLocation | None = None
                locations = result.get("locations", [])
                if locations:
                    phys = locations[0].get("physicalLocation", {})
                    artifact_uri = (
                        phys.get("artifactLocation", {}).get("uri", "")
                    )
                    region = phys.get("region", {})
                    location = FindingLocation(
                        file_path=artifact_uri or None,
                        start_line=region.get("startLine"),
                        end_line=region.get("endLine"),
                        snippet=region.get("snippet", {}).get("text"),
                    )

                # Message text
                message = (
                    result.get("message", {}).get("text", "")
                    or rule.get("shortDescription", {}).get("text", "")
                    or rule.get("fullDescription", {}).get("text", "")
                    or rule_id
                )

                title = (
                    rule.get("shortDescription", {}).get("text")
                    or rule.get("name")
                    or rule_id
                )

                remediation = rule.get("help", {}).get("text") or rule.get("help", {}).get("markdown")

                finding = Finding(
                    id=uuid.uuid4(),
                    scanner=scanner,
                    scanner_rule_id=rule_id,
                    discipline=discipline,
                    severity=severity,
                    target=target,
                    cwe=cwes,
                    owasp_top10_2021=cwe_to_owasp_top10(cwes),
                    asvs_v4_controls=cwe_to_asvs(cwes),
                    cis_aws_controls=[],
                    nist_csf_subcategories=[],
                    hipaa_security_rule=cwe_to_hipaa(cwes),
                    gdpr_art32_subclauses=cwe_to_gdpr(cwes),
                    title=title[:512],
                    description=message[:4096],
                    remediation=remediation,
                    raw=result,
                )
                if location:
                    location.finding_id = finding.id
                    finding.location = location

                findings.append(finding)

            except Exception as exc:
                logger.warning(
                    "sarif_result_normalization_failed",
                    rule_id=result.get("ruleId"),
                    error=str(exc),
                )
                continue

    return findings
