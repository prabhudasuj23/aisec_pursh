from pydantic import BaseModel, EmailStr


class AuthenticatedUser(BaseModel):
    """Decoded and validated Supabase JWT claims."""

    sub: str          # Supabase user UUID
    email: EmailStr
    role: str = "authenticated"
    aud: str = "authenticated"
