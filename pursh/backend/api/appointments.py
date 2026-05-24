"""
Pursh — Appointment booking endpoints.

Patients book appointments with doctors. The booking flow is the primary
DAST scan surface (ZAP will test auth, IDOR, CSRF on these endpoints).

PHI-SAFE: All logs use hashed actor IDs.
"""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from auth.supabase import PurshUser, require_pursh_user
from core.logging import get_logger, hash_patient_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])

DISCLAIMER = "Demonstration project — not a real medical service. Synthetic test data only."

VALID_DOCTOR_IDS = {
    "doctor-uuid-001", "doctor-uuid-002", "doctor-uuid-003",
    "doctor-uuid-004", "doctor-uuid-005",
}


class BookAppointmentRequest(BaseModel):
    doctor_id: str
    appointment_type: str   # "video" | "async_message"
    reason: str             # patient's stated reason — AI-1 doctor-matching input

    @field_validator("doctor_id")
    @classmethod
    def validate_doctor_id(cls, v: str) -> str:
        if v not in VALID_DOCTOR_IDS:
            raise ValueError("Invalid doctor_id.")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason_length(cls, v: str) -> str:
        if len(v) > 1000:
            raise ValueError("Reason must be under 1000 characters.")
        # Intentionally NOT sanitizing here for DAST/ZSS testing visibility
        return v

    @field_validator("appointment_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("video", "async_message"):
            raise ValueError("appointment_type must be 'video' or 'async_message'.")
        return v


class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    appointment_type: str
    reason: str
    status: str
    scheduled_at: str
    disclaimer: str = DISCLAIMER


# ── In-memory store (Phase 2: replace with Supabase) ─────────────────────────
_appointments: list[dict] = []


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    body: BookAppointmentRequest,
    user: PurshUser = Depends(require_pursh_user),
) -> AppointmentResponse:
    """Book an appointment. PHI-SAFE: logs hashed patient ID only."""
    appt = {
        "id": str(uuid4()),
        "patient_id": user.sub,
        "doctor_id": body.doctor_id,
        "appointment_type": body.appointment_type,
        "reason": body.reason,
        "status": "pending",
        "scheduled_at": "2026-06-01T10:00:00Z",
    }
    _appointments.append(appt)
    logger.info(
        "appointment_booked",
        log_id=hash_patient_id(user.sub),  # PHI-SAFE
        appointment_id=appt["id"],
        doctor_id=body.doctor_id,
    )
    return AppointmentResponse(**appt)


@router.get("/mine", response_model=list[AppointmentResponse])
async def my_appointments(user: PurshUser = Depends(require_pursh_user)) -> list[AppointmentResponse]:
    """Return appointments for the authenticated patient. PHI-SAFE."""
    mine = [a for a in _appointments if a["patient_id"] == user.sub]
    logger.info("appointments_listed", log_id=hash_patient_id(user.sub), count=len(mine))
    return [AppointmentResponse(**a) for a in mine]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    user: PurshUser = Depends(require_pursh_user),
) -> AppointmentResponse:
    """Get a specific appointment. Enforces ownership — cannot access other patients' appointments."""
    appt = next((a for a in _appointments if a["id"] == appointment_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    # Authorization check — prevents IDOR (CWE-639)
    if appt["patient_id"] != user.sub and user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied.")
    return AppointmentResponse(**appt)
