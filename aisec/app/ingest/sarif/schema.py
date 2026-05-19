"""
SARIF 2.1.0 schema validator.

We validate the essential structure at the API boundary before handing off to
the normalizer. Strict full-schema validation would reject too many real-world
scanner outputs (many scanners produce non-standard SARIF). We validate the
minimum required fields and fail loudly on those.

Why validate at the boundary?
CWE-20 (Improper Input Validation): accepting malformed scanner output silently
can cause silent data loss, incorrect compliance mapping, or DB constraint errors.
The circuit breaker in the ingest queue escalates after 3 consecutive failures.
"""

from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class SarifRegion(BaseModel):
    startLine: int | None = None
    endLine: int | None = None
    snippet: dict[str, Any] | None = None


class SarifArtifactLocation(BaseModel):
    uri: str | None = None


class SarifPhysicalLocation(BaseModel):
    artifactLocation: SarifArtifactLocation | None = None
    region: SarifRegion | None = None


class SarifLocation(BaseModel):
    physicalLocation: SarifPhysicalLocation | None = None


class SarifMessage(BaseModel):
    text: str | None = None
    markdown: str | None = None


class SarifResult(BaseModel):
    ruleId: str | None = None
    level: str | None = None
    message: SarifMessage | None = None
    locations: list[SarifLocation] = []

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str | None) -> str | None:
        valid = {"error", "warning", "note", "none", None}
        if v not in valid:
            return "warning"  # coerce unknown levels, not reject
        return v


class SarifDriver(BaseModel):
    name: str
    rules: list[dict[str, Any]] = []


class SarifTool(BaseModel):
    driver: SarifDriver


class SarifRun(BaseModel):
    tool: SarifTool
    results: list[SarifResult] = []


class SarifDocument(BaseModel):
    version: str
    runs: list[SarifRun]

    @model_validator(mode="before")
    @classmethod
    def check_sarif_version(cls, values: Any) -> Any:
        version = values.get("version", "")
        if not str(version).startswith("2.1"):
            raise ValueError(f"Unsupported SARIF version: {version}. Expected 2.1.x")
        return values
