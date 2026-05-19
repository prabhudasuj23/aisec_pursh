"""
Pursh — Symptom checker endpoint (AI-3, Phase 10).

Phase 1: stub that returns static guidance.
Phase 10: wires DeepSeek for symptom analysis with PHI redaction layer.

This endpoint is intentionally the most security-sensitive AI surface:
- LLM01: Prompt injection via symptom field
- LLM06: PHI-leak risk if patient identifiers reach the LLM
- LLM09: Overreliance risk — patients must not treat output as medical advice

DISCLAIMER: NOT medical advice. This is a demonstration project.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from pursh.backend.auth.supabase import PurshUser, require_pursh_user
from pursh.backend.core.logging import get_logger, hash_patient_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/symptoms", tags=["symptoms"])

MEDICAL_DISCLAIMER = (
    "⚠️ NOT MEDICAL ADVICE. This is a demonstration project using synthetic data. "
    "Always consult a qualified healthcare professional. "
    "If you are experiencing a medical emergency, call 911 immediately."
)

EMERGENCY_KEYWORDS = {
    "chest pain", "can't breathe", "cannot breathe", "heart attack",
    "stroke", "unconscious", "severe bleeding", "overdose", "suicidal",
}


class SymptomCheckRequest(BaseModel):
    symptoms: str   # free text — primary prompt injection attack surface

    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Please describe your symptoms in at least 3 characters.")
        if len(v) > 500:
            raise ValueError("Symptom description must be under 500 characters.")
        return v.strip()


class SymptomCheckResponse(BaseModel):
    suggested_specialty: str
    urgency: str              # "routine" | "soon" | "emergency"
    guidance: str
    disclaimer: str = MEDICAL_DISCLAIMER
    ai_powered: bool = False  # True once Phase 10 DeepSeek integration ships


def _check_emergency(symptoms: str) -> bool:
    lower = symptoms.lower()
    return any(kw in lower for kw in EMERGENCY_KEYWORDS)


@router.post("/check", response_model=SymptomCheckResponse)
async def check_symptoms(
    body: SymptomCheckRequest,
    user: PurshUser = Depends(require_pursh_user),
) -> SymptomCheckResponse:
    """
    Symptom triage — Phase 1 returns static guidance.
    Phase 10: DeepSeek with PHI-redaction layer + prompt-injection test suite.

    PHI-SAFE: symptom text is never logged, only the hashed user ID.
    """
    logger.info("symptom_check_requested", log_id=hash_patient_id(user.sub))
    # PHI-SAFE: do NOT log body.symptoms — it may contain PHI

    # Emergency override — always show emergency guidance for urgent keywords
    if _check_emergency(body.symptoms):
        return SymptomCheckResponse(
            suggested_specialty="Emergency Medicine",
            urgency="emergency",
            guidance=(
                "Your symptoms may require immediate medical attention. "
                "Please call 911 or go to the nearest emergency room. "
                "Do not wait for a telehealth appointment."
            ),
        )

    # Phase 1: static rule-based routing (Phase 10 replaces with DeepSeek)
    lower = body.symptoms.lower()
    if any(kw in lower for kw in ("skin", "rash", "acne", "hair", "scalp")):
        specialty, guidance = "Dermatology", "Consider consulting a dermatologist for skin concerns."
    elif any(kw in lower for kw in ("anxious", "depressed", "stress", "sleep", "mood")):
        specialty, guidance = "Mental Health", "A mental health professional can provide support."
    elif any(kw in lower for kw in ("erection", "libido", "sexual")):
        specialty, guidance = "Sexual Health", "Our sexual health specialists can help."
    else:
        specialty, guidance = "General Practice", "A general practitioner can evaluate your symptoms."

    return SymptomCheckResponse(
        suggested_specialty=specialty,
        urgency="routine",
        guidance=guidance,
    )
