"""
Pursh — Patient API endpoints.

Patients can view and update their own profile and medical history.
RLS in Supabase enforces that patients only see their own records at the DB layer.

DISCLAIMER: All data is synthetic. Do not enter real PHI.
PHI-SAFE: All functions touching patient data log only hashed IDs.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from pursh.backend.auth.supabase import PurshUser, require_pursh_user
from pursh.backend.core.logging import get_logger, hash_patient_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

DISCLAIMER = "Demonstration project — not a real medical service. Synthetic test data only."


# ── Response models ───────────────────────────────────────────────────────────

class PatientProfile(BaseModel):
    id: str
    display_name: str
    email: EmailStr
    date_of_birth: str | None = None   # YYYY-MM-DD
    disclaimer: str = DISCLAIMER


class SymptomHistory(BaseModel):
    id: str
    patient_id: str
    symptom_description: str
    severity: str                      # mild / moderate / severe
    reported_at: str
    disclaimer: str = DISCLAIMER


# ── Synthetic in-memory data (replaced by Supabase queries in Phase 2) ────────

_SYNTHETIC_PATIENTS: dict[str, dict] = {
    "patient-uuid-001": {
        "id": "patient-uuid-001",
        "display_name": "Test Patient A",
        "email": "testpatient.a@example.com",
        "date_of_birth": "1990-01-01",
    },
    "patient-uuid-002": {
        "id": "patient-uuid-002",
        "display_name": "Test Patient B",
        "email": "testpatient.b@example.com",
        "date_of_birth": "1985-06-15",
    },
}

_SYNTHETIC_SYMPTOMS: list[dict] = [
    {
        "id": "symptom-001",
        "patient_id": "patient-uuid-001",
        "symptom_description": "Mild headache lasting 2 days (synthetic test record)",
        "severity": "mild",
        "reported_at": "2026-05-01T10:00:00Z",
    },
    {
        "id": "symptom-002",
        "patient_id": "patient-uuid-001",
        "symptom_description": "Fatigue after exercise (synthetic test record)",
        "severity": "mild",
        "reported_at": "2026-05-10T14:00:00Z",
    },
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/me", response_model=PatientProfile)
async def get_my_profile(user: PurshUser = Depends(require_pursh_user)) -> PatientProfile:
    """Return the authenticated patient's own profile. PHI-SAFE: logs hashed ID only."""
    # Phase 2: replace with Supabase RLS query
    data = _SYNTHETIC_PATIENTS.get(user.sub)
    if not data:
        # Return a synthetic profile for any valid authenticated user
        data = {
            "id": user.sub,
            "display_name": "Test Patient (synthetic)",
            "email": user.email,
            "date_of_birth": None,
        }
    logger.info("patient_profile_viewed", log_id=hash_patient_id(user.sub))  # PHI-SAFE
    return PatientProfile(**data)


@router.get("/me/symptoms", response_model=list[SymptomHistory])
async def get_my_symptoms(user: PurshUser = Depends(require_pursh_user)) -> list[SymptomHistory]:
    """Return symptom history for the authenticated patient. PHI-SAFE."""
    # Phase 2: replace with Supabase RLS query filtering by auth.uid()
    symptoms = [s for s in _SYNTHETIC_SYMPTOMS if s["patient_id"] == user.sub]
    logger.info("patient_symptoms_viewed", log_id=hash_patient_id(user.sub), count=len(symptoms))
    return [SymptomHistory(**s) for s in symptoms]


@router.get("/list", response_model=list[PatientProfile])
async def list_synthetic_patients() -> list[PatientProfile]:
    """
    Public endpoint — returns synthetic patient list for demo purposes.
    No real PHI. Used by the AISec public dashboard demo.
    """
    return [PatientProfile(**p) for p in _SYNTHETIC_PATIENTS.values()]
