# Triage Decision Trees — AppSec Analyst

> Flowcharts for the decisions you make on every finding. Use these to build consistent, defensible triage habits.

---

## 1. Primary Triage Decision Tree

Every finding goes through this tree first.

```
New finding arrives from scanner
            │
            ▼
    ┌───────────────────────┐
    │ Is it exploitable?    │
    │ (Can an attacker reach │
    │  the vulnerable code?) │
    └───────────┬───────────┘
                │
        ┌───────┴───────┐
        │               │
       YES              NO
        │               │
        ▼               ▼
  ┌──────────┐    ┌──────────────────────────────┐
  │Confirmed │    │ WHY is it not exploitable?    │
  │ finding  │    ├──────────────────────────────┤
  └────┬─────┘    │ A. No external entry point   │
       │          │    (dead code, internal only) │
       │          │ B. Framework handles it       │
       │          │    (ORM, template escaping)   │
       │          │ C. Finding is in test code     │
       │          │    (not deployed)             │
       │          │ D. Compensating control exists │
       │          │    (WAF, auth gate before it)  │
       │          └─────────────┬────────────────┘
       │                        │
       │              ┌─────────┴──────────┐
       │              │                    │
       │         Can you PROVE it?    Cannot prove it
       │              │                    │
       │              ▼                    ▼
       │         Mark FP with        Accept risk:
       │         evidence doc        document + expiry date
       │
       ▼
  Assign severity
  (CVSS + business context)
       │
       ├── CRITICAL → block merge, notify lead, P1 SLA (7 days)
       ├── HIGH     → block merge, create ticket, 30-day SLA
       ├── MEDIUM   → create ticket, 90-day SLA, no block
       └── LOW      → create ticket, 180-day SLA, no block
```

---

## 2. False Positive Decision Tree

Developers will frequently claim FP. Never accept a verbal claim — make them prove it.

```
Developer claims: "This is a false positive"
            │
            ▼
    Ask: "Show me why."
            │
    ┌───────┴────────────────────────────┐
    │                                    │
"Here's the code path               "Trust me, we never
 that shows no external              call it from user input"
 entry point / sanitization"                │
    │                                       │
    ▼                                       ▼
Review the evidence:             Not acceptable — need evidence
    │                                       │
    ├─ Is the sanitization in a       Ask:  │
    │  recognized location?           "Show me the call graph"
    │  (stdlib, ORM, tested util)           │
    │                                       ├─ They can show it → see left branch
    ├─ Is the dead code truly         │    │
    │  unreachable? (check call graph)│    └─ They can't → finding stays open
    │                                 │
    └─ Is the framework escape        │
       documented to cover this sink? │
            │                         │
           YES                        NO
            │                         │
            ▼                         ▼
    Mark FP:                  Finding is NOT a FP
    - Document the reason     Confirm severity
    - Add inline suppression  Create/keep ticket open
    - Log in FP tracker
    
    NOTE: Global rule suppression is almost never justified.
    Suppress at the specific line/file level with a comment.
```

---

## 3. Severity Escalation Decision Tree

CVSS gives you a baseline. Business context adjusts it.

```
CVSS score: [X.X]
            │
            ▼
Base severity from CVSS:
  9.0–10.0 → Critical
  7.0–8.9  → High
  4.0–6.9  → Medium
  0.1–3.9  → Low
            │
            ▼
Apply business context modifiers:
            │
    ┌───────┴──────────────────────────────────────┐
    │ Escalate severity if:                        │
    │  ✓ PHI/PII directly exposed                  │  +1 severity
    │  ✓ Internet-facing endpoint (not internal)   │  +1 severity
    │  ✓ In CISA KEV (actively exploited in wild)  │  → force to Critical
    │  ✓ No compensating controls (no WAF, no auth)│  +1 severity
    │  ✓ HIPAA/GDPR compliance scope               │  +1 severity
    └───────┬──────────────────────────────────────┘
            │
    ┌───────┴──────────────────────────────────────┐
    │ De-escalate severity if:                     │
    │  ✓ Internal-only, no external network access │  -1 severity
    │  ✓ Requires physical access to exploit       │  -1 severity
    │  ✓ Compensating control blocks the attack    │  -1 severity (not to Info)
    │  ✓ Proof-of-concept requires other vulns     │  -1 severity
    └──────────────────────────────────────────────┘
            │
            ▼
    Final severity → SLA clock starts
```

### Escalation examples

| CVSS | Context | Final severity |
|---|---|---|
| 7.5 High | Internal tool, 3 users, no PHI | Medium |
| 5.0 Medium | File upload serving patient lab PDFs, internet-facing | High |
| 4.3 Medium | In CISA KEV with active exploitation | Critical |
| 9.8 Critical | Dead code, no call path from any API | Medium (with expiry doc) |

---

## 4. Accepted Risk Decision Tree

Not everything can be fixed immediately. The accepted-risk process is how you document risk you're knowingly carrying.

```
Finding cannot be fixed in SLA
            │
            ▼
Can we implement a compensating control?
            │
    ┌───────┴────────────────┐
    │                        │
   YES                       NO
    │                        │
    ▼                        ▼
Implement compensating   Escalate to manager
control AND document:    for accepted-risk sign-off
  - What the control is      │
  - Why it's sufficient       │
  - Expiry date for review    ▼
                         Manager/CISO signs off on:
                           - Risk description
                           - Business justification
                           - Accepted expiry date (max 90 days for High)
                           - Owner responsible for monitoring
                           │
                           ▼
                    Document in ticket + risk register
                           │
                           ▼
                    Calendar reminder at expiry:
                    Re-evaluate — still accepted? Fixed? Escalate?
```

**Accepted risk is NOT:**
- A way to make a finding disappear
- Appropriate for Critical findings without CISO sign-off
- Permanent — all accepted risks need expiry dates

---

## 5. Dependency CVE Triage Tree (SCA)

SCA scanners generate a lot of noise. Not every CVE in a transitive dependency is actionable.

```
CVE found in dependency [package@version]
            │
            ▼
Is this a direct or transitive dependency?
            │
    ┌───────┴──────────┐
    │                  │
  Direct            Transitive
    │                  │
    │               Is the vulnerable function
    │               called by our code (even indirectly)?
    │                  │
    │          ┌───────┴────────┐
    │          │                │
    │        YES                NO
    │          │                │
    │          │         Mark as "not reachable"
    │          │         Document reasoning
    │          │         Set 90-day re-evaluation
    │          │
    ▼          ▼
Is a patched version available?
            │
    ┌───────┴──────────┐
    │                  │
   YES                 NO
    │                  │
    ▼                  ▼
How breaking        Is there a workaround?
is the upgrade?     (config, feature flag, alternate lib)
    │                  │
    ├── Non-breaking    ├── YES → implement + document
    │   (patch/minor)  └── NO  → accepted risk (escalate if Critical)
    │   → upgrade in next PR
    │
    ├── Breaking (major version)
    │   → evaluate in sprint planning
    │   → document the risk being carried in interim
    │
    └── EOL package (no patches will come)
        → plan replacement (add to tech debt backlog)
        → set 30-day hard deadline if Critical CVE in EOL package
```

---

## 6. Incident Escalation Decision Tree

When does a finding become an incident?

```
Finding discovered
            │
            ▼
Is there evidence of active exploitation?
(CloudTrail anomalies, IDS alerts, SIEM hits, 
 report from user, anomalous logs)
            │
    ┌───────┴──────────┐
    │                  │
   YES                 NO
    │                  │
    ▼                  ▼
INCIDENT             Continue normal
DECLARE NOW          triage process
    │
    ▼
Severity of incident?
    │
    ├── Data exfiltration confirmed or suspected
    │   → P1: CISO + Legal + Security lead (NOW)
    │
    ├── System compromise suspected
    │   (unusual API calls, lateral movement indicators)
    │   → P1: Security lead + Infra team (NOW)
    │
    ├── Credentials leaked, no confirmed exploitation
    │   → P2: Manager + Owner (within 1 hour)
    │
    └── Misconfiguration found, no exploitation evidence
        → P3: Normal triage, expedited SLA
```

---

## Quick Reference: Triage Status Codes

| Status | Meaning | Who can close | Documentation required |
|---|---|---|---|
| `open` | Triaged, real finding, awaiting fix | Developer + analyst verification | — |
| `in_progress` | Fix in development | Developer | PR link |
| `fixed` | Fix merged and verified | Analyst (after re-scan) | Closure note + re-scan evidence |
| `false_positive` | Not a real vulnerability | Analyst | Why it's FP, suppression justification |
| `accepted_risk` | Real finding, won't fix | Manager sign-off required | Risk justification + expiry date |
| `wont_fix` | Out of scope, duplicate, or third-party owned | Analyst | Reason + owner (if third-party) |

**Never close a finding as `fixed` without running the scanner again and confirming the finding no longer appears in the same location.**
