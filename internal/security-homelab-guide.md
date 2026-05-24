# Enterprise-Style Security Home Lab — Tool Reference & Build Guide

**Profile:** All four domains (AppSec, Vuln Mgmt, Network, SIEM/Blue Team) · Goal: realistic enterprise simulation · Host: single laptop/PC running VMs.

---

## 0. Read this first — the single-machine reality

A real enterprise SOC runs these tools across dozens of servers, 24/7. On one laptop you **cannot** run all of them at once, and pretending otherwise is how home labs die. The realistic approach is **scenario-based profiles**: a small always-on core, plus subsets you spin up only for the exercise you're doing.

**Licensing legend** — matters for an "enterprise" context:
- `[OSS]` = genuinely open source, free for any use.
- `[Freemium]` = commercial product, free tier with limits. Not open source. (Snyk, Qualys, Nessus fall here — the tools you originally named.)

**Status tags** — shows exactly where each tool sits in the AISec pipeline:

| Tag | Meaning |
|---|---|
| `[ACTIVE · AISec CI]` | Normalizer built, tests passing, wired into CI — findings flow into the AISec DB today |
| `[Planned · Phase N]` | `ScannerName` enum entry exists, normalizer not yet built — next phase of CLAUDE.md §7 |
| `[Homelab · Docker]` | Homelab-only; run as a container; not part of the AISec ingestion pipeline |
| `[Homelab · EC2]` | Homelab-only; run on EC2 sprint instance due to RAM requirements |
| `[Homelab · VM]` | Homelab-only; requires a full VM (firewall, Windows targets, attacker box) |
| `[Homelab · CLI]` | Homelab-only; CLI tool, no persistent server overhead |
| `[Skip · Freemium]` | Commercial / closed-source — the OSS equivalent is listed inline |

RAM tag appended where non-trivial, e.g. `[4 GB]`.

**Realistic hardware floor:**

| Your RAM | What's actually feasible |
|---|---|
| 16 GB | One scenario at a time. Containerize aggressively. SIEM *or* full NSM, not both. |
| 32 GB | Comfortable. Core stack + one heavy scenario (e.g. small AD lab). **Recommended minimum.** |
| 64 GB+ | Near-enterprise. Multi-VM AD lab + SIEM + IDS concurrently. |

**Base platform:** Type-2 hypervisor (VirtualBox `[OSS]` or VMware Workstation, free for personal use) for full VMs, **plus Docker/Podman** `[OSS]` for the app/scanner tools — containers use a fraction of the RAM of full VMs. Run the heavy stuff in containers, keep VMs for things that must be a real OS (firewall, Windows hosts, attacker box).

**Network segmentation (do this — it's what makes it "enterprise"):** Use a firewall VM as the gateway and split into virtual subnets so traffic actually crosses boundaries you can monitor.

```
                 ┌─────────────────────────────────────────┐
   Host NIC ───► │  pfSense/OPNsense VM (router+firewall)    │
                 └───┬──────────┬───────────┬────────────┬───┘
                     │          │           │            │
              MGMT 10.0.1.0  CORP 10.0.10.0  DMZ 10.0.20.0  RED 10.0.30.0
              (SIEM, mgmt)  (Win/Linux hosts) (vuln web apps) (Kali/attacker)
                     │          │           │            │
              IDS sensor taps span/mirror these segments ──► Suricata/Zeek ──► SIEM
```

---

## 1. App & Code Security (SAST · DAST · SCA)

**SAST = scans source code. DAST = attacks the running app. SCA = scans dependencies.** A real pipeline uses all three.

### Static Analysis (SAST)
- **Semgrep** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — Pattern/rule-based static analysis across 30+ languages. Fast, low false-positives, custom rules in readable YAML. The AISec SAST workhorse — normalizer + golden-file tests built. *normalizer: `ingest/sarif/normalizer.py`*
- **SonarQube Community Edition** `[Freemium]` `[Homelab · Docker · 2-4 GB]` — Code quality + security hotspots with a polished dashboard, history, and quality gates. CE is free (source-available, not OSI-open); advanced rules and branch analysis are paid. Great for the "central dashboard" feel of an enterprise. Not integrated into AISec pipeline — use for the UI/UX learning.
- **Language-specific linters** `[OSS]` `[Homelab · CLI]` — **Bandit** (Python), **gosec** (Go), **Brakeman** (Ruby/Rails), **njsscan** (Node). Lightweight, drop into CI. Not yet in AISec normalizer; output can feed DefectDojo directly.

### Dependency / Supply-Chain (SCA)
- **OWASP Dependency-Check** `[OSS]` `[Homelab · Docker]` — Flags known-vulnerable libraries via CVE matching. The classic OSS SCA tool. Not in AISec pipeline — use standalone or feed DefectDojo.
- **Trivy FS** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — Swiss-army scanner: dependencies **+ container images + IaC + secrets**. One binary, fast, huge coverage. Filesystem scanner normalizer + tests built. *normalizer: `ingest/sarif/normalizer.py`*
- **Trivy Image** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — Container image variant of Trivy. Wired in `_TOOL_NAME_MAP` as `trivy-image`. Pre-push gate in CI.
- **Grype** `[OSS]` `[Planned · Phase 4]` `[Docker · <1 GB]` — Container/filesystem vuln scanner, pairs with **Syft** for SBOM generation. `ScannerName.GRYPE` in enum; `_TOOL_NAME_MAP` entry now added — normalizer to be built in Phase 4.
- **Syft** `[OSS]` `[Planned · Phase 4]` `[Docker · <1 GB]` — SBOM generator (CycloneDX 1.5 + SPDX 2.3). Already generating SBOMs; `ScannerName.SYFT` in enum; ingestion adapter TBD Phase 4.
- **Snyk** `[Skip · Freemium]` — Polished SaaS SCA/SAST. Free tier limited, phones home. **Trivy + Dependency-Check are the OSS equivalents.**

### Dynamic Analysis (DAST)
- **OWASP ZAP** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — Flagship OSS web app scanner. Intercepting proxy + active/passive scanner + automation. `_TOOL_NAME_MAP` entry exists; baseline on every PR, full scan nightly.
- **Nikto** `[OSS]` `[Homelab · CLI]` — Fast web server misconfiguration/known-vuln scanner. Noisy but a good first pass. Not in AISec pipeline — run ad-hoc against DMZ targets.
- **Nuclei** `[OSS]` `[Homelab · CLI]` — Template-driven scanner (thousands of community CVE/misconfig templates). Excellent for targeted/CI scanning alongside OpenVAS. Not in AISec normalizer yet.

### Secrets & IaC
- **Gitleaks** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — Hunt committed API keys/passwords in git history and PRs. Normalizer + golden-file tests built. *normalizer: `ingest/sarif/normalizer.py`*
- **detect-secrets** `[OSS]` `[Planned · Phase 6]` `[CLI]` — Stripe's secret scanner; complements Gitleaks in pre-commit. `ScannerName.DETECT_SECRETS` in enum; `_TOOL_NAME_MAP` entry now added.
- **TruffleHog** `[OSS]` `[Homelab · CLI]` — Alternative secret scanner with verified-secret detection. Not in AISec pipeline; use for manual deep-history scans.
- **Checkov** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — IaC scanning: Terraform, K8s, CloudFormation. Normalizer + golden-file tests built; discipline tagged `DEVSECOPS`. *normalizer: `ingest/sarif/normalizer.py`*
- **tfsec** `[OSS]` `[ACTIVE · AISec CI]` `[Docker · <1 GB]` — Terraform-specific security scanner. `_TOOL_NAME_MAP` entry exists. Runs alongside Checkov in CI for cross-validation.
- **KICS** `[OSS]` `[Homelab · CLI]` — IaC scanning across more formats than Checkov/tfsec (Ansible, Dockerfile, ARM). Not in AISec pipeline — good stretch addition.

---

## 2. Vulnerability Management & Scanning

### Scanners
- **Greenbone / OpenVAS (Community Edition)** `[OSS]` `[Homelab · EC2 · 4 GB]` — Full network vulnerability scanner with 100k+ checks (NVTs). The genuine OSS equivalent of Nessus/Qualys. Heaviest tool in this section; ~4 GB RAM and slow first NVT sync. Run on EC2 sprint instance — pipe results into DefectDojo via XML import.
- **Nmap** `[OSS]` `[Homelab · CLI]` — Foundational. Host discovery, port/service/version detection, OS fingerprinting, and the **NSE** scripting engine for light vuln checks. Every scan starts here. Install once, use always.
- **Nuclei** `[OSS]` `[Homelab · CLI]` — Template-driven vuln detection; thousands of community CVE/misconfig templates. Far lighter than OpenVAS — excellent for targeted/CI scanning. Complements rather than replaces a full scanner.
- **Nessus Essentials** `[Skip · Freemium]` — Free for up to 16 IPs, not open source. **OpenVAS is the OSS equivalent.**
- **Qualys Community Edition** `[Skip · Freemium]` — Cloud-based, commercial. Same story — OpenVAS covers you.

### Vulnerability Management (the "enterprise" glue)
- **DefectDojo** `[OSS]` `[Homelab · Docker · 2 GB]` — Aggregates output from Semgrep, ZAP, Trivy, Nmap, OpenVAS, Nuclei, etc. into one platform with dedup, triage, SLA tracking, and metrics. **This is what turns a pile of scanners into a real vuln-management program.** Deploy this first in your homelab stack — it is the backbone of the remediation loop (§10).
- **Faraday** `[OSS]` `[Homelab · Docker]` — Alternative collaborative vuln-management/pentest platform. Good if you want a second opinion on DefectDojo's UX.

---

## 3. Network & Traffic Analysis (IDS/IPS · NSM · Packet)

- **Wireshark** `[OSS]` `[Homelab · CLI/GUI]` — The definitive packet analyzer — deep protocol dissection, follow streams, decrypt TLS with session keys. Plus **tshark/tcpdump** for CLI/headless capture. Your manual deep-dive tool. Zero RAM overhead when idle.
- **Suricata** `[OSS]` `[Homelab · Docker · 1 GB]` — High-performance IDS/IPS + NSM. Rule-based detection (Emerging Threats ruleset), protocol logging, file extraction. **The primary OSS IDS to deploy.** Feed its EVE JSON alerts into Wazuh. Run as a Docker container sniffing a bridge network for local scenario practice.
- **Zeek** (formerly Bro) `[OSS]` `[Homelab · Docker · 1 GB]` — Not signature-based — generates rich structured logs of *everything* on the wire (conn, dns, http, ssl, files). Pair with Suricata: Suricata says "alert," Zeek gives the full context. Gold-standard NSM data source for a SIEM. Deploy alongside Suricata as a scenario stack.
- **Snort 3** `[OSS]` `[Homelab · Docker]` (Cisco) — The original IDS/IPS. Suricata is the more common homelab choice today, but Snort is worth knowing for industry recognition. Good stretch alternative.
- **pfSense / OPNsense** `[OSS]` `[Homelab · VM · 1-2 GB]` — Firewall/router VM. Gateway that creates your segmented subnets (§0); run IDS inline here. Only spin up when doing network-segmentation scenarios.
- **Arkime** (formerly Moloch) `[OSS]` `[Homelab · EC2 · heavy]` — Full-packet-capture indexing and search at scale. Needs Elasticsearch (~4 GB+). Only deploy on EC2 when specifically practicing PCAP retention/search.
- **Security Onion** `[OSS]` `[Homelab · VM · 12-16 GB]` — A whole distro bundling Suricata + Zeek + Elastic + Wazuh, pre-integrated. *Either/or at 16 GB:* run Security Onion for a turnkey SOC-in-a-box, **or** build components individually to understand the pieces. For learning, build the pieces; Security Onion is the "shortcut after you've already learned."

---

## 4. SIEM / Blue Team (Logging · Detection · DFIR · Threat Intel)

### Log aggregation / SIEM core
- **Wazuh** `[OSS]` `[Homelab · EC2 · 4 GB]` — SIEM + XDR + HIDS. Lightweight agents on Windows/Linux hosts report FIM, log data, vuln detection, and compliance (PCI/NIST/HIPAA packs built-in). **The single best OSS SIEM starting point.** Forked from OSSEC, far more capable. Run manager on EC2 t3.large; agents connect over SSH tunnel from local VMs.
- **Elastic Stack (ELK)** `[Freemium-ish]` `[Homelab · EC2 · 4 GB+]` — Elasticsearch + Logstash + Kibana. The storage/search/visualization layer that Wazuh dashboard, Security Onion, and Arkime all sit on. Core features free; advanced security features gated. RAM-hungry — Elasticsearch alone wants 2–4 GB+. On EC2; not needed if using Wazuh's built-in OpenSearch dashboard.
- **Graylog** `[OSS]` `[Homelab · Docker · 2 GB]` — Leaner log-management alternative to full ELK with a friendlier UI. Better choice than ELK on a 16 GB host when you just need centralized syslog + search.

### Detection content & response
- **Sigma** `[OSS]` `[Homelab · CLI]` — Vendor-neutral detection rule format ("the YARA of logs"). Write once, compile to Wazuh/Elastic/Splunk queries via `sigma convert`. Zero overhead — pure YAML rules. Build your detection library here; one rule per Atomic Red Team technique you validate.
- **TheHive + Cortex** `[OSS]` `[Homelab · EC2 · 3 GB]` — IR case management (TheHive) + automated enrichment (Cortex). Wazuh alerts flow in via webhook; Cortex analyzers call VirusTotal, AbuseIPDB, MISP automatically. The "enterprise SOC workflow" piece. Run on EC2 alongside Wazuh.
- **MISP** `[OSS]` `[Homelab · EC2 · 3 GB]` — Threat-intelligence sharing platform. Ingest IOC feeds, correlate against Wazuh/TheHive detections. The context layer that turns a raw IP into "attributed to FIN7." Heavy — add to EC2 sprint stack, not always-on.
- **Velociraptor** `[OSS]` `[Homelab · Docker · <1 GB]` — Endpoint DFIR/hunting — query all hosts simultaneously with VQL: "show me processes spawned last hour," "find files modified in /etc." Trivially light server; agents are ~20 MB. Run locally or on EC2; agents connect from all VMs.
- **OSSEC** `[OSS]` `[Homelab · skip]` — The HIDS Wazuh forked from. Skip in favor of Wazuh — it is the modern, maintained replacement. Know the lineage; don't deploy OSSEC.

### Generate detections to test against (key for "realistic")
- **Atomic Red Team** `[OSS]` `[Homelab · CLI]` (Red Canary) — Library of MITRE ATT&CK-mapped attack tests in PowerShell/bash. Run one atomic, confirm Wazuh/Suricata caught it, write the Sigma rule. The core "build → validate" feedback loop. No server overhead — just scripts.
- **MITRE Caldera** `[OSS]` `[Homelab · Docker · 1 GB]` — Automated adversary emulation: chains multiple ATT&CK techniques into full kill-chain operations via agent model. More realistic than individual atomics — validates end-to-end detection coverage.

---

## 5. Targets — what you actually scan & attack (don't skip)

A SIEM with nothing happening is boring. You need vulnerable, realistic targets:

- **OWASP Juice Shop** `[OSS]` `[Homelab · Docker · <1 GB]` — Deliberately vulnerable e-commerce app covering OWASP Top 10. Point ZAP/Nuclei/Nikto at it; put it in the DMZ subnet. Best starting target — always-on, container.
- **OWASP WebGoat** `[OSS]` `[Homelab · Docker · <1 GB]` — Unlike Juice Shop (CTF-style), WebGoat is a **structured learning platform** — each vuln has a lesson + exploit challenge + fix guidance. Use when you want to learn the remediation, not just find the bug.
- **DVWA** `[OSS]` `[Homelab · Docker · <1 GB]` — Classic. Adjustable difficulty levels; good for beginners before moving to Juice Shop.
- **bWAPP** `[OSS]` `[Homelab · Docker · <1 GB]` — 100+ web vulnerabilities. Useful for breadth coverage across less-common vuln classes.
- **OWASP crAPI** `[OSS]` `[Homelab · Docker · <1 GB]` — Deliberately vulnerable REST + GraphQL API. Covers OWASP API Top 10. Essential — AISec and Pursh are both FastAPI-backed, so API vuln practice is directly relevant.
- **Vulhub** `[OSS]` `[Homelab · Docker · <1 GB]` — Dockerized real-CVE environments (Log4Shell, Spring4Shell, Confluence RCE, Apache Struts, etc.). The remediation-loop target: spin up the vulnerable version → exploit the real CVE → apply the vendor patch → rescan to confirm fixed.
- **Metasploitable 2/3** `[OSS]` `[Homelab · VM]` — Intentionally vulnerable Linux/Windows VMs. Classic exploitation practice; point Metasploit at it and watch the SIEM light up.
- **VulnHub** boxes `[OSS]` `[Homelab · VM]` — Hundreds of free vulnerable VMs (boot-to-root). Great for offensive-validation skill building.
- **GOAD (Game of Active Directory)** `[OSS]` `[Homelab · VM · 24-32 GB]` — Pre-built vulnerable Windows AD lab (Kerberoasting, AD CS, lateral movement). *Very* enterprise-realistic but multiple Windows VMs = 24–32 GB+. Save for 32 GB+ host or trimmed EC2.
- **DetectionLab** `[OSS]` `[Homelab · VM · 16+ GB]` — Windows AD + Splunk/Velociraptor pre-wired for *detection* practice. Same RAM caveat as GOAD. Good if you want the detection side of AD without building GOAD from scratch.

---

## 6. Offensive / validation toolkit (optional, but realistic enterprises red-team themselves)

- **Kali Linux** `[OSS]` `[Homelab · VM · 2-4 GB]` — Attacker VM with the full toolset pre-loaded. One dedicated VM in the RED subnet. Use it to generate real attack traffic that your blue-team stack (Suricata + Wazuh) must detect.
- **Parrot OS** `[OSS]` `[Homelab · VM · 2-4 GB]` — Lighter alternative to Kali. Same purpose — RED subnet attacker box.
- **Metasploit Framework** `[OSS]` `[Homelab · included in Kali]` — Exploitation framework — develop/launch exploits against Metasploitable/Vulhub targets, generate the activity your blue side detects. Comes pre-installed in Kali.
- **Burp Suite Community** `[Skip · Freemium (active scanner)]` — Manual web-app testing proxy. The active scanner is paid. **ZAP fills that gap for free** — use ZAP for automated DAST, Burp Community only for manual proxy intercept work.

---

## 7. Suggested phased build (16 GB laptop + EC2 sprints)

Don't deploy everything. Build in waves; tear down what you're not actively using.

**RAM budget rule for 16 GB:** always-on Docker stack ≤ 7 GB, leaving OS + browser headroom. Scenario stacks are spin-up/tear-down. Heavy stacks (Wazuh, OpenVAS, TheHive) live on EC2.

**EC2 budget rule for $100 credit:** t3.large is $0.083/hr → 8 hrs/day = $0.66/day → ~150 days of learning sprints. **Always stop the instance when done for the day.**

**Phase 1 — AppSec core (always-on local, ~4 GB Docker):**
1. Docker installed; WSL2 backend on Windows.
2. **DefectDojo** container — the vuln-management hub everything feeds into.
3. **OWASP Dependency-Track** container — continuous SBOM/CVE monitoring (Syft already generates CycloneDX).
4. **Juice Shop + crAPI** in DMZ — your always-available scan targets.
5. Existing AISec scanners (Semgrep, Trivy, ZAP, Gitleaks) piped into DefectDojo. Run the remediation loop (§10) on every finding.

**Phase 2 — SIEM + IR on EC2 (spin up for sprint, stop when done):**
1. Launch t3.large EC2, Ubuntu 22.04.
2. Docker Compose: **Wazuh manager + dashboard + agents** (~4 GB).
3. Add **TheHive + Cortex** (~3 GB) alongside — same instance, 16 GB total fits.
4. Install **Velociraptor** server; deploy agents on local VMs via VPN or SSH tunnel.
5. Practice: generate a finding in DefectDojo → escalate to TheHive case → investigate with Velociraptor → close with postmortem.

**Phase 3 — Network monitoring (local, scenario-based):**
Add **Suricata + Zeek** as Docker containers sniffing a bridge network. Spin up a **Vulhub** CVE box in the same bridge. Attack from host, watch Suricata alert, Zeek log context, Wazuh ingest both. Write a **Sigma** rule for the attack pattern.

**Phase 4 — Vuln management depth (EC2 sprint):**
Add **OpenVAS/Greenbone** to the EC2 instance (swap TheHive out if RAM-constrained, or use a second t3.large). Scan the EC2's own VPC + target subnets. Pipe OpenVAS results into DefectDojo. Practice triage-to-fix on every High/Critical. Run **Lynis** and **OpenSCAP** against the EC2 host itself.

**Phase 5 — Detection engineering:**
Write **Sigma** rules for every ATT&CK technique you've triggered in Phase 3. Run **Atomic Red Team** atomics, confirm Wazuh catches each one. Run **MITRE Caldera** for full kill-chain validation. Add **MISP** to the EC2 stack for IOC enrichment of TheHive cases.

**Phase 6 — Compliance evidence (local + EC2):**
Run **InSpec** compliance profiles (PCI-DSS, SOC 2, NIST CSF) against your EC2 host and Docker containers. Export HTML reports into `/docs/compliance/evidence/`. Map every failing control to an open DefectDojo finding. This is the auditor-persona workflow.

**Phase 7 — Deception + WAF (local, always-on lightweight):**
Add **Cowrie** (SSH honeypot) + **OpenCanary** (multi-protocol) to local Docker. Deploy **ModSecurity + OWASP CRS** in front of Juice Shop. Attack the WAF from host, observe what gets blocked and what bypasses. This teaches both sides: WAF tuning and WAF bypass.

**Phase 8 — Stretch (32 GB+ or beefy EC2 only):**
**GOAD/DetectionLab** for Windows AD attack-and-detect. **Security Onion** as turnkey NSM/SIEM replacement. **Arkime** for full-PCAP retention. These are the "senior depth" additions.

---

## 8. Quick reference — recommended OSS stack by domain

| Domain | Deploy these (OSS) | Where | Skip / freemium-only |
|---|---|---|---|
| SAST | Semgrep, SonarQube CE, Bandit/gosec | Local Docker | — |
| SCA | Trivy, OWASP Dependency-Check, Grype | Local Docker | Snyk |
| DAST | OWASP ZAP, Nikto, Nuclei | Local Docker | Burp Pro |
| SBOM monitor | **OWASP Dependency-Track** | Local Docker (always-on) | — |
| Vuln scan | OpenVAS/Greenbone, Nmap, Nuclei | EC2 sprint / Local CLI | Nessus, Qualys |
| Vuln mgmt | **DefectDojo** | Local Docker (always-on) | — |
| Compliance scan | OpenSCAP, Lynis, InSpec | Local CLI / EC2 | — |
| Network IDS/NSM | Suricata, Zeek, Wireshark, pfSense | Local Docker (scenario) | — |
| SIEM | **Wazuh**, Graylog/ELK | EC2 sprint | Splunk (free tier capped) |
| IR / DFIR | TheHive+Cortex, Velociraptor | EC2 sprint / Local Docker | — |
| Threat intel | MISP | EC2 sprint | — |
| Detection val. | Atomic Red Team, Caldera, Sigma | Local (scripts/CLI) | — |
| Container runtime | **Falco** | Local Docker | — |
| K8s compliance | kube-bench | Local CLI | — |
| WAF | ModSecurity + OWASP CRS | Local Docker | — |
| Deception | Cowrie, OpenCanary | Local Docker | — |
| Targets | Juice Shop, **crAPI**, Vulhub, WebGoat, Metasploitable, GOAD | Local Docker / VM | — |

> **16 GB honest priorities:** **DefectDojo** (always-on, ties everything together) + **Dependency-Track** (SBOM monitoring) + **Semgrep/Trivy/ZAP** (AppSec, containers) + **Wazuh + TheHive** on EC2 for IR sprints + **Suricata/Zeek** for network scenarios. That is a credible enterprise-style program inside 16 GB local + $100 EC2 budget.

---

## 9. Net-new OSS tools (beyond original guide)

These are tools **not** in the original §1–6 above and not already in the AISec CI pipeline. Each is genuinely open-source.

### 9.1 Vuln Management & Remediation Lifecycle

**OWASP Dependency-Track** `[OSS]`
Ingests CycloneDX / SPDX SBOMs (Syft already generates these) and continuously monitors every component against NVD + OSV + GitHub Advisory. Raises a policy violation the moment a new CVE hits a component you ship — without re-running a scan. The compliance angle: PCI-DSS Req 6.3.3 requires component inventory; Dependency-Track is the evidence artifact. ~2 GB Docker.

**DefectDojo** `[OSS]` (OWASP) ← already in §2 but worth re-emphasising its remediation role
The critical distinction between DefectDojo and raw scanner output: DefectDojo tracks the **lifecycle** of every finding (New → Active → Risk Accepted → Resolved → Closed), enforces SLA policies (Critical fixed in 7 days, High in 30), deduplicates the same vuln found by three different scanners, and gives you metrics over time (MTTR, open/closed velocity, false-positive rate). This is what turns "I ran Semgrep" into "I run a vulnerability management program."

### 9.2 Compliance-as-Code & Benchmarking

**OpenSCAP** `[OSS]` + SCAP Security Guide (SSG)
Runs SCAP content (XCCDF profiles) against Linux hosts to check compliance with CIS Benchmarks, NIST 800-53, PCI-DSS, and HIPAA. Generates scored HTML evidence reports — exactly what an auditor asks for. `oscap xccdf eval --profile cis_server_l1 --results result.xml ssg-ubuntu2204-ds.xml`. Completely CLI, no RAM overhead.

**Lynis** `[OSS]` (CISOfy)
Lightweight host-hardening auditor. `lynis audit system` runs in ~60 seconds, scores the host 1–100, and generates a prioritized remediation list. Run it on every new VM before doing anything else. Maps suggestions to CIS Controls v8. No agents, no server.

**InSpec** `[OSS]` (Chef/Progress)
Compliance-as-code: write audit controls in Ruby DSL, execute against local hosts, Docker containers, or AWS (via `inspec-aws`). Community profiles exist for PCI-DSS, SOC 2 Trust Services Criteria, CIS, and HIPAA. The key differentiator: your compliance checks live in version control, run in CI, and produce machine-readable JSON that feeds into DefectDojo or a compliance dashboard.

### 9.3 Detection Engineering

**Sigma** `[OSS]`
The vendor-neutral detection rule format. Write a rule once in YAML, compile it to Wazuh/Elastic/Splunk/Sentinel queries via `sigma convert`. Every time you run an Atomic Red Team test and catch the technique, write the Sigma rule for it — that's your detection library growing. The SigmaHQ/sigma repository has 3,000+ community rules to import as a baseline.

**Atomic Red Team** `[OSS]` (Red Canary)
A library of hundreds of small, targeted MITRE ATT&CK-mapped attack tests in PowerShell and bash. Run one atomic (`Invoke-AtomicTest T1059.001`), then check whether Wazuh/Suricata generated the expected alert. This is the "build → test → iterate" feedback loop that makes detections real. Zero infrastructure overhead — just scripts.

**MITRE Caldera** `[OSS]`
Automated adversary emulation that chains atomics into full kill-chain scenarios using an agent model. More realistic than individual atomics: Caldera runs multi-step operations (recon → initial access → persistence → lateral movement) so you can validate end-to-end detection coverage, not just individual technique detection. ~1 GB Docker.

### 9.4 Endpoint DFIR

**Velociraptor** `[OSS]`
Think of it as "live forensics at scale." Deploy a Velociraptor server, install lightweight agents on your VMs, then hunt across all hosts simultaneously with VQL queries: "show me all processes that executed in the last hour," "find all files modified in /etc," "extract browser history." Essential for IR practice — when TheHive escalates a case, Velociraptor is how you investigate the host. Server is ~200 MB, agent is ~20 MB.

### 9.5 Threat Intelligence

**MISP** `[OSS]` (Malware Information Sharing Platform)
Ingest IOC feeds (CIRCL, abuse.ch, Emerging Threats), then correlate against Wazuh alerts in TheHive via Cortex analyzers. When an IP in a Wazuh alert matches a known C2 in MISP, Cortex flags it automatically. Heavy (~3 GB) — run on EC2 alongside Wazuh+TheHive. MISP is the "context layer" that turns a raw IP alert into "this is attributed to FIN7."

### 9.6 Container & Runtime Security

**Falco** `[OSS]` (CNCF)
Monitors Linux syscalls at runtime and fires alerts when containers do unexpected things: shell spawned in a container, unexpected network connection, /etc/passwd read. Zero application code changes. Add to AISec CI as a Docker container alongside your scanner containers — any scanner that tries to do something unexpected will trigger a Falco alert. Essentially free on RAM.

**kube-bench** `[OSS]` (Aqua)
CLI tool that checks a running Kubernetes cluster against CIS Kubernetes Benchmark controls. No server, no agent — just `kube-bench run --targets node`. Output maps to CIS control IDs which map to SOC 2 CC6.x and NIST CSF controls. Run it against any k3s/kind/EKS cluster you spin up.

### 9.7 Deception

**Cowrie** `[OSS]`
A medium-interaction SSH + Telnet honeypot. When an attacker (or your Kali VM) hits the fake SSH port, Cowrie logs every command they run, every file they try to download, every credential they try. Feed the JSON logs to Wazuh. You learn attacker TTPs by watching them operate. Trivially light in Docker.

**OpenCanary** `[OSS]` (Thinkst)
Multi-protocol honeypot: fake SMB shares, fake FTP, fake HTTP admin pages, fake RDP. Any connection to these is a high-confidence alert — legitimate users never touch them. Low noise, high signal. A single OpenCanary touch should open a TheHive case automatically. ~50 MB Docker.

### 9.8 WAF

**ModSecurity v3 + OWASP Core Rule Set (CRS)** `[OSS]`
A WAF engine you deploy as an Nginx or Apache module (or standalone container) in front of any web app. The OWASP CRS is the default ruleset — 300+ rules blocking SQLi, XSS, RCE, path traversal, scanner signatures, and more. Deploy in front of Juice Shop or Pursh, attack it with ZAP, observe what the WAF blocks (and what it misses). Then tune the CRS paranoia level and repeat. Teaching both sides: protection design and bypass research.

### 9.9 API Security Target

**OWASP crAPI** `[OSS]` (Completely Ridiculous API)
A deliberately vulnerable REST + GraphQL API application covering all OWASP API Security Top 10 vulnerabilities: broken object-level auth, broken function-level auth, mass assignment, excessive data exposure, lack of rate limiting, etc. Essential for API-security learning given AISec and Pursh are both FastAPI-backed. Scan it with ZAP API scan, Nuclei API templates, and manual Burp Community. Fix it mentally (or in a fork) to learn remediations.

### 9.10 Remediation-Focused Vulnerable Targets

**OWASP WebGoat** `[OSS]`
Unlike Juice Shop (which is a CTF-style app), WebGoat is a **structured learning platform** — each vulnerability has a lesson page explaining the weakness, then a challenge to exploit it, then guidance on the fix. The goal is not just to find the bug but to understand why the fix works. Use it as a study companion to DefectDojo findings: see a SQL injection in DefectDojo → open WebGoat's SQLi lesson → fix the real code.

**Vulhub** `[OSS]`
Pre-built Docker Compose environments for hundreds of real CVEs (Log4Shell, Spring4Shell, Apache Struts, Confluence RCE, etc.). The workflow: spin up the vulnerable version → exploit the real CVE → apply the real vendor patch → rescan with Trivy/Nuclei to confirm the finding is gone → record in DefectDojo as "Fixed." This is the closest thing to a real remediation cycle you can do without a production system.

---

## 10. The Remediation Learning Loop

Scanning without fixing is just a pile of data. The loop below is the first-class process — run it for every significant finding.

```
┌─────────────────────────────────────────────────────────────┐
│                  REMEDIATION LEARNING LOOP                  │
│                                                             │
│  1. SCAN      → Finding appears in DefectDojo               │
│                  (Semgrep / Trivy / ZAP / OpenVAS / etc.)   │
│                                                             │
│  2. TRIAGE    → Tag CWE, severity, compliance controls       │
│                  (HIPAA / PCI-DSS / NIST CSF / SOC 2)       │
│                  Assign SLA deadline                        │
│                                                             │
│  3. LEARN     → Look up CWE in /docs/secure-coding/         │
│                  Reproduce in WebGoat (web vulns) or        │
│                  Vulhub (CVEs) in a safe container          │
│                  Understand the root cause — not just fix   │
│                                                             │
│  4. REMEDIATE → Fix the code / config / infra               │
│                  Write a test that would have caught it     │
│                                                             │
│  5. VERIFY    → Rescan with same tool                       │
│                  Confirm DefectDojo status → "Resolved"     │
│                  Gate: do not close without a rescan        │
│                                                             │
│  6. DOCUMENT  → Append to /docs/skills/bug-log.md           │
│                  Bug → Root cause → Fix → Prevention        │
│                  Link Sigma rule if applicable              │
└─────────────────────────────────────────────────────────────┘
```

**Why the loop matters:** Most security engineers can find vulnerabilities. The differentiating skill is the closed-loop discipline — tracking every finding to verified remediation, measuring MTTR, and building institutional knowledge in the bug log. DefectDojo enforces the lifecycle; the bug log builds the knowledge base.

**SLA targets (use these as your DefectDojo policy):**

| Severity | Target remediation time |
|---|---|
| Critical | 3 days |
| High | 14 days |
| Medium | 30 days |
| Low | 90 days |
| Info | No SLA — batch quarterly |

**Compliance integration:** Every remediated finding should reference the compliance control it satisfies (e.g., "PCI-DSS Req 6.3.3 — confirmed no High/Critical in cardholder-data-path deps"). This is the evidence trail an auditor reads.

---

## 11. EC2 Sprint Strategy ($100 credit)

**Cost reality:**

| Instance | vCPU | RAM | $/hr | 8-hr day | Days from $100 |
|---|---|---|---|---|---|
| t3.large | 2 | 8 GB | $0.083 | $0.66 | ~151 days |
| t3.xlarge | 4 | 16 GB | $0.166 | $1.33 | ~75 days |
| m5.large | 2 | 8 GB | $0.096 | $0.77 | ~130 days |

**Recommendation:** use **t3.xlarge** for the full SIEM+IR stack (16 GB fits Wazuh + TheHive + OpenVAS + MISP together). At $1.33/day for an 8-hour learning sprint, $100 buys 75 full learning days — essentially unlimited for practical purposes.

**Critical discipline: stop the instance every night.** A t3.xlarge left running 24/7 costs $120/month — over budget. Add an **AWS Instance Scheduler** or just set a daily CloudWatch alarm at $5 spend to alert you.

**EC2 sprint stack layout:**

```
t3.xlarge (16 GB) — Ubuntu 22.04 — Docker Compose

Services (docker-compose up):
  wazuh-manager      4 GB   SIEM + compliance packs
  wazuh-dashboard    1 GB   OpenSearch Dashboards
  thehive            2 GB   IR case management
  cortex             1 GB   Automated enrichment analyzers
  misp               2 GB   Threat intel (optional — add when doing IR practice)
  openvas            4 GB   Network vuln scanner (run as separate profile)
  velociraptor       0.5 GB DFIR server (agents on local VMs via SSH tunnel)
  ─────────────────────────
  Total              ~14.5 GB ✓ (stop OpenVAS when running MISP, both use 4 GB)
```

**Setup checklist for EC2 sprint:**
1. Launch t3.xlarge, Ubuntu 22.04, 50 GB gp3 root volume.
2. Security group: SSH (22) from your IP only, Wazuh dashboard (443), TheHive (9000), Cortex (9001) — nothing public by default.
3. Use SSH tunnel for all browser access: `ssh -L 443:localhost:443 ubuntu@<ec2-ip>` — never expose management UIs to the internet.
4. Clone your homelab Docker Compose configs; `docker compose up -d`.
5. Connect local Wazuh agents via the manager's IP (reachable over VPN or SSH tunnel).
6. When the session ends: `docker compose stop`, then **stop the EC2 instance** (not terminate — you want to resume next time).

**What to keep local vs on EC2:**

| Tool | Local (always-on) | EC2 (sprint) | Reason |
|---|---|---|---|
| DefectDojo | ✓ | — | You want findings persisted across sessions |
| Dependency-Track | ✓ | — | Continuous monitoring, low RAM |
| Semgrep/Trivy/ZAP | ✓ | — | CI pipeline tools, containers |
| Wazuh | — | ✓ | 4 GB RAM, only needed during active practice |
| TheHive + Cortex | — | ✓ | Same reasoning |
| OpenVAS | — | ✓ | 4 GB + slow NVT sync — only worth it per sprint |
| MISP | — | ✓ | Heavy; only needed during threat-intel scenarios |
| Suricata + Zeek | ✓ scenario | — | Docker containers for local network scenarios |
| Falco | ✓ | — | Tiny; useful always-on for container monitoring |
| Cowrie + OpenCanary | ✓ | — | Trivially light; good to always have running |
| Nuclei + Nmap | ✓ | — | CLI tools, no RAM cost |

---

## 12. Compliance Expansion — Framework Reference

Four frameworks beyond HIPAA + GDPR, mapped to the tools above.

### PCI-DSS v4.0 (Payment Card Industry)
Relevant for any app handling card data (even synthetic).

| Requirement | Tooling |
|---|---|
| Req 2 — Secure configs | Lynis, OpenSCAP CIS profile, Wazuh FIM |
| Req 6.3.3 — Patch mgmt / vuln components | Dependency-Track policy violations, Trivy |
| Req 6.4 — Web-app protection | ModSecurity + OWASP CRS (WAF), ZAP scan results |
| Req 10 — Audit logging | Wazuh audit module, Pursh audit_log table |
| Req 11.3 — Vulnerability scanning | OpenVAS quarterly scans, DefectDojo SLA metrics |
| Req 11.4 — Penetration testing | ZAP DAST, Nuclei, manual via Kali |

Evidence artifacts: DefectDojo SLA reports, OpenSCAP HTML, Lynis output, Wazuh compliance dashboard export. See `/docs/compliance/pci-dss-mapping.md`.

### NIST CSF 2.0
The US federal baseline. The `Finding` model's `nist_csf_subcategories` field already exists — it just needs mapping data.

| CSF Function | Tools |
|---|---|
| GV (Govern) | CLAUDE.md policies, CODEOWNERS, SECURITY.md |
| ID (Identify) | Syft SBOM, Nmap asset inventory, Dependency-Track |
| PR (Protect) | Semgrep, Checkov, ModSecurity, KMS, RLS, MFA |
| DE (Detect) | Wazuh, Suricata, Zeek, Falco, Sigma rules |
| RS (Respond) | TheHive runbooks, Cortex enrichment, IR playbooks |
| RC (Recover) | RDS PITR, S3 versioning, chaos-drill results |

See `/docs/compliance/nist-csf-mapping.md`.

### SOC 2 Type II (Trust Services Criteria)
Most relevant framework for SaaS/cloud-native hiring context.

| Trust Criteria | Tools / Evidence |
|---|---|
| CC6.1 — Logical access | Wazuh user monitoring, Supabase RLS tests, OIDC audit logs |
| CC6.3 — Access removal | Offboarding runbook, IAM Access Analyzer |
| CC7.1 — Config monitoring | Wazuh FIM, AWS Config, InSpec runs |
| CC7.2 — Anomaly detection | Wazuh alerts, Suricata rules, Falco events |
| CC8.1 — Change management | Git branch protection, signed commits, PR template checklist |
| A1.2 — Availability monitoring | CloudWatch alarms, uptime metrics, RDS Multi-AZ |

See `/docs/compliance/soc2-mapping.md`.

### CIS Controls v8
Implementation-level controls that map directly to CIS Benchmarks.

| IG1 (Basic) | Tools |
|---|---|
| CIS 1 — Asset inventory | Nmap, Syft SBOM, Dependency-Track |
| CIS 2 — Software inventory | Syft, OWASP Dependency-Check |
| CIS 3 — Data protection | Macie, KMS, RLS, TLS enforcement |
| CIS 4 — Secure config | Lynis, OpenSCAP CIS profiles, kube-bench |
| CIS 7 — Vuln management | DefectDojo full lifecycle |
| CIS 8 — Audit log management | Wazuh, Pursh audit_log table |
| CIS 13 — Network monitoring | Suricata, Zeek, pfSense |
| CIS 17 — Incident response | TheHive runbooks, Velociraptor |
