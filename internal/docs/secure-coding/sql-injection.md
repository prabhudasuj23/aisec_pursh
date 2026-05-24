# Secure Coding: SQL Injection (CWE-89)

**Audience:** Backend developers working on Pursh or AISec (Python / FastAPI / SQLAlchemy)  
**OWASP:** A03:2021 — Injection  
**ASVS:** V5.3.4, V5.3.5  
**HIPAA:** §164.312(b) — Audit controls  
**Semgrep rule:** `python.lang.security.audit.formatted-sql-query`  
**Remediation card:** [aisec/app/mappings/remediation/CWE-89.md](../../aisec/app/mappings/remediation/CWE-89.md)

---

## What the weakness is

SQL injection occurs when user-supplied input is concatenated directly into a SQL
query string instead of being passed as a separate parameter. The database cannot
distinguish the injected content from the intended query structure, allowing an
attacker to:

- Read rows they are not authorized to see (e.g., all patient records)
- Modify or delete records
- In some databases: execute OS commands via stored procedures

In a HIPAA context this is an audit control failure (§164.312(b)) — an attacker
can insert false audit records or delete real ones, making breach detection impossible.

---

## Vulnerable code

```python
# pursh/backend/api/patients.py — NEVER do this
from sqlalchemy import text

async def get_patient(patient_id: str, db: AsyncSession):
    # patient_id comes from the URL path — attacker-controlled
    query = f"SELECT * FROM patient_records WHERE patient_id = '{patient_id}'"
    result = await db.execute(text(query))
    return result.fetchall()
```

**Payload that breaks this:**
```
GET /api/v1/patients/' OR '1'='1
```
Returns every patient record in the database.

**Payload that drops a table:**
```
GET /api/v1/patients/x'; DROP TABLE patient_records; --
```

---

## Fixed code

**Option A — ORM style (preferred for this repo)**

```python
from sqlalchemy import select
from app.models.patient import PatientRecord

async def get_patient(patient_id: str, db: AsyncSession):
    # SQLAlchemy ORM builds parameterized SQL automatically
    stmt = select(PatientRecord).where(PatientRecord.patient_id == patient_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

**Option B — raw SQL when ORM is not practical**

```python
from sqlalchemy import text

async def get_patient(patient_id: str, db: AsyncSession):
    # Named parameter — driver handles quoting and escaping
    stmt = text("SELECT * FROM patient_records WHERE patient_id = :pid")
    result = await db.execute(stmt, {"pid": patient_id})
    return result.fetchall()
```

Both options produce parameterized queries. The database treats `patient_id` as
data, not as SQL syntax — injection is structurally impossible.

---

## How Semgrep detects it

Semgrep rule: `python.lang.security.audit.formatted-sql-query.formatted-sql-query`  
Pack: `p/python`, `p/security-audit` (both run on every PR in this repo)

Semgrep flags any f-string or `.format()` call passed to a SQL execution function:

```
Finding: formatted-sql-query
Severity: ERROR
File: pursh/backend/api/patients.py
Line: 8
Rule: python.lang.security.audit.formatted-sql-query
Message: String formatting used in SQL query. Use parameterized queries.

  8 | query = f"SELECT * FROM patient_records WHERE patient_id = '{patient_id}'"
```

Semgrep fires on the pattern regardless of whether the variable is truly
attacker-controlled — it is conservative by design. Always verify whether the
flagged variable comes from user input before dismissing it.

---

## How to fix it next time

- **Default to ORM.** `select(Model).where(Model.col == val)` is always parameterized.
- **If you must use raw SQL**, use `text("... :param")` with a dict — never f-strings.
- **Never trust `repr()` or `str()`** as an escaping mechanism — it is not.
- **Test it.** Add a test that sends `' OR '1'='1` as the input and confirms the
  query returns only the expected row (or nothing), not all rows.

---

## Compliance reference

| Framework | Control | Requirement |
|---|---|---|
| OWASP Top 10 2021 | A03:2021 | Injection prevention |
| OWASP ASVS v4.0.3 | V5.3.4 | Parameterized query interfaces |
| OWASP ASVS v4.0.3 | V5.3.5 | Parameterized stored procedures |
| HIPAA Security Rule | §164.312(b) | Audit controls — data integrity |
| GDPR Art. 32 | Art32(1)(b) | Integrity of processing |
