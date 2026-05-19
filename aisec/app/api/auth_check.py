from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.models import AuthenticatedUser
from app.auth.oidc import require_authenticated_user

router = APIRouter(prefix="/api/v1", tags=["auth"])


class MeResponse(BaseModel):
    sub: str
    email: str
    role: str


@router.get("/me", response_model=MeResponse)
async def me(
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> MeResponse:
    """
    Returns the authenticated user's identity claims.
    Requires a valid Supabase Bearer JWT.
    Used to verify login redirect works end-to-end.
    """
    return MeResponse(sub=user.sub, email=user.email, role=user.role)
