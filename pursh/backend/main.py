"""
Pursh — synthetic telehealth app backend.
FastAPI + Supabase Auth + RLS-enforced Postgres.

DISCLAIMER: Demonstration project only. Not a real medical service.
All data is synthetically generated. Do not enter real symptoms or PHI.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pursh.backend.api import patients, doctors, appointments, symptoms
from pursh.backend.core.config import get_settings
from pursh.backend.core.logging import CorrelationIdMiddleware, configure_logging


DISCLAIMER = (
    "Demonstration project — not a real medical service. "
    "Synthetic test data only. This is a security-engineering portfolio project."
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Pursh API",
        description=f"Synthetic telehealth demo app. **{DISCLAIMER}**",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(patients.router)
    app.include_router(doctors.router)
    app.include_router(appointments.router)
    app.include_router(symptoms.router)

    return app


app = create_app()
