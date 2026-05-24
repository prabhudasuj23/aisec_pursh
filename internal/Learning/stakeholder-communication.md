# Stakeholder Communication — AppSec Analyst

> How to communicate the same technical finding to a developer, manager, and CISO/client. Internal reference — real scripts, not theory.

---

## The core problem

You will know things that are technically true but:
- A developer doesn't understand why they should prioritize it over a feature
- A manager doesn't understand what risk they're accepting if they don't fix it
- A CISO doesn't want to know how it works — they want to know what to tell the board

**One finding, three audiences, three completely different conversations.**

---

## Scenario 1: Critical SQL Injection in Patient Search

**Technical reality:**  
Semgrep found a SQL injection sink in `pursh/backend/api/patients.py:47`. User-controlled `search_term` is string-concatenated into a raw SQL query. CVSS 9.8. Affects the patient search endpoint accessible to all authenticated doctors.

---

### To the developer

```
Hey [name] — Semgrep flagged a SQL injection in the patient search endpoint (patients.py:47).

The current code does:
    query = f"SELECT * FROM patients WHERE name = '{search_term}'"

An attacker who is a logged-in doctor can submit:
    search_term = "' OR '1'='1" 
and get back every patient in the database, not just their own.

Or they can do:
    search_term = "'; DROP TABLE patients; --"
and that's obvious.

Fix: use SQLAlchemy ORM or parameterized query:
    patients = Patient.objects.filter(name=search_term)
    # or raw with params:
    cursor.execute("SELECT * FROM patients WHERE name = %s", [search_term])

The %s placeholder is handled by the DB driver — it escapes automatically.

This is a P1 — needs to be in the next PR. Let me know if you want to pair on the fix.
```

**Key techniques:**
- Specific file + line number — not vague
- Show the exact exploit — not just "it's dangerous"
- Show the exact fix — not just "sanitize your input"
- Offer to pair — reduce friction on the fix path

---

### To the manager / team lead

```
We found a critical security issue in the patient search feature. A logged-in user 
(e.g., a doctor) could potentially access or delete records they shouldn't be able to see.

This is a known vulnerability class (SQL injection — ranked #3 on OWASP's top 10 web app 
risks). The fix is a one-line code change that [developer name] can implement in a few hours.

Our SLA for critical findings is 7 days. I've already flagged it to [developer name] and 
blocked the current search feature PR from merging until it's addressed.

No evidence the vulnerability has been exploited — it was caught in code review before 
reaching production.

Action needed from you: please confirm [developer name] has time allocated this sprint 
to address this. I can track it through our security dashboard.
```

**Key techniques:**
- No CWE numbers, no CVSS scores
- Translate to business terms: "access records they shouldn't see"
- Frame the fix as simple and fast — reduce panic
- Tell them what's already been done (blocked PR)
- One clear ask: capacity allocation

---

### To the CISO or client

```
Security Posture Update — [Date]

CRITICAL FINDING: Patient search vulnerability identified and contained.

Status: CONTAINED — finding identified in code review before production deployment.

Summary: Our automated SAST scan identified a database injection vulnerability in the 
patient search function during code review. This type of vulnerability (ranked in OWASP's 
top 3) could, if exploited in production, allow an authenticated user to access 
unauthorized patient records — a potential HIPAA §164.312(a)(1) access control violation.

The vulnerability was caught before merging to production. No patient data was at risk.

Actions taken:
  - PR blocked from merging [today, 10:30 AM]
  - Developer notified and working on fix [ETA: 48 hours]
  - No production systems affected

Compliance note: This is exactly the control that HIPAA §164.312(b) (audit controls) 
requires us to demonstrate — finding and logging issues before they reach production. 
This incident will be documented in our quarterly security review as evidence of program 
effectiveness.

No executive action required at this time. I will confirm closure within our 7-day SLA.
```

**Key techniques:**
- Lead with the status ("CONTAINED") — executives first want to know: is the crisis over?
- Connect to regulatory obligations they care about (HIPAA, GDPR)
- Frame the find as evidence the program works, not evidence of failure
- End with: no action needed from them (unless it's escalation)

---

## Scenario 2: High finding left open 45 days (SLA breach)

### To the developer (escalation message)

```
Hey [name] — following up on SEC-127 (path traversal in file upload, opened 2024-01-02).
Our SLA for High findings is 30 days. We're at day 45.

I understand you've been heads-down on the Q1 launch. Here's what I can do to help:
- I've written the exact code fix in the ticket comments already
- If the blocker is testing, I can help write the test case
- If it's deprioritized by your lead, let me know and I'll escalate with your manager

I need this closed or a documented accepted-risk justification this week.
What's blocking you?
```

### To the manager (escalation)

```
I need to flag that SEC-127 (High severity file upload vulnerability) is at 45 days open,
15 days past our SLA.

I've been in contact with [dev name] but it's consistently being deprioritized.

Options:
  1. Allocate sprint capacity to fix it this week
  2. Accept risk formally: you and [dev name] sign off on a documented accepted-risk 
     with a new deadline of [date] — I can prepare that document
  3. Escalate to you to prioritize — I'm happy to explain the risk in a 15-min call

This finding involves the patient file upload path, which touches S3-stored lab results.
Path traversal here could allow a user to read files outside their bucket prefix.

Let me know which direction you want to take.
```

---

## Scenario 3: Critical CVE in a dependency you use

**Log4Shell moment:** you've just found that a package in your tech stack has a critical 0-day with active exploitation.

### Communication sequence

**First message — to your manager (within 30 minutes of discovery):**
```
HEADS UP — Critical CVE affecting [package name], version [X.X] which we use in [service].
CVE-2024-XXXX, CVSS 9.8, active exploitation in the wild per CISA KEV.

I'm assessing our exposure now. Will update within 2 hours with:
  - Confirmed affected/not affected
  - Patch availability  
  - Recommended action

No action needed from you yet — just wanted you aware.
```

**Second message — findings (2 hours later):**
```
Exposure assessment complete for CVE-2024-XXXX:

AFFECTED: Yes — [service name] uses [package] version [X.X] (vulnerable range: < [fixed version])
EXPOSURE: [Internet-facing / Internal only / Called via user input: Yes/No]
PATCH AVAILABLE: Yes — [fixed version] released [date]
EXPLOITATION: Active in the wild (CISA KEV listed 2024-01-XX)

Recommended action: Emergency patch in next 24 hours.
I've already:
  - Opened SEC-145 with High/Critical priority
  - Tagged [dev lead] as owner
  - Confirmed the fix is a version bump in requirements.txt (low risk change)

If we cannot patch in 24h: recommend disabling [affected feature] as temporary mitigation.

Who do I need sign-off from to declare this a P1 incident and get immediate capacity?
```

---

## Reading the room: what each audience actually fears

| Audience | Their real fear | Frame your message around |
|---|---|---|
| Developer | Being blamed, blocked, or overwhelmed with tickets | "Here's the fix, I'll help you, it's not your fault the pattern exists" |
| Team lead / Manager | Sprint disruption, slipped deadlines, their team looking bad | "It's scoped, fast to fix, won't blow up the sprint" |
| CISO / VP | Breach reaching the press, regulatory fines, board questions | "Contained, no impact, evidence our controls work" |
| Compliance Auditor | Can they find a paper trail? Is there a control gap? | "Documented, timestamped, mapped to requirement X" |
| Client (external) | "Should I still trust this vendor?" | "We found it ourselves, we fixed it, here's the evidence, here's our process" |

---

## Common mistakes in stakeholder communication

| Mistake | What it looks like | What to do instead |
|---|---|---|
| Crying wolf | Every finding is "critical emergency" | Reserve urgent escalation for Critical + in-the-wild exploitation |
| Too much jargon | "CWE-22 CVSS 7.5 path traversal via symlink" to a manager | "A file path vulnerability that could let users read files they shouldn't" |
| No context | "We have 47 open findings" | "We have 47 open findings, down from 89 last quarter. 0 are overdue Critical, 3 are overdue High." |
| Ambiguous ask | "We need to address this" | "I need [developer's name] to spend [2 hours / 1 sprint] on this by [date]" |
| Explaining without recommending | Listing all the options, no opinion | Always give your recommendation. "I recommend option 2 because..." |
| Post-breach surprises | CISO finds out about a critical from a news article | Monthly posture report ensures they always know before anyone else does |
