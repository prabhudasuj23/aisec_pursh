# Security Metrics & KPIs — What Management Actually Tracks

> The numbers that CISOs ask for, what they mean, how to calculate them, and what good vs bad looks like.

---

## Why metrics matter for an AppSec analyst

Without metrics, security is anecdotal. "We're doing security reviews" is not the same as "we reduced critical finding MTTR from 21 days to 4 days this quarter." The second statement is defensible, promotable, and budget-justifiable.

Metrics also protect you: if you're not measuring, you don't know if your program is working, and neither does anyone else.

---

## Core AppSec Metrics

### 1. MTTR — Mean Time to Remediate

**What it measures:** Average time from finding discovery to verified fix, by severity.

**How to calculate:**
```
MTTR = Sum of (closed_date - opened_date) for all findings in period
       ─────────────────────────────────────────────────────────────
                     Total findings closed in period
```

**Targets (industry benchmarks):**

| Severity | Target MTTR | Bad | Unacceptable |
|---|---|---|---|
| Critical | ≤ 7 days | 8–30 days | > 30 days |
| High | ≤ 30 days | 31–90 days | > 90 days |
| Medium | ≤ 90 days | 91–180 days | > 180 days |
| Low | ≤ 180 days | > 180 days | — |

**What MTTR tells you:**
- Consistently high MTTR on Critical → prioritization problem, escalate
- Bimodal MTTR (most close in 2 days, some sit forever) → a few teams are blocking
- MTTR improving quarter over quarter → program is working

**What MTTR hides:**
- If your team bulk-marks old findings as FP to clean up the queue, MTTR looks great but the risk is the same. Watch FP rate alongside MTTR.

---

### 2. False Positive Rate

**What it measures:** What percentage of scanner findings are not real vulnerabilities?

**How to calculate:**
```
FP Rate = Findings marked False Positive in period
          ──────────────────────────────────────────
          Total findings generated in period
```

**Targets:**

| Scanner type | Target FP rate | Concern threshold |
|---|---|---|
| SAST (Semgrep) | < 15% | > 25% |
| DAST (ZAP) | < 20% | > 35% |
| SCA (Trivy/Grype) | < 10% | > 15% |
| Secrets (Gitleaks) | < 5% | > 10% |

**What high FP rate means:**
- Developers stop reading alerts ("alert fatigue") — the most dangerous security failure mode
- You are generating noise, not signal
- Rules need tuning — not suppressing, tuning (understand WHY it's FP and narrow the rule)

**What a sudden drop in FP rate might mean:**
- Improved rule tuning (good)
- Developers are no longer marking FPs — they're either ignoring alerts or not doing proper triage (bad)

---

### 3. Scanner Coverage

**What it measures:** What percentage of your attack surface is being scanned?

**Dimensions to track:**

```
Coverage matrix:
┌──────────────────────────────────────────────────────────────┐
│ Repo/service     │ SAST │ SCA │ Secrets │ IaC │ DAST │ SBOM │
├──────────────────┼──────┼─────┼─────────┼─────┼──────┼──────┤
│ pursh/frontend   │  ✓   │  ✓  │   ✓     │  —  │  ✓   │  ✓   │
│ pursh/backend    │  ✓   │  ✓  │   ✓     │  —  │  ✓   │  ✓   │
│ aisec/app        │  ✓   │  ✓  │   ✓     │  —  │  —   │  ✓   │
│ infra/terraform  │  —   │  —  │   ✓     │  ✓  │  —   │  —   │
└──────────────────┴──────┴─────┴─────────┴─────┴──────┴──────┘

Coverage score = (filled cells / total cells) × 100
```

**What good coverage looks like:**
- Every internet-facing service has SAST + SCA + Secrets + DAST
- Every IaC module has Checkov or tfsec
- No service has zero coverage in any relevant category

**The gap that kills you:** "We have 95% coverage" but the 5% is the most sensitive service.

---

### 4. Vulnerability Density

**What it measures:** Number of findings per 1,000 lines of code (KLOC).

```
Density = Total open findings
          ─────────────────────────────
          Codebase size in KLOC
```

**Why it matters:** Raw finding count is meaningless without context. A 10,000-line app with 5 findings is different from a 100,000-line app with 5 findings. Density lets you compare:
- Service A vs Service B (which has worse code quality?)
- Quarter over quarter (is the codebase getting more or less secure relative to its size?)

---

### 5. Security Debt Ratio

**What it measures:** How much of your engineering capacity is consumed by security rework vs new work.

```
Debt ratio = Story points / hours spent on security-remediation work
             ────────────────────────────────────────────────────────
             Total story points / hours in the sprint
```

**Healthy:** < 10% (security is keeping up with development pace)
**Warning:** 10–20% (security debt accumulating faster than it's being paid)
**Critical:** > 20% (program is falling behind — need dedicated remediation sprint or architectural changes)

---

### 6. Dependency Age / Patch Lag

**What it measures:** How outdated are your dependencies?

```
Track per dependency:
├── Current version in use
├── Latest available version
├── Release date of current version
├── Days since a security patch was released for your version
└── Whether the version is EOL (end of life)
```

**Red flags:**
- Any dependency > 2 major versions behind
- Any dependency with known CVE in your version, even if CVSS < 7
- Any EOL dependency in a production service

---

### 7. Time to Detect (TTD)

**What it measures:** How long did a vulnerability exist in production before you found it?

```
TTD = Date finding detected - Date vulnerable code was introduced
```

This requires correlating the finding's code location with git blame. Hard to measure but powerful.

**Why it matters:** If you're finding 6-month-old vulnerabilities, your detection pipeline has a blind spot. If you're catching everything within the same PR cycle, your shift-left is working.

---

## CISO Dashboard — one-page format

```
SECURITY POSTURE — Q1 2024
══════════════════════════════════════════════════════════════════

RISK TREND:     ↓ IMPROVING   (Critical open: 3 vs 11 last quarter)

SCANNER COVERAGE:     97%  (of services × scanner categories)
FINDINGS THIS QUARTER:
  Critical:  18 found  |  15 closed  |  3 open  |  MTTR: 4.2d ✓
  High:      47 found  |  41 closed  |  6 open  |  MTTR: 22d ✓
  Medium:   112 found  |  98 closed  | 14 open  |  MTTR: 61d ✓
  Low:       83 found  |  67 closed  | 16 open  |  MTTR: 94d ✓

FALSE POSITIVE RATE:   11%  (target: <15%) ✓
SECURITY DEBT RATIO:    8%  (target: <10%) ✓

COMPLIANCE:
  HIPAA controls covered:   82%  (↑3% this quarter)
  GDPR Art.32 covered:      79%  (stable)
  OWASP Top 10 scan coverage: 100%

INCIDENTS THIS QUARTER:
  P1:  0
  P2:  1  (leaked key, contained within 30 min, no data exposure)
  P3:  2  (scanner false alarms, no impact)

TOP 3 REMAINING RISKS:
  1. 3 Critical open: all in legacy auth module — sprint allocated for Q2
  2. IaC scanning gap: 2 Terraform modules not yet covered
  3. DAST auth coverage: 3 endpoints require custom auth scripts (in progress)

══════════════════════════════════════════════════════════════════
```

---

## Metrics traps to avoid

| Trap | What it looks like | The real picture |
|---|---|---|
| Gaming MTTR | Close tickets by marking FP en masse | FP rate spikes — reveals the gaming |
| Vanity coverage | "100% of repos scanned" | Scanning repo root with `semgrep scan .` but not the actual app directory |
| Scope creep in findings | Counting every Low from SCA | Signal is buried in noise; CISOs lose faith in the numbers |
| Point-in-time reporting | Findings snapshot on report day | Trend matters more than snapshot — always show quarter-over-quarter |
| Missing the "not scanned" surface | Reporting only on what you scan | The riskiest service might be the one not in your coverage matrix |

---

## Metrics to propose when joining a new team

If you're starting at a new company and they have no security metrics:

**Week 1:** Establish baselines (count open findings by severity, measure scanner coverage)
**Month 1:** First MTTR calculation (even if data is rough)
**Quarter 1:** First quarterly posture report with full metric set
**Quarter 2:** First quarter-over-quarter trend comparison — now you can show direction

The hardest metric to establish is the one you didn't start measuring on day 1.
