import pathlib
from typing import List

from pydantic import BaseModel, Field, field_validator

TTL = pathlib.Path("core/ontology.ttl").read_text(encoding="utf-8")


def _extract_units(ttl: str):
    units = []
    for line in ttl.splitlines():
        if "rdf:type :AllowedUnit" in line:
            units.append(line.split()[0].strip(":"))
    return sorted(set(units))


ALLOWED_UNITS = _extract_units(TTL)


class MetricIn(BaseModel):
    athlete_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    ts: str
    name: str
    unit: str
    value: float
    coach_id: str

    @field_validator("unit")
    @classmethod
    def unit_allowed(cls, v):
        if v not in ALLOWED_UNITS:
            raise ValueError(f"Unit '{v}' not allowed. Allowed: {ALLOWED_UNITS}")
        return v


class DiffOut(BaseModel):
    added_units: List[str] = []
