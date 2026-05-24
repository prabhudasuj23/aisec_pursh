# Enterprise Application Security Engineer — Complete Knowledge Guide

> **Purpose:** A practical, simple-language reference covering everything an enterprise Application Security (AppSec) / DevSecOps engineer needs to know. Each chapter includes real-world case studies, tool guidance, and day-in-the-life context.

---

## How to Use This Guide

Read chapters in order if you are new to AppSec. Jump to any chapter if you need a reference on a specific topic. Every chapter is self-contained.

---

## Table of Contents

| # | Chapter | What You Will Learn |
|---|---|---|
| 1 | [Application Security Fundamentals](01-AppSec-Fundamentals.md) | SDLC, OWASP Top 10, Threat Modeling, Secure Coding |
| 2 | [Git & SCM Security](02-SCM-Security.md) | Branch protection, secrets detection, repo hygiene |
| 3 | [SAST — Static Testing](03-SAST.md) | Finding bugs in code before it runs |
| 4 | [DAST — Dynamic Testing](04-DAST.md) | Finding bugs in running applications |
| 5 | [Vulnerability Management](05-Vulnerability-Management.md) | Triage, CVSS, patching SLAs, verification |
| 6 | [CI/CD & DevSecOps](06-CICD-DevSecOps.md) | Secure pipelines, automated gates, secrets management |
| 7 | [Cloud & Infrastructure Security](07-Cloud-Infrastructure-Security.md) | AWS/Azure/GCP, IAM, containers, Kubernetes |
| 8 | [Security Reviews, Audits & Governance](08-Reviews-Audits-Governance.md) | Architecture reviews, SOC 2, ISO 27001, NIST, PCI-DSS |
| 9 | [Communication & Reporting](09-Communication-Reporting.md) | Writing findings, exec reports, developer guidance |
| 10 | [Hands-On Labs & Projects](10-Hands-On-Labs.md) | Practical exercises and portfolio projects |
| 11 | [Learning Progression & Career Map](11-Learning-Progression.md) | Study order, interview stories, career growth |

---

## Real-World Case Studies Covered

| Incident | Chapter | Lesson |
|---|---|---|
| Equifax 2017 (147M records) | 1, 5 | Unpatched open-source component (Apache Struts) |
| Log4Shell 2021 | 1, 3, 5 | Critical vulnerability in logging library |
| SolarWinds 2020 | 1, 6 | Supply chain attack via CI/CD compromise |
| Capital One 2019 | 7 | SSRF + over-privileged IAM role |
| British Airways 2018 | 4 | Magecart JavaScript injection, XSS |
| CircleCI 2023 | 6 | CI secrets stolen, token abuse |
| Samsung GitHub Leak | 2 | Hardcoded credentials pushed to public repo |
| Heartbleed 2014 | 3 | Bounds check bug in OpenSSL |
| Uber 2022 | 8, 9 | Auth bypass, breach cover-up |
| Meltdown/Spectre | 5 | Enterprise-wide patching under pressure |

---

## Quick Reference: What AppSec Engineers Do Day-to-Day

- Triage scanner findings from SAST, DAST, SCA, and container scans
- Review pull requests for security issues
- Build and maintain security automation in CI/CD pipelines
- Run threat modeling sessions for new features
- Write remediation guidance for developers
- Support compliance audits (SOC 2, PCI-DSS, ISO 27001)
- Respond to security incidents and vulnerabilities
- Coach developers on secure coding patterns
- Report risk posture to leadership

---

*This guide maps directly to the responsibilities in enterprise AppSec and DevSecOps job descriptions.*
