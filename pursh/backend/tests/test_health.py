"""
Pursh backend smoke + security tests.
These run in CI (Stage 1) and verify the app starts and key security controls hold.
"""

import sys
import os

# Add backend root to path so imports resolve the same way as in Docker
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ── Health ─────────────────────────────────────────────────────────────────────

def test_healthz_returns_200():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Public endpoints ───────────────────────────────────────────────────────────

def test_list_doctors_public():
    """GET /api/v1/doctors/ is a public endpoint — no auth needed."""
    resp = client.get("/api/v1/doctors/")
    assert resp.status_code == 200
    doctors = resp.json()
    assert len(doctors) >= 1
    # Each doctor profile has a disclaimer (anti-medical-advice)
    for doc in doctors:
        assert "disclaimer" in doc
        assert "Demonstration project" in doc["disclaimer"]


def test_doctor_not_found_returns_404():
    resp = client.get("/api/v1/doctors/nonexistent-id")
    assert resp.status_code == 404


def test_list_synthetic_patients_public():
    """Public demo endpoint returns synthetic patients with disclaimer."""
    resp = client.get("/api/v1/patients/list")
    assert resp.status_code == 200
    patients = resp.json()
    assert len(patients) >= 1
    for p in patients:
        assert "disclaimer" in p
        assert "Demonstration project" in p["disclaimer"]


# ── Auth enforcement ───────────────────────────────────────────────────────────

def test_patient_me_requires_auth():
    """Unauthenticated request to /me must return 401 or 403."""
    resp = client.get("/api/v1/patients/me")
    assert resp.status_code in (401, 403)


def test_appointments_requires_auth():
    resp = client.post("/api/v1/appointments/", json={
        "doctor_id": "doctor-uuid-001",
        "appointment_type": "video",
        "reason": "Test reason",
    })
    assert resp.status_code in (401, 403)


def test_symptoms_requires_auth():
    resp = client.post("/api/v1/symptoms/check", json={"symptoms": "headache"})
    assert resp.status_code in (401, 403)


def test_doctor_patients_requires_doctor_role():
    """Doctor-only endpoint must reject unauthenticated callers."""
    resp = client.get("/api/v1/doctors/me/patients")
    assert resp.status_code in (401, 403)


# ── Input validation ───────────────────────────────────────────────────────────

def test_openapi_json_available_in_non_prod():
    """OpenAPI docs are available (dev/local env) — useful for DAST scanning."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "Pursh API"
