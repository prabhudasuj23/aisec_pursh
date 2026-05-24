"""
Pursh — Doctor API endpoints.

Doctors can view their assigned patients and appointments.
RLS ensures doctors only see patients assigned to them.

PHI-SAFE: All logs use hashed actor IDs.
DISCLAIMER: Synthetic data only. Not a real medical service.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.supabase import PurshUser, require_doctor, require_pursh_user
from core.logging import get_logger, hash_patient_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/doctors", tags=["doctors"])

DISCLAIMER = "Demonstration project — not a real medical service. Synthetic test data only."


class DoctorProfile(BaseModel):
    id: str
    display_name: str
    specialty: str
    bio: str
    availability: str
    disclaimer: str = DISCLAIMER


class AssignedPatient(BaseModel):
    patient_id: str
    display_name: str
    next_appointment: str | None


# ── Synthetic data ────────────────────────────────────────────────────────────

SYNTHETIC_DOCTORS = [
    DoctorProfile(
        id="doctor-uuid-001",
        display_name="Dr. Alex Chen (Synthetic)",
        specialty="General Practice",
        bio="Synthetic profile for security testing. Not a real physician.",
        availability="Mon-Fri 9am-5pm",
    ),
    DoctorProfile(
        id="doctor-uuid-002",
        display_name="Dr. Jordan Patel (Synthetic)",
        specialty="Dermatology",
        bio="Synthetic profile for security testing. Not a real physician.",
        availability="Tue-Thu 10am-4pm",
    ),
    DoctorProfile(
        id="doctor-uuid-003",
        display_name="Dr. Morgan Lee (Synthetic)",
        specialty="Mental Health",
        bio="Synthetic profile for security testing. Not a real physician.",
        availability="Mon-Wed 8am-6pm",
    ),
    DoctorProfile(
        id="doctor-uuid-004",
        display_name="Dr. Sam Rivera (Synthetic)",
        specialty="Hair Loss",
        bio="Synthetic profile for security testing. Not a real physician.",
        availability="Wed-Fri 9am-3pm",
    ),
    DoctorProfile(
        id="doctor-uuid-005",
        display_name="Dr. Taylor Kim (Synthetic)",
        specialty="Sexual Health",
        bio="Synthetic profile for security testing. Not a real physician.",
        availability="Mon-Thu 10am-6pm",
    ),
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[DoctorProfile])
async def list_doctors() -> list[DoctorProfile]:
    """Public endpoint — browse available doctors for booking."""
    return SYNTHETIC_DOCTORS


@router.get("/{doctor_id}", response_model=DoctorProfile)
async def get_doctor(doctor_id: str) -> DoctorProfile:
    doctor = next((d for d in SYNTHETIC_DOCTORS if d.id == doctor_id), None)
    if not doctor:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return doctor


@router.get("/me/patients", response_model=list[AssignedPatient])
async def get_my_patients(user: PurshUser = Depends(require_doctor)) -> list[AssignedPatient]:
    """Doctor-only: view assigned patients. PHI-SAFE."""
    logger.info("doctor_patient_list_viewed", log_id=hash_patient_id(user.sub))
    # Phase 2: replace with Supabase RLS query
    return [
        AssignedPatient(
            patient_id="patient-uuid-001",
            display_name="Test Patient A (synthetic)",
            next_appointment="2026-06-01T10:00:00Z",
        )
    ]
