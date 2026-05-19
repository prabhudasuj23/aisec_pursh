"""
Pursh structured logging.
Same structlog pattern as AISec but with pursh-specific context fields.
PHI rule: never log patient_id_value — only hashed IDs.
"""

import hashlib
import logging
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from pursh.backend.core.config import get_settings


def hash_patient_id(patient_id: str) -> str:
    """Return a one-way hash of a patient ID safe for logging. Never log raw patient IDs."""
    return hashlib.sha256(patient_id.encode()).hexdigest()[:16]


def configure_logging() -> None:
    settings = get_settings()
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer: Any = (
        structlog.dev.ConsoleRenderer()
        if settings.environment == "local"
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            service="pursh",
            method=request.method,
            path=request.url.path,
        )
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response
