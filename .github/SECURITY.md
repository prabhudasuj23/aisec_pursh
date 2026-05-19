# Security Policy

## Scope

This repository contains:
- **AISec** — an enterprise security platform (control plane, scanners, dashboard)
- **Pursh** — a synthetic telehealth demonstration app used as a scan target

**Pursh is a demonstration project, not a real medical service. It contains no
real patient health information (PHI). All data is synthetically generated.**

## Supported versions

| Component | Supported |
|---|---|
| `main` branch | ✅ Yes |
| Feature branches | ❌ No — report against `main` |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

### Private disclosure

Report vulnerabilities via **GitHub Security Advisories**:

1. Go to the **Security** tab of this repository.
2. Click **"Report a vulnerability"**.
3. Fill in the template with as much detail as possible.

Alternatively, email: **security@aivistix.com** (PGP key available on request).

### What to include

- Description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept if available)
- Affected component(s) and version/commit hash
- Any suggested mitigations

### Response timeline

| Stage | Target |
|---|---|
| Acknowledgement | Within **48 hours** |
| Initial triage | Within **5 business days** |
| Fix or mitigation | Within **30 days** for Critical/High; **90 days** for Medium/Low |
| Public disclosure | Coordinated — we will notify you before publishing |

## Out of scope

The following are **not** in scope for this security policy:

- Findings from automated scanners run against the demo environment without
  prior coordination (we already scan ourselves — see AISec's own pipeline)
- Denial-of-service attacks against the public demo
- Social engineering of project maintainers
- Issues in third-party dependencies already tracked in Dependabot alerts
- Theoretical vulnerabilities without a working proof of concept

## Safe harbor

We consider good-faith security research under this policy to be:

- Authorized against `aisec.aivistix.com` and `pursh.aivistix.com` demo environments only
- Not authorized against any other Aivistix systems

Researchers acting in good faith under this policy will not be pursued legally.

## Recognition

We maintain a public acknowledgements list in `/docs/security-acknowledgements.md`
for researchers who responsibly disclose valid vulnerabilities.
