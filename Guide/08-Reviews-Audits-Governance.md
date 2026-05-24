# Chapter 8: Security Reviews, Audits & Governance

> **Goal:** Learn how to conduct structured application security reviews, support compliance audits, and connect technical security work to governance frameworks like SOC 2, ISO 27001, NIST CSF, and PCI-DSS. This is where AppSec engineers move from individual contributor to program-level work.

---

## 8.1 What Is a Security Review?

A security review is a structured evaluation of a system, change, or feature to identify security risks before they reach production. It is not a penetration test — it is a design and architecture-level assessment.

### When to Conduct Security Reviews

| Trigger | Type of Review |
|---|---|
| New product or major feature | Full architecture review |
| New third-party integration | Integration security review |
| Change to authentication or authorization | Auth review |
| New data type (PHI, PCI, PII) being stored | Data classification review |
| Change to cryptography | Crypto review |
| New cloud infrastructure | Infrastructure review |
| Pre-launch for high-risk apps | Comprehensive pre-launch review |

### Types of Security Reviews

**1. Architecture Review**
Review system design before code is written. Focus on trust boundaries, data flows, privilege levels, and attack surfaces.

**2. Code Review (Security-Focused)**
Review source code changes for security vulnerabilities. Can be part of normal PR review or a dedicated security review for high-risk code.

**3. Design Review**
Review feature or API design documents for security implications. Catch insecure-by-design problems before implementation.

**4. Pre-Launch Review**
Before launching a new service to production, verify all security controls are in place. Checklist-driven.

---

## 8.2 How to Conduct an Application Security Review

### Step 1: Gather Context

Before reviewing code or architecture, understand:

- **What does this system do?** What business problem does it solve?
- **Who uses it?** Internal employees? External customers? Partners?
- **What data does it handle?** PII? PHI? Payment data? IP?
- **What systems does it integrate with?** Third-party APIs? Databases? Message queues?
- **What is the threat model?** Who would want to attack this, and why?

**Questions to ask the development team:**
- "Walk me through what happens when a user logs in"
- "Where is sensitive data stored, and how is it protected?"
- "What happens if this service is down?"
- "What permissions does this service's service account have?"

### Step 2: Draw the Data Flow

Create or request a data flow diagram (DFD):

```
[User Browser]
  │ HTTPS
  ▼
[API Gateway] → [Auth Service] (token validation)
  │ Internal HTTP
  ▼
[Application API]
  │              │
  ▼              ▼
[Postgres DB] [S3 bucket] (encrypted at rest)
  │
  ▼
[Audit Log Table]
```

Mark:
- Trust boundaries (internet → internal, user → admin)
- Where sensitive data flows
- Authentication/authorization check points
- Encryption at rest and in transit

### Step 3: Apply a Security Review Framework

Use a structured checklist so nothing is missed:

**Authentication and Authorization:**
- Is authentication required for all sensitive endpoints?
- Is authorization checked server-side for every resource access?
- Are admin functions separated from user functions?
- Is MFA required for privileged operations?

**Data Protection:**
- What sensitive data does this feature handle?
- Is it encrypted at rest? In transit?
- Is sensitive data logged anywhere?
- Is there data minimization? (Do not collect what you do not need)

**Input and Output:**
- Is all user input validated?
- Are all database queries parameterized?
- Is output encoded before rendering?
- Are file uploads validated (type, size, content)?

**Error Handling:**
- Do error responses reveal internal details?
- Does the app fail securely (closed, not open) on errors?

**Cryptography:**
- What cryptographic algorithms and key lengths are used?
- Are they current (AES-256, RSA-2048, SHA-256)?
- Where are keys stored?

**Logging and Monitoring:**
- Are authentication events logged?
- Are authorization failures logged?
- Are sensitive operations (data export, admin actions) logged?
- Are logs stored where they cannot be tampered with by the app?

**Third-party Integrations:**
- Are third-party APIs called securely (TLS, certificate validation)?
- Is the minimum required data sent to third parties?
- Are third-party credentials stored securely (secrets manager, not hardcode)?

### Step 4: Document Findings

Security review findings should be documented in a consistent format:

```markdown
## Security Review: Order Management API v2.0
Reviewer: Jane Smith (AppSec Team)
Date: 2024-03-15
Risk Level: HIGH

### Findings

#### Finding 1: IDOR in Order Status API
Severity: High
Description: GET /api/orders/{id}/status does not verify that the authenticated
user owns the order. Any authenticated user can view any order's status by
guessing the order ID.
Impact: Confidentiality breach — order details (products, addresses) exposed
Affected: All authenticated users; 50,000+ orders in system
Recommendation: Add authorization check:
  `filter(Order.id == order_id, Order.user_id == current_user.id)`
References: OWASP API1:2023 Broken Object Level Authorization

#### Finding 2: Verbose Error Messages
Severity: Low
Description: The API returns stack traces in 500 error responses in all environments.
Impact: Information disclosure — reveals internal file paths, class names, library versions
Recommendation: Return generic error messages in production; log full details internally.

### Positive Observations
- All inter-service communication uses mTLS ✅
- Database queries use SQLAlchemy ORM correctly (parameterized) ✅
- Secrets loaded from AWS Secrets Manager ✅
- Rate limiting in place on auth endpoints ✅
```

---

## 8.3 Supporting Compliance Audits

Compliance audits are formal assessments of whether an organization meets the requirements of a standard (SOC 2, PCI-DSS, ISO 27001, HIPAA). AppSec engineers provide evidence and explain security controls.

### How Audits Work

**1. Scoping:** The auditor defines what is in scope — which systems, data types, and processes will be evaluated.

**2. Evidence collection:** The auditor requests evidence that controls exist and work. AppSec engineers provide:
- Security policies and standards documents
- Scanner reports showing vulnerabilities are being found and fixed
- SLA metrics (time-to-fix by severity)
- Code review records
- Penetration test reports
- Training completion records
- Change management records

**3. Testing:** The auditor may test controls directly:
- Attempt to access resources without authorization
- Review configuration of security tools
- Interview engineers about their processes

**4. Findings and report:** The auditor documents findings (gaps) and issues a report.

**5. Remediation:** Organization addresses gaps; some audits include a follow-up assessment.

### Evidence an AppSec Engineer Provides

| Auditor Request | AppSec Evidence |
|---|---|
| "Show me your vulnerability management process" | SLA policy document + Jira/tracking reports showing findings → fixed within SLA |
| "Show me your SDLC security controls" | Pipeline configuration showing SAST/SCA/DAST; PR requirement policy |
| "Show me a vulnerability that was found and fixed" | Specific finding: scanner output → ticket → commit → re-scan showing resolved |
| "Show me your penetration testing" | Pen test report + remediation tracking |
| "Show me developer security training" | Training platform completion records |
| "Show me your access control reviews" | IAM review records; quarterly access reviews |

---

## 8.4 Key Compliance Frameworks

### SOC 2 (Service Organization Control 2)

**What it is:** An audit framework for service organizations (SaaS companies, cloud services) that defines trust service criteria.

**Five Trust Service Criteria:**
- **Security** (CC) — system is protected against unauthorized access
- **Availability** (A) — system is available for operation as agreed
- **Processing Integrity** (PI) — processing is complete, valid, accurate, timely, authorized
- **Confidentiality** (C) — information designated as confidential is protected
- **Privacy** (P) — personal information is collected, used, retained, disclosed per privacy notice

Most SaaS companies pursue **SOC 2 Type II** (audits actual operation over 6–12 months) for the Security criteria at minimum.

**What AppSec engineers do for SOC 2:**
- Maintain vulnerability management process and metrics
- Ensure code review is documented in every PR
- Maintain SDLC security documentation
- Operate incident response process
- Conduct annual penetration test
- Maintain access control and least privilege

### ISO 27001

**What it is:** International standard for information security management systems (ISMS). Certifiable by accredited bodies.

**Key controls relevant to AppSec (Annex A):**
- A.8 — Asset Management (know what you have)
- A.9 — Access Control (least privilege, MFA)
- A.10 — Cryptography (approved algorithms, key management)
- A.12 — Operations Security (vulnerability management, malware protection, logging)
- A.14 — System Acquisition, Development, and Maintenance (secure SDLC)
- A.16 — Information Security Incident Management (incident response)

**ISO vs SOC 2:** ISO 27001 is a standard (defines what controls to have); SOC 2 is an audit (attests that controls work). Many enterprises pursue both.

### NIST Cybersecurity Framework (CSF)

**What it is:** A voluntary framework from the US National Institute of Standards and Technology. Five core functions:

| Function | What It Means | AppSec Examples |
|---|---|---|
| **Identify** | Know your assets and risks | Asset inventory, threat modeling, vulnerability scanning |
| **Protect** | Implement safeguards | SAST/DAST/SCA, secure coding standards, MFA, encryption |
| **Detect** | Identify security events | SIEM, GuardDuty, DAST monitoring, log analysis |
| **Respond** | Take action on detected events | Incident response plan, runbooks, containment procedures |
| **Recover** | Restore capabilities | Business continuity, backup/restore, lessons learned |

NIST CSF is widely used in US government and enterprise. When an auditor or customer asks "What framework do you align to?", NIST CSF is a common answer.

**NIST CSF 2.0 (2024)** added a sixth function:
- **Govern** — Organizational context, risk strategy, supply chain risk management

### PCI-DSS (Payment Card Industry Data Security Standard)

**What it is:** Required if you store, process, or transmit payment card data (credit/debit card numbers). Enforced by card brands (Visa, Mastercard). Non-compliance results in fines and loss of ability to process cards.

**12 PCI-DSS Requirements:**

| Requirement | Summary |
|---|---|
| 1 | Install and maintain network security controls (firewalls) |
| 2 | Apply secure configurations to all system components |
| 3 | Protect stored account data (encryption, tokenization) |
| 4 | Protect cardholder data in transit (TLS) |
| 5 | Protect against malicious software (antimalware) |
| 6 | Develop and maintain secure systems and software |
| 7 | Restrict access to system components by business need |
| 8 | Identify users and authenticate access (MFA) |
| 9 | Restrict physical access to cardholder data |
| 10 | Log and monitor all access to system components |
| 11 | Test security of systems and networks regularly (pen test, scanning) |
| 12 | Support information security with organizational policies |

**PCI-DSS v4.0 (2024) changes relevant to AppSec:**
- Requirement 6.2: Web application and API scanning on every new version
- Requirement 6.3: DAST against internet-facing web applications
- Requirement 11.3: Internal and external penetration testing annually; after significant changes
- Requirement 12.3.1: Formal risk assessment for all technology and security decisions

### HIPAA Security Rule (Healthcare)

**What it is:** Required for healthcare organizations and their business associates who handle Protected Health Information (PHI).

**Three safeguard categories:**
- **Administrative safeguards:** Security officer, workforce training, risk assessment, incident response
- **Physical safeguards:** Facility access controls, workstation security, device controls
- **Technical safeguards:** Access control, audit controls, integrity controls, transmission security

**Key HIPAA AppSec controls:**
- Unique user identification (§164.312(a)(2)(i)) — no shared accounts
- Automatic logoff (§164.312(a)(2)(iii)) — session timeout
- Encryption (§164.312(a)(2)(iv) and §164.312(e)(1)) — at rest and in transit
- Audit controls (§164.312(b)) — log all PHI access
- Person authentication (§164.312(d)) — MFA

---

## 8.5 Policy and Standards Development

AppSec engineers write policies and standards that guide the organization's security practices.

### Policy vs. Standard vs. Guideline vs. Procedure

| Document | Mandatory? | Level of Detail | Example |
|---|---|---|---|
| **Policy** | Yes | High-level (what must be done) | "All production systems must use MFA" |
| **Standard** | Yes | Specific requirements (how to meet policy) | "MFA must use TOTP (not SMS) for privileged accounts" |
| **Guideline** | No | Recommendations (how to meet standard) | "Consider using YubiKey for admin accounts" |
| **Procedure** | Yes | Step-by-step instructions | "How to enroll in TOTP MFA: 1. Go to account settings..." |

### Example: Secure Development Policy

```markdown
# Secure Development Policy
Version: 2.1 | Last Updated: 2024-01-15 | Owner: AppSec Team

## Purpose
This policy establishes requirements for secure software development to protect
company systems and customer data from security vulnerabilities.

## Scope
All software developed, modified, or maintained by [Company] engineers.

## Requirements

### 1. Threat Modeling
All new services and significant features must undergo threat modeling prior
to implementation. The threat model must be reviewed by the AppSec team.

### 2. Security Testing
1.1 SAST tools must be integrated into all code repositories and run on every
    pull request. Critical and High findings must be resolved before merging.
1.2 SCA tools must scan all dependencies. Critical CVEs must be resolved
    within 24 hours; High CVEs within 7 days.
1.3 DAST scans must run against staging environments prior to production release.

### 3. Secret Management
3.1 Credentials, API keys, and passwords must not be stored in source code or
    configuration files committed to version control.
3.2 All secrets must be stored in [Company]-approved secrets management systems.

### 4. Code Review
4.1 All code changes require at least one peer review before merging to main.
4.2 Changes to authentication, authorization, or cryptography require review
    from the AppSec team.

## Exceptions
Exceptions must be approved by the CISO and documented with business justification.

## Enforcement
Violations may result in corrective action up to and including termination.
```

---

## 8.6 Real-World Case Study: Uber Data Breach Cover-Up (2022)

**What happened:** In 2016, hackers stole data on 57 million Uber users and drivers. Uber's security team discovered the breach. Instead of reporting it (as required by law), then-CSO Joe Sullivan paid the hackers $100,000 disguised as a "bug bounty" payment and required them to sign NDAs. The breach was hidden for a year. In 2022, Sullivan was convicted of obstruction of justice and concealment of a felony — the first criminal conviction of a corporate security officer for breach cover-up.

**What went wrong — technical:**
- Uber engineers committed AWS access keys to a private GitHub repository
- Attackers found the keys (they scanned GitHub for AWS key patterns — a common attack)
- Keys had excessive permissions (not least privilege)
- The keys enabled access to an S3 bucket containing a database backup with the 57 million records

**What went wrong — governance:**
- No mandatory breach notification process
- CSO made the payment decision alone, without legal and compliance review
- Cover-up violated multiple breach notification laws (GDPR Art. 33 requires notification within 72 hours)

**Lessons for AppSec governance:**
1. **Breach notification policy must be mandatory and documented** — any confirmed breach triggers an automatic process involving legal, compliance, and leadership. Not a CSO judgment call.
2. **Secrets scanning must block commits** — the AWS keys should never have reached GitHub.
3. **Incident response must have legal involvement from the start** — security engineers make technical decisions; lawyers make legal decisions.
4. **Least privilege** — the exposed keys should not have accessed S3 production backup data.

---

## Chapter 8 Summary

| Topic | Key Takeaway |
|---|---|
| Security reviews | Structured, documented, triggered by specific events; cover auth, data, input, crypto, logging |
| Audit support | Provide evidence chains: finding → ticket → fix → verify → close |
| SOC 2 | Trust service criteria; Type II audits actual operations over time |
| ISO 27001 | International ISMS standard; certifiable; 14 control domains |
| NIST CSF | Five functions: Identify, Protect, Detect, Respond, Recover |
| PCI-DSS | 12 requirements for card data; pen test and scanning mandated |
| HIPAA | PHI protection: access control, audit logs, encryption, MFA |
| Policy writing | Policy (what) → Standard (how) → Guideline (recommendation) → Procedure (steps) |
| Uber lesson | Governance failures can result in criminal charges; breach notification must be mandatory |

---

*Next: [Chapter 9 — Communication & Reporting](09-Communication-Reporting.md)*
