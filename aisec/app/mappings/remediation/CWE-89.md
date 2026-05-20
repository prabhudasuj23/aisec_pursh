# CWE-89 — SQL Injection

**OWASP Top 10 2021:** A03:2021 — Injection  
**ASVS v4.0.3:** V5.3.4, V5.3.5 (Parameterized queries required)  
**HIPAA:** §164.312(b) — Audit controls (data integrity must be enforced at DB layer)  
**GDPR:** Art32(1)(b) — Integrity of processing  
**CIS Control:** 16.5 — Use parameterized interfaces  

---

## What it is

SQL Injection occurs when user-supplied input is concatenated directly into a SQL
query string. An attacker can break out of the intended query and execute arbitrary
SQL — reading data they shouldn't see, modifying records, or dropping tables.

In a HIPAA context this is a §164.312(b) violation: the audit trail becomes
untrustworthy once an attacker can insert or delete rows.

---

## Vulnerable code (Python / SQLAlchemy raw text)

```python
# NEVER do this — user_id comes from the request
query = f"SELECT * FROM patient_records WHERE patient_id = '{user_id}'"
result = await db.execute(text(query))
```

An attacker sends `user_id = "' OR '1'='1"` and reads every patient record.

---

## Fixed code (SQLAlchemy 2.0 parameterized)

```python
# Correct — parameter binding; driver handles quoting and escaping
from sqlalchemy import select, text
from app.models.finding import PatientRecord

# ORM style (preferred)
stmt = select(PatientRecord).where(PatientRecord.patient_id == user_id)
result = await db.execute(stmt)

# Raw text when ORM is not possible — still parameterized
stmt = text("SELECT * FROM patient_records WHERE patient_id = :uid")
result = await db.execute(stmt, {"uid": user_id})
```

---

## How Semgrep detects it

Rule: `python.lang.security.audit.formatted-sql-query.formatted-sql-query`  
Pack: `p/python`, `p/security-audit`

Semgrep flags any f-string or `.format()` call passed to a SQL execution method.
It fires regardless of whether the variable is attacker-controlled — conservative
by design. Always review whether the flagged variable actually comes from user input.

```
finding: formatted-sql-query
severity: ERROR
location: pursh/backend/api/patients.py:42
message: String interpolation in SQL query — use parameterized queries instead.
```

---

## Fix checklist

- [ ] Replace every `text(f"...")` or `text("...".format(...))` with `text("... :param")` + dict
- [ ] Prefer ORM-style (`select(Model).where(Model.col == val)`) over raw SQL
- [ ] Add a Semgrep custom rule for this pattern to `scanners/semgrep/custom-rules.yaml`
- [ ] Write a regression test that passes a SQLi payload and confirms 422 response

---

## See also

- [Secure coding tutorial: SQL injection](../../../docs/secure-coding/sql-injection.md)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [SQLAlchemy 2.0 — Parameterized statements](https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.text)
