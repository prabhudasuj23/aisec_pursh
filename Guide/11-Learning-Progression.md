# Chapter 11: Learning Progression & Career Map

> **Goal:** A clear, realistic roadmap for becoming an enterprise Application Security engineer. This chapter translates the knowledge in Chapters 1–10 into a sequenced learning plan, interview preparation strategy, and career growth path.

---

## 11.1 The Recommended Learning Order

The order matters. Each layer builds on the previous one. Starting with SAST without understanding OWASP is like debugging code without knowing what a bug looks like.

```
Phase 1 (Weeks 1–4):   OWASP Top 10 + Secure Coding Fundamentals
Phase 2 (Weeks 5–8):   Git/SCM Security + SAST Setup
Phase 3 (Weeks 9–12):  DAST + Vulnerability Management
Phase 4 (Weeks 13–16): CI/CD DevSecOps Pipeline
Phase 5 (Weeks 17–20): Cloud Security Fundamentals
Phase 6 (Weeks 21–24): Security Reviews + Governance Basics
Phase 7 (Weeks 25–28): Communication + Reporting
Phase 8 (Ongoing):     Labs, Portfolio, Interview Prep, Specialization
```

This is 6–7 months of consistent evening/weekend study. Full-time learners can compress it to 3–4 months.

---

## 11.2 Phase 1: OWASP Top 10 and Secure Coding (Weeks 1–4)

### What to Learn

- All 10 OWASP 2021 categories with real-world examples
- The root cause of each vulnerability (not just "what it is")
- The standard mitigation for each
- Secure coding principles: input validation, parameterized queries, output encoding, least privilege

### How to Learn It

| Activity | Resource | Time |
|---|---|---|
| Read OWASP Top 10 official page | owasp.org/Top10 | 2 hours |
| Exploit Juice Shop | Lab 1 from Chapter 10 | 4–6 hours |
| Read PortSwigger Web Security Academy | portswigger.net/web-security | 10–15 hours |
| Build the vulnerable API + fix it | Lab 2 from Chapter 10 | 6–8 hours |

### PortSwigger Web Security Academy — Free Curriculum

PortSwigger (makers of Burp Suite) have an excellent free curriculum:
- SQL injection — read + 16 labs
- XSS — read + 30 labs
- Broken access control — read + 13 labs
- CSRF — read + 8 labs
- Business logic vulnerabilities — read + 12 labs

Each topic has interactive labs you complete in a browser — no setup required.

### Week-by-Week Plan

**Week 1:** OWASP Top 10 reading + A01-A03 PortSwigger labs (Broken Access Control, Crypto, Injection)  
**Week 2:** OWASP A04-A07 + Juice Shop exercises for SQL injection and XSS  
**Week 3:** Secure coding principles + build the vulnerable Flask API  
**Week 4:** Fix the API + write vulnerability reports for each issue found  

### Exit Criteria for Phase 1

You are ready for Phase 2 when you can:
- [ ] Explain all 10 OWASP categories without notes, with a real example for each
- [ ] Write a SQL injection payload and explain why it works
- [ ] Write the parameterized query fix and explain why it prevents the attack
- [ ] Write a vulnerability report in the format from Chapter 9

---

## 11.3 Phase 2: Git/SCM Security + SAST (Weeks 5–8)

### What to Learn

- Git fundamentals: branches, PRs, protected branches, CODEOWNERS
- Secrets detection: Gitleaks, detect-secrets, pre-commit hooks
- How SAST works: pattern matching, AST, taint analysis
- Semgrep: running scans, reading results, writing custom rules, tuning false positives

### How to Learn It

| Activity | Time |
|---|---|
| Read Chapter 2 (SCM Security) and Chapter 3 (SAST) of this guide | 3 hours |
| Set up Semgrep on your demo repo from Phase 1 | 2 hours |
| Configure pre-commit hooks (gitleaks + detect-secrets + ruff) | 2 hours |
| Configure GitHub branch protection rules on your repo | 1 hour |
| Read Semgrep documentation and tutorial | 3 hours |
| Write one custom Semgrep rule for your demo app | 2 hours |

### Semgrep Learning Path

1. **Run the default rules:** `semgrep --config auto .`
2. **Run OWASP rules:** `semgrep --config p/owasp-top-ten .`
3. **Read a finding** and understand why it is flagged
4. **Create a false positive:** write safe code that Semgrep incorrectly flags
5. **Suppress it with justification:** `# nosemgrep: rule-id -- reason`
6. **Write a custom rule** for a pattern in your own code

### Week-by-Week Plan

**Week 5:** Git branch protection + CODEOWNERS setup + read Chapter 2  
**Week 6:** Semgrep setup + run on demo repo + analyze results  
**Week 7:** Pre-commit hooks (Gitleaks, detect-secrets, semgrep) — Lab 4 Part 1  
**Week 8:** Write custom Semgrep rules + tune false positives  

---

## 11.4 Phase 3: DAST + Vulnerability Management (Weeks 9–12)

### What to Learn

- How DAST works, what it finds that SAST cannot
- OWASP ZAP: baseline scan, full scan, API scan
- Burp Suite basics: proxy, repeater, manual testing
- CVSS scoring, SLA frameworks, triage, root cause analysis
- SCA: Trivy, SBOM generation with Syft

### How to Learn It

| Activity | Time |
|---|---|
| Read Chapters 4 and 5 | 3 hours |
| PortSwigger Burp Suite tutorials (free) | 4 hours |
| Run ZAP against your demo app (Lab 3) | 2–3 hours |
| Generate SBOM with Syft, scan with Grype | 2 hours |
| Practice CVSS scoring: score 5 real CVEs | 2 hours |

### Week-by-Week Plan

**Week 9:** DAST concepts + PortSwigger Burp tutorials + install Burp Community  
**Week 10:** ZAP scans against demo app + analyze and document findings  
**Week 11:** CVSS scoring practice + triage framework + SLA document  
**Week 12:** SCA with Trivy + SBOM with Syft + vulnerability management practice  

---

## 11.5 Phase 4: CI/CD DevSecOps Pipeline (Weeks 13–16)

### What to Learn

- GitHub Actions: workflow structure, jobs, steps, permissions, OIDC
- Security gate design: what to gate on, how to baseline
- Secrets management: OIDC, GitHub Secrets, principle of least privilege for CI
- Container security: Dockerfile hardening, Trivy image scanning, cosign
- IaC scanning: Checkov, tfsec

### How to Learn It

| Activity | Time |
|---|---|
| Read Chapter 6 | 2 hours |
| Complete Lab 4 (full CI/CD pipeline) | 4 hours |
| Add IaC scanning: write Terraform + Checkov | 3 hours |
| Configure OIDC for GitHub Actions → AWS | 2 hours |
| Container hardening: rewrite a Dockerfile following best practices | 2 hours |

### Week-by-Week Plan

**Week 13:** GitHub Actions basics + build SAST + SCA pipeline  
**Week 14:** Add container scanning + DAST to pipeline  
**Week 15:** IaC scanning + Dockerfile hardening  
**Week 16:** Full end-to-end pipeline review + OIDC setup  

---

## 11.6 Phase 5: Cloud Security (Weeks 17–20)

### What to Learn

- AWS shared responsibility model
- IAM: roles vs users, least privilege, SCPs
- VPC networking: public/private subnets, security groups, NACLs
- Container security: Kubernetes RBAC, pod security, network policies
- AWS security services: GuardDuty, Security Hub, CloudTrail, Inspector

### How to Learn It

| Activity | Time |
|---|---|
| Read Chapter 7 | 2 hours |
| AWS Cloud Practitioner free course (CloudQuest) | 8–10 hours |
| Run Prowler against AWS account (Lab 6) | 2–3 hours |
| IAM policy writing practice | 2 hours |
| Kubernetes security: read CIS Kubernetes Benchmark | 3 hours |

### Free Cloud Security Resources

- **AWS Skill Builder** (free tier): AWS Security Fundamentals, AWS Security Specialty prep
- **CloudGoat** (Rhino Security Labs): Intentionally vulnerable AWS environment for hands-on attack and defense practice
- **flaws.cloud**: A series of AWS challenges where you exploit misconfigured S3, IAM, metadata service

### Week-by-Week Plan

**Week 17:** AWS fundamentals + IAM deep dive  
**Week 18:** VPC networking + security groups + Lab 6 (cloud review)  
**Week 19:** Container security + Kubernetes basics  
**Week 20:** AWS security services + GuardDuty + Security Hub setup  

---

## 11.7 Phase 6–8: Reviews, Governance, Communication, and Portfolio

**Weeks 21–24:** Security reviews + governance frameworks
- Complete a full security review of your demo application using the template from Chapter 8
- Read a SOC 2 overview and map your current controls
- Write a one-page security policy

**Weeks 25–28:** Communication and reporting
- Write vulnerability reports for 5 vulnerabilities in your demo app
- Create a mock CISO dashboard showing metrics from your CI/CD pipeline
- Record a 5-minute video explaining one vulnerability to a developer audience

**Ongoing:** Portfolio refinement and interview prep

---

## 11.8 Interview Preparation

### Common AppSec Interview Questions and How to Answer Them

**"Walk me through a vulnerability you found."**

Use the STAR format (Situation, Task, Action, Result):

```
Situation: I was reviewing a Flask API I built for learning purposes.

Task: I ran Semgrep against the codebase to identify security issues.

Action: Semgrep flagged a SQL injection on line 87 where user input was
concatenated directly into a SQL query. I manually confirmed exploitability
by sending the payload ' OR '1'='1 which returned all user records.
I fixed it by replacing string concatenation with a parameterized query
(using %s placeholder), added a regression test, and re-ran Semgrep to
confirm the finding was resolved.

Result: The vulnerability was fixed, a regression test prevents reintroduction,
and the fix is documented in the PR with the original finding attached.
```

**"What is the difference between SAST and DAST?"**

```
SAST (Static) analyzes source code without running the application. It finds
vulnerabilities in code patterns — like identifying that a SQL query uses
string concatenation before the app is ever deployed. It runs early in the
pipeline (on every PR) and is fast.

DAST (Dynamic) tests a running application by sending real HTTP requests.
It confirms vulnerabilities are actually exploitable at runtime — like sending
a SQL injection payload and confirming the database returns all records. It
runs against a staging environment and is slower.

They complement each other. SAST can flag patterns that might be safe (false
positives); DAST confirms actual exploitability. DAST finds runtime issues
that SAST cannot see — like missing security headers or session management
flaws — because those only appear when the app is running.
```

**"Walk me through how you would set up a SAST scanner in a CI/CD pipeline."**

```
I would choose a SAST tool based on the team's language stack. For Python,
I'd use Semgrep with the OWASP Top 10 and Python rule packs.

Setup steps:
1. Add a GitHub Actions job that runs Semgrep on every PR
2. Configure it to scan only changed files (diff-only) for speed on PRs,
   and full scan nightly on main
3. Output SARIF format and upload to GitHub Security tab so findings appear
   inline on the PR diff
4. Set the exit code to non-zero on Critical/High findings to block the merge
5. Establish a baseline for the existing codebase so we don't immediately
   block all PRs with legacy technical debt
6. Add a custom rule for any application-specific patterns

After launch, I'd track the false positive rate monthly and tune rules to
keep it below 20%. I'd also write a runbook for developers on how to suppress
false positives with a documented justification.
```

**"How do you communicate a vulnerability to a developer who doesn't have security background?"**

```
I focus on three things: what broke, what an attacker could do with it, and
exactly how to fix it — with a code example.

I avoid jargon. Instead of "CWE-89 Injection in the Data Access Layer,"
I say: "The search API can be tricked into returning all user records.
Here's the exact attack payload, here's what it returns, and here's the
two-line fix."

I also link to a tutorial so they understand why — not just what to change.
Developers who understand why a fix works write better code going forward.
```

**"What would you do on your first 30 days at a new AppSec job?"**

```
Week 1: Understand the environment
- Read existing security policies, standards, and any audit reports
- Meet with the development team leads to understand their tech stack, team size,
  and pain points with security today
- Review the existing CI/CD pipeline and identify what security tools are already
  integrated vs. missing

Week 2: Asset inventory and vulnerability landscape
- Understand what systems exist, what data they handle (PII, payment, health)
- Review open vulnerability findings: what is the backlog? What is the SLA?
- Identify which systems are highest risk (internet-facing, PHI/PCI)

Week 3: Quick wins
- Pick 2–3 high-impact, low-effort improvements (e.g., "Semgrep is configured
  but results not posted as PR comments — enable reviewdog")
- Fix a visible gap that affects developers daily

Week 4: Plan
- Present a 90-day roadmap to the security manager and development leads
- Include: gaps found, proposed tool additions, training plan, SLA improvements

Throughout: Listen more than you talk in the first 30 days. Understand
why existing decisions were made before proposing changes.
```

---

## 11.9 Certifications — What Is Worth Pursuing

| Certification | Value | When to Pursue | Cost |
|---|---|---|---|
| **CompTIA Security+** | Entry-level validation, government/defense required | Before your first security role | $392 exam |
| **CEH (Certified Ethical Hacker)** | Recognized brand, useful for employer signaling | After 6+ months hands-on | $950 + training |
| **OSCP (Offensive Security Certified Professional)** | Gold standard for pentesters; very hands-on | After 1 year if specializing in penetration testing | $1,499 |
| **GWAPT (GIAC Web Application Penetration Tester)** | Strong signal for AppSec roles | After solid web security foundation | $2,000–$7,000 |
| **AWS Security Specialty** | Strong for cloud-focused AppSec | After Phase 5 (cloud security) | $300 exam |
| **CISSP** | Management and governance credibility | After 5+ years experience | $699 exam |

**Recommendation for your path:** Start with **Security+** for baseline validation while you build the practical skills. Pursue **AWS Security Specialty** once you complete Phase 5. **OSCP** or **GWAPT** if you want to specialize in offensive security/penetration testing.

---

## 11.10 Specialization Paths

After the foundation (Chapters 1–10), specialize in one or two areas for senior-level depth:

### Option A: Application Security Specialist

**Focus:** Deep expertise in SAST, DAST, code review, secure design

**Extra study:**
- PortSwigger Web Security Academy — complete all advanced labs
- Custom Semgrep rule writing — contribute to the Semgrep registry
- Penetration testing specialization (OSCP)
- Write a security tool or contribute to an open-source security project

**Typical title:** Senior AppSec Engineer, Application Security Architect

### Option B: DevSecOps Specialist

**Focus:** Building and operating security automation at scale

**Extra study:**
- Advanced GitHub Actions / GitLab CI/CD patterns
- Kubernetes security deep dive (CKS certification)
- Policy-as-code: OPA (Open Policy Agent), Kyverno
- Supply chain security: SLSA, sigstore, in-toto attestations
- Platform engineering security

**Typical title:** DevSecOps Engineer, Security Platform Engineer

### Option C: Cloud Security Specialist

**Focus:** AWS/Azure/GCP security, CSPM, workload protection

**Extra study:**
- AWS Security Specialty certification
- Prowler deep dive and custom checks
- Cloud attack techniques (CloudGoat, HackTheBox cloud modules)
- IAM deep dive, SCPs, permission boundaries
- CSPM tools: Prisma Cloud, Wiz, Orca

**Typical title:** Cloud Security Engineer, Security Architect (Cloud)

### Option D: AI Security Specialist (Emerging)

**Focus:** Security of AI/ML systems and LLM-powered applications

**Extra study:**
- OWASP Top 10 for LLM Applications
- Prompt injection techniques and mitigations
- AI model evaluation security (MLflow, model cards)
- AI red-teaming tools: Garak, promptfoo
- RAG system security, tool use security

**Typical title:** AI Security Engineer, MLSecOps Engineer

---

## 11.11 Day in the Life — Enterprise AppSec Engineer

Here is what a typical day actually looks like:

**Morning (9:00–11:00 AM)**
- Review overnight scanner alerts (new critical CVE from Dependabot, GuardDuty finding from staging)
- Triage new SAST findings from PRs that were merged yesterday
- Answer developer questions: "Semgrep is flagging this — is it a false positive?"

**Mid-morning (11:00 AM–12:00 PM)**
- Security review meeting for a new feature (user-uploaded file processing)
- Review the design doc, draw a data flow, identify SSRF and path traversal risks
- Write up security requirements for the dev team

**Afternoon (1:00–3:00 PM)**
- Work on a project: "Add ZAP DAST to the staging pipeline for the payments service"
- Write the GitHub Actions workflow, configure the scan policy, test against staging

**Late afternoon (3:00–5:00 PM)**
- Write the monthly CISO report (pull metrics from dashboards, write the summary)
- Quick code review for a high-risk PR (new auth implementation)
- Update a secure coding tutorial: a new SQL injection variant was found this week

**Ad hoc (throughout day)**
- Respond to Slack: "Is it safe to use library X for cryptography?"
- Review a dependency update PR (SCA scan passes, approve)
- Handle an escalation: dev team wants to accept risk on a Medium finding — review and document

---

## 11.12 The Realistic Timeline

**Months 1–3:** Fundamentals phase (OWASP, SAST, DAST basics)
- You can explain vulnerabilities clearly
- You can run SAST and DAST and interpret results
- You have a demo app in GitHub with security pipeline

**Months 3–6:** Automation and cloud phase
- You have a production-grade CI/CD security pipeline
- You can conduct a basic cloud security review
- You can run a threat modeling session

**Months 6–9:** Communication and governance phase
- You can write clear vulnerability reports for developers and executives
- You understand SOC 2, NIST CSF, and PCI-DSS at a working level
- You have a portfolio with 4–6 documented projects

**After 9 months:** Interview-ready for entry-to-mid-level AppSec roles (2–4 YOE equivalent depth in key areas)

**Months 9–18:** Specialization and depth — choose 1–2 areas, go deep, build artifacts that show senior-level thinking in those areas

---

## Chapter 11 Summary

| Phase | Focus | Duration |
|---|---|---|
| Phase 1 | OWASP Top 10 + Secure Coding | 4 weeks |
| Phase 2 | SCM Security + SAST | 4 weeks |
| Phase 3 | DAST + Vulnerability Management | 4 weeks |
| Phase 4 | CI/CD DevSecOps | 4 weeks |
| Phase 5 | Cloud Security | 4 weeks |
| Phase 6–8 | Reviews, Governance, Communication, Portfolio | 8 weeks |
| Ongoing | Specialization + interview prep | Indefinite |

**The most important thing:** Do the labs. Knowledge without practice does not build the muscle memory that interviews and the job require. Every hour of hands-on work is worth 3 hours of reading.

---

## Final Reading List

### Free Online Resources (Start Here)

- **OWASP:** owasp.org — Top 10, ASVS, Testing Guide, Cheat Sheets
- **PortSwigger Web Security Academy:** portswigger.net/web-security — free interactive labs
- **NIST Cybersecurity Framework:** nist.gov/cyberframework
- **Semgrep Docs:** semgrep.dev/docs
- **AWS Security Documentation:** docs.aws.amazon.com/security

### Books Worth Buying

- *The Web Application Hacker's Handbook* (Stuttard, Pinto) — comprehensive web security
- *The DevSecOps Playbook* (Sean Mack) — DevSecOps implementation
- *Hacking: The Art of Exploitation* (Erickson) — deep understanding of how attacks work
- *Security Engineering* (Anderson) — academic but comprehensive; builds mental models

### Hands-On Platforms

- **HackTheBox:** hackthebox.com — attack-focused, builds offensive skills
- **TryHackMe:** tryhackme.com — more guided, good for beginners
- **PentesterLab:** pentesterlab.com — web application security focused
- **CloudGoat:** Intentionally vulnerable AWS environment

---

*You have now completed the Enterprise Application Security Engineer Knowledge Guide.*

*Start with [Chapter 1: Application Security Fundamentals](01-AppSec-Fundamentals.md) and work through to [Chapter 10: Hands-On Labs](10-Hands-On-Labs.md) before revisiting this progression guide.*
