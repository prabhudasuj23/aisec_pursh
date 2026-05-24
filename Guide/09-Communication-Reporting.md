# Chapter 9: Communication & Reporting

> **Goal:** Learn how to communicate security findings clearly to different audiences — developers, managers, and executives. An AppSec engineer who finds important vulnerabilities but cannot communicate them effectively creates no value. Clear communication is what turns technical findings into business risk reduction.

---

## 9.1 Why Communication Skills Matter in AppSec

AppSec engineers communicate with three very different audiences:

| Audience | What They Care About | Communication Style |
|---|---|---|
| **Developers** | "What's broken, why is it wrong, how do I fix it?" | Technical, specific, with code examples |
| **Engineering managers** | "How much work is this? What's the priority vs other work?" | Effort, risk, business impact |
| **CISOs / Executives** | "What's our risk exposure? Are we getting better or worse?" | Business risk, trends, investment decisions |

The same vulnerability needs three different explanations. Your job is to translate security technical findings into language that each audience can act on.

---

## 9.2 Writing Vulnerability Reports for Developers

Developers need vulnerability reports to be:
- **Specific:** Exactly which file, line number, endpoint
- **Reproducible:** How to trigger the vulnerability
- **Actionable:** Exactly what to change, with code example
- **Educational:** Why this is a problem (brief, not a lecture)

### The Anatomy of a Good Vulnerability Report

**Title:** Clear, specific, not jargon-heavy

Bad: `CWE-89 SQLI Finding in Module A`  
Good: `SQL injection in user search API allows reading all user records`

**Severity:** With brief justification

```
Severity: HIGH (CVSS 8.1)
Justification: Internet-facing endpoint, no authentication required,
allows reading all user email addresses from the database.
```

**Description:** What is the vulnerability and why is it a problem?

```
The /api/users/search endpoint constructs a SQL query by concatenating the
user-supplied "email" parameter directly into the query string. An attacker
can manipulate this parameter to return records from other users or the entire
users table.

This is a SQL injection vulnerability (CWE-89, OWASP A03:2021). It allows an
unauthenticated attacker to read all user records, including email addresses,
names, and hashed passwords.
```

**Proof of Concept:** How to reproduce it

```
1. Send the following request (no authentication needed):
   GET /api/users/search?email=' OR '1'='1 HTTP/1.1
   Host: api.example.com

2. The API returns all user records in the database instead of searching
   by email address.

Evidence:
   [Attach screenshot or response snippet showing all users returned]
```

**Root Cause:** What in the code causes it

```python
# Vulnerable code in src/api/users.py, line 87:
query = f"SELECT id, email, name FROM users WHERE email LIKE '%{email}%'"
result = db.execute(query)
```

**Remediation:** The exact fix

```python
# Fix: use a parameterized query
query = "SELECT id, email, name FROM users WHERE email LIKE %s"
result = db.execute(query, (f"%{email}%",))

# Or with SQLAlchemy ORM:
users = db.query(User).filter(User.email.contains(email)).all()
```

**Verification:** How to confirm the fix works

```
After applying the fix:
1. Repeat the test with: email=' OR '1'='1
2. Should return 0 results (no users match this email string)
3. Re-run Semgrep — the python-sqli rule should no longer flag line 87
4. The automated regression test in tests/test_api.py::test_search_sqli
   should pass (add this test if it does not exist)
```

**References:**
- OWASP A03:2021 Injection
- CWE-89: Improper Neutralization of Special Elements used in an SQL Command
- Internal: [Secure Coding: SQL Injection Tutorial](../docs/secure-coding/sql-injection.md)

---

## 9.3 Writing for Engineering Managers

Engineering managers need to make prioritization decisions. They need to know:
- **What is broken and how serious is it**
- **What the business impact is if left unfixed**
- **How much work the fix requires**
- **What the risk is if they defer it**

### The Manager Briefing Format

```
Subject: Security Finding — SQL Injection in User Search API [Action Required by 2024-03-22]

Summary: A vulnerability in the user search API allows unauthorized access to
all user records. This is a P1 (Critical/High) finding requiring a fix within
7 days per our security SLA.

Risk: If exploited, an attacker could read email addresses, names, and hashed
passwords for all 50,000 registered users. This would trigger our breach
notification obligations under GDPR and state data protection laws.

Fix: 2-line code change in src/api/users.py (switching from string concatenation
to parameterized query). Engineering estimate: 1–2 hours including testing and PR
review.

SLA Deadline: 2024-03-22 (7 days from discovery, per High-severity SLA)

Status: Assigned to [Developer Name]. AppSec to review the fix.

Please confirm this is assigned and on track. If you need an SLA extension,
contact the AppSec team at [email].
```

**Key elements:**
- **Action and deadline in the subject line** — managers get 100 emails/day
- **Business risk in plain English** (50,000 users' data, GDPR obligations)
- **Effort estimate** (2-line code change = 1–2 hours) — so they can prioritize
- **Clear next step** (who is responsible, deadline, escalation path)

---

## 9.4 Executive and CISO Reporting

CISOs and executives need to understand security posture at a program level. They do not want individual vulnerability details — they want trends, risks, and investment information.

### The Monthly Security Posture Report

**Structure:**

```
1. Executive Summary (1 paragraph — read in 30 seconds)
2. Key Metrics (5–6 numbers with trend arrows)
3. Top Risks This Period (3–5 issues, business-language)
4. What We Fixed (brief wins — important for morale and showing progress)
5. Upcoming Work (what you plan to do next month)
6. Asks (if you need anything: budget, headcount, policy decisions)
```

**Executive Summary Example:**
```
Security posture improved in March. Total open High/Critical findings dropped
from 23 to 14 (39% reduction). The SQL injection vulnerability in the user
search API was found and fixed in 3 days, well within our 7-day SLA. We
completed the annual penetration test; results show improvement from last year
— 12 findings vs 21 last year. One area requiring attention: our Kubernetes
cluster configuration has 3 unresolved CIS benchmark gaps that need platform
team capacity to address.
```

**Key Metrics Dashboard:**

| Metric | This Month | Last Month | Trend |
|---|---|---|---|
| Open Critical findings | 2 | 5 | ↓ Improving |
| Open High findings | 12 | 18 | ↓ Improving |
| Mean Time to Fix — Critical | 18 hours | 24 hours | ↓ Improving |
| Mean Time to Fix — High | 5.2 days | 8.1 days | ↓ Improving |
| SLA compliance rate | 91% | 84% | ↑ Improving |
| Code coverage by SAST | 96% of repos | 89% of repos | ↑ Improving |

**Top Risks Example:**
```
Risk 1: Kubernetes cluster (HIGH)
Three CIS benchmark configuration gaps allow privilege escalation within
the cluster if an application container is compromised. Fix requires 
Platform Engineering capacity (estimated 2 sprint days). 
Interim mitigation: network policies added to limit blast radius.
Owner: Platform Engineering; Target fix: Q2 sprint 3

Risk 2: Third-party dependency (MEDIUM)
Express.js version used by 5 internal services has a known DoS vulnerability.
Patches available; engineering is upgrading. SLA: 30 days.
Status: 3 of 5 services already updated.
```

### What CISOs Actually Ask About

Based on real enterprise CISO concerns:

- **"Are we getting better or worse?"** → Trend charts over time (not point-in-time snapshots)
- **"What keeps you up at night?"** → Top 2–3 risks in plain English
- **"Are we meeting our obligations?"** → SLA compliance rate; audit readiness
- **"Where do we need to invest?"** → Tool gaps, headcount needs, training gaps
- **"What would an attacker get if they broke in right now?"** → Crown jewels mapping to current exposures

---

## 9.5 Developer Guidance and Training

One of the highest-leverage activities an AppSec engineer can do is teach developers to write secure code themselves. If 50 developers write secure code by default, you have multiplied your impact 50x.

### Principles of Effective Developer Security Training

**1. Use real examples from your codebase**
Developers tune out generic OWASP slide presentations. They pay attention when you show them a real vulnerability in a codebase they work on every day.

"Here is a SQL injection we found last week in the orders API. Here is exactly what the attacker could do with it. Here is the two-line fix. Here is why the fix works."

**2. Connect to consequences developers care about**
Developers care about:
- "Will this page me at 3am?" → "Yes, if this SQL injection causes a data breach and we get regulated, someone is writing a post-mortem"
- "Will this delay the release?" → "Yes, if we find this in a pen test 2 days before launch"
- "Will I get blamed?" → "The finding goes to you, the team lead, and your manager"

**3. Make it fast and actionable**
A 30-minute lunch-and-learn beats a 2-day mandatory security training that developers sleep through. Focus on the three vulnerabilities most common in your codebase.

**4. PR-level education**
When SAST flags a finding on a PR, the comment should link to a training resource:
```
🚨 SQL Injection Risk (Semgrep: python-sqli)
Line 87: User input is concatenated into a SQL query.

This allows SQL injection attacks. Fix: use parameterized queries.
📖 Learn more: [SQL Injection — Secure Coding Guide](../docs/secure-coding/sql-injection.md)
```

The developer learns at the moment they are writing the vulnerable code — not 6 months later in a training session.

### Secure Coding Tutorial Template

Each tutorial should include:

1. **What the weakness is** (one paragraph, plain English)
2. **Why it matters** (real-world impact, example breach)
3. **Vulnerable code example** (realistic, from your stack)
4. **Secure code example** (same scenario, fixed)
5. **How to test** (how to verify your code is safe)
6. **How the scanner detects it** (so developers understand what Semgrep is telling them)

---

## 9.6 Cross-Team Collaboration

AppSec engineers work with many teams. Being effective requires understanding each team's priorities and presenting security in those terms.

### Working with Product Teams

Product managers care about: features, customer value, and release timelines.

**Don't say:** "You can't launch this feature, there's a security vulnerability."

**Do say:** "We found a vulnerability that could expose customer data. We have a 2-day fix. Let's add it to this sprint so we can launch on schedule and safely."

Product managers want solutions, not blockers. Come with the fix, not just the problem.

### Working with DevOps/Platform Teams

Platform engineers care about: reliability, performance, and automation.

AppSec and platform engineers are natural allies — both care about automation, repeatability, and not having humans do things manually. Frame security as infrastructure improvements:

- "Can we add Trivy to the container build pipeline? It runs in 30 seconds and gates on Critical CVEs."
- "Can we configure the ECS task role to only have the permissions this service needs?"

### Managing Trade-offs

Sometimes developers or product managers push back on security requirements:
- "This authentication check adds 50ms of latency"
- "We don't have time to fix this before launch"
- "This is an internal-only service, no one can reach it"

**The AppSec approach:**
1. **Understand their concern** — is it legitimate? 50ms latency matters for high-traffic APIs.
2. **Quantify the risk** — "This endpoint is accessible from the internet and handles payment data. If exploited, this is a reportable breach under PCI-DSS."
3. **Find a middle ground** — can you add a WAF rule as interim mitigation while the fix is developed?
4. **Make the risk acceptance explicit** — if they choose not to fix it, document it as a formal risk acceptance with their name, the reason, and a review date.

**Never silently accept risk.** If someone overrides your security recommendation, document it formally. This protects you and ensures the decision is made with full information.

### When to Escalate

Escalate to CISO or security leadership when:
- A critical vulnerability is not being fixed within SLA with no valid reason
- A risk acceptance is being made for business reasons without proper authority
- You discover evidence of an ongoing attack or data breach
- Legal or compliance exposure is at stake (breach that may require notification)

---

## 9.7 Real-World Case Study: Twitch Data Breach Communication (2021)

**What happened:** In October 2021, an anonymous poster published 125GB of Twitch's source code, internal tools, and revenue data on 4chan. This included Twitch's entire codebase, unreleased games, and the payout information for top streamers.

**Twitch's initial response (what went wrong):**

Twitch's first public statement was:
> "We can confirm a breach has taken place. Our teams are working with urgency to understand the extent of this."

This was accurate but vague. It said nothing about:
- What data was exposed
- Whether streamers or users should take action
- Whether passwords were compromised
- A timeline for updates

**Better crisis communication principles:**

1. **Acknowledge quickly** — even if you don't have all the facts, acknowledge something happened and that you're investigating (Twitch did this, but slowly)

2. **Tell people what actions to take** — "We recommend all users change their passwords and enable 2FA immediately" — this gives people something to do and shows you care about their safety

3. **Be specific about what was and was not exposed** — "Source code was exposed. We have no evidence that user passwords, payment information, or login credentials were accessed"

4. **Set a communication timeline** — "We will provide an update within 24 hours as we understand more"

5. **Internal communication first** — employees and teams should hear from leadership before reading it on Twitter. Twitch employees reportedly learned about the breach from news articles.

**What AppSec engineers should document to enable good breach communication:**
- **Data classification map:** What type of data is in each system? If system X is breached, what data is exposed?
- **Crown jewels inventory:** Which systems contain the most sensitive data?
- **Breach notification requirements:** What laws apply? (GDPR: 72 hours; CCPA; state laws)
- **Communication templates:** Pre-written notification templates (fill in the specifics) so you are not writing from scratch in a crisis

---

## Chapter 9 Summary

| Audience | What They Need | Format |
|---|---|---|
| Developers | Exact location, root cause, code fix, verification steps | Detailed technical report with code examples |
| Engineering managers | Business risk, effort estimate, deadline, who owns it | Brief email with action item + deadline in subject |
| CISOs/Executives | Trends, top risks, SLA compliance, investment asks | Monthly dashboard + 1-page briefing |

| Skill | Key Takeaway |
|---|---|
| Vulnerability reports | Title + severity + PoC + code fix + verification = developers can act immediately |
| Executive reporting | Trend over time; business language; specific asks |
| Developer training | Real codebase examples; PR-level education; fast and actionable |
| Cross-team collab | Come with solutions not blockers; make risk acceptance explicit and documented |
| Breach communication | Data classification map + notification templates ready before you need them |

---

*Next: [Chapter 10 — Hands-On Labs & Projects](10-Hands-On-Labs.md)*
