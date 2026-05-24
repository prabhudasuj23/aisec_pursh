Here are the exact commands to run each scanner one by one and see results. Open a PowerShell window in your project root first:


cd C:\Users\prabh\Downloads\ci_cd_seclab
1 — SAST (Semgrep)

semgrep --config p/python --config p/security-audit --config p/owasp-top-ten pursh/
What you'll see: List of files scanned, then any findings with file path, line number, rule name, and severity. A "0 findings" message means clean.

To save to a file and read it:


semgrep --config p/owasp-top-ten --json --output scan-results\semgrep.json pursh/
Get-Content scan-results\semgrep.json | python -m json.tool | Select-String "ruleId|severity|path" | Select-Object -First 40
2 — SCA (Trivy filesystem)

trivy fs --severity CRITICAL,HIGH,MEDIUM pursh/
What you'll see: A table per requirements file showing package name, installed version, fixed version, CVE ID, and severity. Empty table = no findings.

To save and read:


trivy fs --severity CRITICAL,HIGH,MEDIUM --format table pursh/ 2>&1 | Tee-Object scan-results\trivy-sca.txt
Get-Content scan-results\trivy-sca.txt
3 — SBOM (Syft)

syft pursh/ --output table
What you'll see: A table of every package Syft found — name, version, type (pip, etc.). This is your bill of materials.

To generate the machine-readable files:


syft pursh/ --output cyclonedx-json=scan-results\pursh.cyclonedx.json
syft pursh/ --output spdx-json=scan-results\pursh.spdx.json
Then scan the SBOM with Grype:


$grype = ".\scanners\grype-bin\grype.exe"
& $grype "sbom:scan-results\pursh.cyclonedx.json" -o table
What Grype shows: Same as Trivy — CVE table against your SBOM. Cross-validates Trivy's SCA results.

4 — Secrets (Gitleaks)

$gitleaks = ".\scanners\gitleaks-bin\gitleaks.exe"
& $gitleaks detect --source . --config scanners\gitleaks\.gitleaks.toml --verbose
What you'll see: Any matched secret pattern with the file, line number, matched string (truncated), and rule name. "No leaks found" = clean.

5 — DAST (ZAP) — needs the app running first
Terminal 1 — start the app:


cd aisec
$env:SUPABASE_URL="https://placeholder.supabase.co"
$env:SUPABASE_ANON_KEY="placeholder"
$env:SUPABASE_JWT_SECRET="placeholder-32-chars-minimum-here"
$env:DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090
Terminal 2 — verify the app is up:


Invoke-WebRequest -Uri "http://localhost:8090/healthz" | Select-Object StatusCode, Content
Terminal 2 — run ZAP:


$out = "$PWD\scan-results"
docker run --rm -v "${out}:/zap/wrk/:rw" `
  ghcr.io/zaproxy/zaproxy:stable `
  zap-baseline.py `
  -t "http://host.docker.internal:8090" `
  -J "zap-report.json" `
  -r "zap-report.html" `
  -I
What you'll see: ZAP prints each alert as it finds it — PASS/WARN/FAIL per check. At the end it shows a summary table with alert name, risk level (High/Medium/Low/Informational), and count.

To read the HTML report (nicely formatted):


Start-Process "scan-results\zap-report.html"
Quick reference
Scanner	Command prefix	Output to watch
SAST	semgrep --config p/owasp-top-ten pursh/	Finding count at the bottom
SCA	trivy fs --severity CRITICAL,HIGH pursh/	CVE table per requirements file
SBOM	syft pursh/ --output table	Package inventory table
Grype	.\scanners\grype-bin\grype.exe sbom:scan-results\pursh.cyclonedx.json	CVE table from SBOM
Secrets	.\scanners\gitleaks-bin\gitleaks.exe detect --source . --config ...	Leak list or "no leaks found"
DAST	docker run ... zap-baseline.py -t http://host.docker.internal:8090	Alert table + HTML report
Run them in that order — SBOM before Grype (Grype needs the SBOM file), and start the app before ZAP