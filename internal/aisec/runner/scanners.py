"""Scanner definitions — maps scanner ID to command, output file, and display metadata."""
import os
from pathlib import Path

# Root of the monorepo (four levels up from internal/aisec/runner/)
REPO_ROOT = Path(__file__).parent.parent.parent.parent

SCAN_RESULTS_DIR = REPO_ROOT / "internal" / "scan-results"
SCAN_RESULTS_DIR.mkdir(exist_ok=True)

# Windows vs Linux binary suffix
EXE = ".exe" if os.name == "nt" else ""

SCANNERS: dict[str, dict] = {
    "semgrep": {
        "label": "Semgrep (SAST)",
        "result_file": "semgrep-pursh.json",
        "command": [
            "semgrep", "scan",
            "--config", str(REPO_ROOT / "internal" / "scanners" / "semgrep" / "custom-rules.yaml"),
            "--config", "p/owasp-top-ten",
            str(REPO_ROOT / "pursh"),
            "--json",
        ],
        "type": "semgrep",
    },
    "trivy-sca": {
        "label": "Trivy SCA",
        "result_file": "trivy-pursh-sca.json",
        "command": [
            "trivy", "fs",
            str(REPO_ROOT / "pursh"),
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM",
            "--quiet",
        ],
        "type": "trivy",
    },
    "trivy-image": {
        "label": "Trivy Image",
        "result_file": "trivy-env.json",
        "command": [
            "trivy", "fs",
            str(REPO_ROOT / "pursh"),
            "--format", "json",
            "--severity", "CRITICAL,HIGH",
            "--quiet",
        ],
        "type": "trivy",
    },
    "gitleaks": {
        "label": "Gitleaks (Secrets)",
        "result_file": "gitleaks-clean.json",
        "command": [
            str(REPO_ROOT / "internal" / "scanners" / "gitleaks-bin" / f"gitleaks{EXE}"),
            "detect",
            "--source", str(REPO_ROOT / "pursh"),   # ONLY scan pursh/, not entire repo
            "--config", str(REPO_ROOT / "internal" / "scanners" / "gitleaks" / ".gitleaks.toml"),
            "--report-format", "json",
            "--report-path", str(SCAN_RESULTS_DIR / "gitleaks-clean.json"),
            "--no-git",
        ],
        "type": "gitleaks",
    },
    "grype": {
        "label": "Grype (Vulns)",
        "result_file": "grype-pursh.json",
        "command": [
            str(REPO_ROOT / "internal" / "scanners" / "grype-bin" / f"grype{EXE}"),
            f"dir:{REPO_ROOT / 'pursh'}",
            "--name", "pursh",
            "-o", "json",
        ],
        "type": "grype",
    },
    "checkov": {
        "label": "Checkov (IaC)",
        "result_file": "checkov.json",
        "command": [
            "python", "-m", "checkov.main",
            "-d", str(REPO_ROOT / "internal" / "infra" / "terraform"),
            "--output", "json",
            "--skip-check", "CKV_TF_1",
            "--compact",
            "--quiet",
        ],
        "type": "checkov",
        # checkov writes findings JSON to stdout; runner captures it
        "write_stdout": True,
    },
    "syft": {
        "label": "Syft (SBOM)",
        "result_file": "pursh.cyclonedx.json",
        "command": [
            "syft",
            str(REPO_ROOT / "pursh"),
            "--source-name", "pursh",
            "--source-version", "0.0.0-dev",
            "-o", "cyclonedx-json",
        ],
        "type": "cyclonedx",
    },
    "zap": {
        "label": "ZAP (DAST)",
        "result_file": "zap-report.json",
        "command": [
            "python", "-c",
            (
                "import json, sys; "
                "msg = {'info': 'ZAP requires a running target. "
                "Start the Pursh app on port 3000, then run: "
                "docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py "
                "-t http://host.docker.internal:3000 -J zap-report.json'}; "
                "print(json.dumps(msg))"
            ),
        ],
        "type": "zap",
    },

    # ── DAST additions ────────────────────────────────────────────────────────
    "nikto": {
        "label": "Nikto (Web Scanner)",
        "result_file": "nikto-pursh.xml",
        "command": [
            "docker", "run", "--rm", "--network=host",
            "frapsoft/nikto",
            "-h", "http://localhost:3000",
            "-o", "/tmp/nikto-pursh.xml",
            "-Format", "xml",
        ],
        "type": "nikto",
    },
    "schemathesis": {
        "label": "Schemathesis (API Fuzzer)",
        "result_file": "schemathesis-pursh.json",
        "command": [
            "schemathesis", "run",
            "http://localhost:8001/openapi.json",
            "--checks", "all",
            "--hypothesis-max-examples", "50",
            "--report", str(SCAN_RESULTS_DIR / "schemathesis-pursh.json"),
        ],
        "type": "schemathesis",
    },

    # ── Secrets addition ──────────────────────────────────────────────────────
    "trufflehog": {
        "label": "TruffleHog (Secrets)",
        "result_file": "trufflehog-pursh.json",
        "command": [
            "docker", "run", "--rm",
            "-v", f"{REPO_ROOT}:/repo:ro",
            "trufflesecurity/trufflehog:latest",
            "filesystem", "/repo/pursh",
            "--json",
            "--no-update",
        ],
        "type": "trufflehog",
        "write_stdout": True,
    },

    # ── SCA addition ──────────────────────────────────────────────────────────
    "dependency-check": {
        "label": "OWASP Dependency-Check",
        "result_file": "dependency-check-report.json",
        "command": [
            "docker", "run", "--rm",
            "-v", f"{REPO_ROOT / 'pursh'}:/src:ro",
            "-v", f"{SCAN_RESULTS_DIR}:/report",
            "owasp/dependency-check",
            "--scan", "/src",
            "--project", "pursh",
            "--format", "JSON",
            "--out", "/report",
            "--nvdApiDelay", "6000",
        ],
        "type": "dependency_check",
    },

    # ── IaC addition ──────────────────────────────────────────────────────────
    "kics": {
        "label": "KICS (IaC Security)",
        "result_file": "kics-pursh.json",
        "command": [
            "docker", "run", "--rm",
            "-v", f"{REPO_ROOT}:/path:ro",
            "-v", f"{SCAN_RESULTS_DIR}:/output",
            "checkmarx/kics:latest",
            "scan",
            "-p", "/path/internal/infra/terraform",
            "-o", "/output",
            "--report-formats", "json",
            "--output-name", "kics-pursh",
            "--no-progress",
        ],
        "type": "kics",
    },

    # ── Vulnerability Management ───────────────────────────────────────────────
    "nuclei": {
        "label": "Nuclei (Vuln Scanner)",
        "result_file": "nuclei-pursh.json",
        "command": [
            "docker", "run", "--rm", "--network=host",
            "-v", f"{SCAN_RESULTS_DIR}:/output",
            "projectdiscovery/nuclei:latest",
            "-u", "http://localhost:3000",
            "-t", "cves/",
            "-t", "misconfiguration/",
            "-json-export", "/output/nuclei-pursh.json",
            "-silent",
        ],
        "type": "nuclei",
    },
    "nmap": {
        "label": "Nmap (Port Scanner)",
        "result_file": "nmap-pursh.xml",
        "command": [
            "nmap",
            "-sV", "--open",
            "-oX", str(SCAN_RESULTS_DIR / "nmap-pursh.xml"),
            "localhost",
        ],
        "type": "nmap",
    },
    "openvas": {
        "label": "OpenVAS (Greenbone)",
        "result_file": "openvas-report.xml",
        "command": [
            "python", "-c",
            (
                "import json; "
                "print(json.dumps({'info': 'OpenVAS requires Greenbone Community Edition. "
                "Setup: docker run -d --name greenbone-community-edition "
                "-p 9390:9390 greenbone/community-edition "
                "Then export your task results XML to "
                "internal/scan-results/openvas-report.xml'}))"
            ),
        ],
        "type": "openvas",
    },

    # ── Network / IDS ─────────────────────────────────────────────────────────
    "suricata": {
        "label": "Suricata (IDS/IPS)",
        "result_file": "suricata-eve.json",
        "command": [
            "python", "-c",
            (
                "import json; "
                "print(json.dumps({'info': 'Suricata requires a running sensor capturing live traffic. "
                "Install: sudo apt install suricata && sudo suricata-update "
                "Then copy /var/log/suricata/eve.json to "
                "internal/scan-results/suricata-eve.json'}))"
            ),
        ],
        "type": "suricata",
    },
    "zeek": {
        "label": "Zeek (NSM)",
        "result_file": "zeek-notice.log",
        "command": [
            "python", "-c",
            (
                "import json; "
                "print(json.dumps({'info': 'Zeek requires a running network sensor. "
                "Install: sudo apt install zeek && zeek -i eth0 "
                "Then copy /opt/zeek/logs/current/notice.log to "
                "internal/scan-results/zeek-notice.log'}))"
            ),
        ],
        "type": "zeek",
    },

    # ── Secrets / SCM ─────────────────────────────────────────────────────────
    "detect-secrets": {
        "label": "detect-secrets",
        "result_file": "detect-secrets.json",
        "command": [
            "detect-secrets", "scan",
            str(REPO_ROOT / "pursh"),
            "--all-files",
        ],
        "type": "detect_secrets",
        "write_stdout": True,
    },

    # ── IaC / Pipeline Security ───────────────────────────────────────────────
    "tfsec": {
        "label": "tfsec (IaC)",
        "result_file": "tfsec-pursh.json",
        "command": [
            "tfsec",
            str(REPO_ROOT / "internal" / "infra" / "terraform"),
            "--format", "json",
            "--soft-fail",
            "--out", str(SCAN_RESULTS_DIR / "tfsec-pursh.json"),
        ],
        "type": "tfsec",
    },

    # ── CloudSec — stubs (require AWS credentials or running service) ─────────
    "prowler": {
        "label": "Prowler (CSPM)",
        "result_file": "prowler-output.json",
        "command": [
            "python", "-c",
            (
                "import json; "
                "print(json.dumps({'info': 'Prowler requires AWS credentials. "
                "Run: docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY "
                "-e AWS_DEFAULT_REGION prowler/prowler -M json "
                "-o /tmp/prowler-output.json then copy result here.'}))"
            ),
        ],
        "type": "prowler",
    },
    "scoutsuite": {
        "label": "ScoutSuite (CSPM)",
        "result_file": "scoutsuite-results.json",
        "command": [
            "python", "-c",
            (
                "import json; "
                "print(json.dumps({'info': 'ScoutSuite requires AWS credentials. "
                "Run: scout aws --report-dir /tmp/scoutsuite then copy last_run.json here.'}))"
            ),
        ],
        "type": "scoutsuite",
    },
    "guardduty": {
        "label": "GuardDuty",
        "result_file": "guardduty-findings.json",
        "command": [
            "python", "-c",
            "import json; print(json.dumps({'info': 'GuardDuty requires AWS credentials. Use: aws guardduty list-findings --detector-id <id> then aws guardduty get-findings and save JSON to guardduty-findings.json'}))",
        ],
        "type": "guardduty",
    },
    "inspector": {
        "label": "AWS Inspector v2",
        "result_file": "inspector-findings.json",
        "command": [
            "python", "-c",
            "import json; print(json.dumps({'info': 'Inspector v2 requires AWS credentials. Use: aws inspectorv2 list-findings --output json > inspector-findings.json'}))",
        ],
        "type": "inspector",
    },
    "macie": {
        "label": "AWS Macie",
        "result_file": "macie-findings.json",
        "command": [
            "python", "-c",
            "import json; print(json.dumps({'info': 'Macie requires AWS credentials and Macie enabled. Use: aws macie2 list-findings then aws macie2 get-findings --finding-ids ... and save to macie-findings.json'}))",
        ],
        "type": "macie",
    },
    "iam-access-analyzer": {
        "label": "IAM Access Analyzer",
        "result_file": "iam-analyzer-findings.json",
        "command": [
            "python", "-c",
            "import json; print(json.dumps({'info': 'IAM Access Analyzer requires AWS credentials. Use: aws accessanalyzer list-findings --analyzer-arn <arn> --output json > iam-analyzer-findings.json'}))",
        ],
        "type": "iam_access_analyzer",
    },

    # ── AI Security — stubs (require LLM API + running Pursh app) ─────────────
    "promptfoo": {
        "label": "promptfoo (LLM Red-Team)",
        "result_file": "promptfoo-results.json",
        "command": [
            "python", "-c",
            "import json; print(json.dumps({'info': 'promptfoo requires Pursh AI endpoints running. Run: npx promptfoo eval -c internal/scanners/promptfoo/config.yaml -o internal/scan-results/promptfoo-results.json'}))",
        ],
        "type": "promptfoo",
    },
    "garak": {
        "label": "Garak (LLM Vulns)",
        "result_file": "garak-results.json",
        "command": [
            "python", "-c",
            "import json; print(json.dumps({'info': 'Garak requires garak installed in a Python venv. Run: python -m garak --model_type rest --model_name pursh-llm --report_prefix internal/scan-results/garak-results'}))",
        ],
        "type": "garak",
    },
}
