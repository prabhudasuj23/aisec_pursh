"""
CWE → OWASP / ASVS / HIPAA / GDPR mapping tables.

These mappings are DATA, not business logic. They live here as Python dicts
(loaded once at startup) and are referenced by the normalizers.

Anti-pattern §8.4: never hardcode mappings in business logic. All mapping
lookups go through the functions in this module.

Sources:
- OWASP Top 10 2021: https://owasp.org/Top10/
- OWASP ASVS v4.0.3: https://owasp.org/www-project-application-security-verification-standard/
- HIPAA Security Rule: 45 CFR Part 164
- GDPR Article 32
"""

from __future__ import annotations

# ── CWE → OWASP Top 10 2021 ──────────────────────────────────────────────────
# Key: CWE-NNN  Value: OWASP category code
_CWE_TO_OWASP: dict[str, str] = {
    # A01: Broken Access Control
    "CWE-22": "A01:2021",   # Path traversal
    "CWE-284": "A01:2021",  # Improper access control
    "CWE-285": "A01:2021",  # Improper authorization
    "CWE-639": "A01:2021",  # IDOR
    "CWE-352": "A01:2021",  # CSRF
    # A02: Cryptographic Failures
    "CWE-312": "A02:2021",  # Cleartext storage of sensitive info
    "CWE-319": "A02:2021",  # Cleartext transmission
    "CWE-326": "A02:2021",  # Inadequate encryption strength
    "CWE-327": "A02:2021",  # Broken crypto algorithm
    "CWE-330": "A02:2021",  # Insufficient random values
    # A03: Injection
    "CWE-89": "A03:2021",   # SQL injection
    "CWE-79": "A03:2021",   # XSS
    "CWE-78": "A03:2021",   # OS command injection
    "CWE-94": "A03:2021",   # Code injection
    "CWE-77": "A03:2021",   # Command injection
    "CWE-90": "A03:2021",   # LDAP injection
    # A04: Insecure Design
    "CWE-209": "A04:2021",  # Error message exposure
    "CWE-434": "A04:2021",  # Unrestricted file upload
    # A05: Security Misconfiguration
    "CWE-16": "A05:2021",   # Configuration
    "CWE-611": "A05:2021",  # XML external entity
    # A06: Vulnerable and Outdated Components
    "CWE-1104": "A06:2021", # Outdated component
    # A07: Identification and Authentication Failures
    "CWE-287": "A07:2021",  # Improper authentication
    "CWE-306": "A07:2021",  # Missing authentication
    "CWE-798": "A07:2021",  # Hard-coded credentials
    "CWE-521": "A07:2021",  # Weak password requirements
    # A08: Software and Data Integrity Failures
    "CWE-502": "A08:2021",  # Deserialization
    "CWE-829": "A08:2021",  # Inclusion from untrusted source
    # A09: Security Logging and Monitoring Failures
    "CWE-223": "A09:2021",  # Omission of security-relevant information
    "CWE-778": "A09:2021",  # Insufficient logging
    # A10: SSRF
    "CWE-918": "A10:2021",  # SSRF
}

# ── CWE → OWASP ASVS v4.0.3 controls ─────────────────────────────────────────
_CWE_TO_ASVS: dict[str, list[str]] = {
    "CWE-89":  ["V5.3.4", "V5.3.5"],   # SQL injection → Input validation
    "CWE-79":  ["V5.3.3", "V14.4.1"],  # XSS → Output encoding
    "CWE-78":  ["V5.3.8"],             # OS command injection
    "CWE-287": ["V2.1.1", "V3.3.1"],   # Authentication
    "CWE-798": ["V2.10.1"],            # Hard-coded credentials
    "CWE-312": ["V6.2.1", "V9.1.1"],   # Cleartext storage
    "CWE-319": ["V9.1.1", "V9.1.2"],   # Cleartext transmission
    "CWE-352": ["V4.2.2", "V13.2.3"],  # CSRF
    "CWE-22":  ["V5.2.2", "V12.3.1"],  # Path traversal
    "CWE-918": ["V10.3.2"],            # SSRF
    "CWE-502": ["V5.5.1", "V5.5.2"],   # Deserialization
}

# ── CWE → HIPAA Security Rule sections ───────────────────────────────────────
_CWE_TO_HIPAA: dict[str, list[str]] = {
    "CWE-287": ["164.312(d)"],          # Authentication failures
    "CWE-306": ["164.312(a)(1)"],       # Missing authentication → access control
    "CWE-312": ["164.312(a)(2)(iv)"],   # Cleartext storage → encryption
    "CWE-319": ["164.312(e)(1)"],       # Cleartext transmission
    "CWE-89":  ["164.312(b)"],          # SQL injection → audit controls
    "CWE-79":  ["164.312(b)"],          # XSS → audit controls
    "CWE-223": ["164.312(b)"],          # Missing logging → audit controls
    "CWE-284": ["164.312(a)(1)"],       # Access control
    "CWE-639": ["164.312(a)(1)"],       # IDOR → access control
}

# ── CWE → GDPR Article 32 sub-clauses ─────────────────────────────────────────
_CWE_TO_GDPR: dict[str, list[str]] = {
    "CWE-312": ["Art32(1)(a)"],   # Cleartext storage → pseudonymization/encryption
    "CWE-319": ["Art32(1)(b)"],   # Cleartext transmission → confidentiality
    "CWE-287": ["Art32(1)(b)"],   # Auth failures → confidentiality/integrity
    "CWE-284": ["Art32(1)(b)"],   # Access control → confidentiality
    "CWE-223": ["Art32(1)(d)"],   # Missing logging → testing/evaluation
    "CWE-89":  ["Art32(1)(b)"],   # SQL injection → integrity
}


def cwe_to_owasp_top10(cwes: list[str]) -> str | None:
    for cwe in cwes:
        if result := _CWE_TO_OWASP.get(cwe):
            return result
    return None


def cwe_to_asvs(cwes: list[str]) -> list[str]:
    controls: list[str] = []
    for cwe in cwes:
        controls.extend(_CWE_TO_ASVS.get(cwe, []))
    return list(dict.fromkeys(controls))


def cwe_to_hipaa(cwes: list[str]) -> list[str]:
    sections: list[str] = []
    for cwe in cwes:
        sections.extend(_CWE_TO_HIPAA.get(cwe, []))
    return list(dict.fromkeys(sections))


def cwe_to_gdpr(cwes: list[str]) -> list[str]:
    clauses: list[str] = []
    for cwe in cwes:
        clauses.extend(_CWE_TO_GDPR.get(cwe, []))
    return list(dict.fromkeys(clauses))
