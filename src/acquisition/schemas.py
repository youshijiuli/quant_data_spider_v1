"""Pydantic schemas for the acquisition layer."""

from pydantic import BaseModel


class FetchRequest(BaseModel):
    source_code: str
    params: dict = {}


class FetchResponse(BaseModel):
    source_code: str
    row_count: int
    columns: list[str]
    duration_ms: int


class SourceInfo(BaseModel):
    source_code: str
    source_name: str
    is_active: bool
    rate_limit_rps: float
