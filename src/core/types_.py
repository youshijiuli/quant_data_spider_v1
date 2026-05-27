"""Shared type definitions and dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SyncResult:
    source_code: str
    status: str
    total_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    error_message: str | None = None
    duration_ms: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None

    @classmethod
    def failed(cls, source_code: str, error_message: str) -> "SyncResult":
        return cls(source_code=source_code, status="failed", error_message=error_message)


@dataclass
class DataQualityReport:
    source_code: str
    row_count: int = 0
    null_counts: dict[str, int] = field(default_factory=dict)
    outlier_counts: dict[str, int] = field(default_factory=dict)
    duplicate_count: int = 0
    invalid_rows: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def null_rate(self) -> dict[str, float]:
        if self.row_count == 0:
            return {}
        return {col: count / self.row_count for col, count in self.null_counts.items()}

    @property
    def is_healthy(self) -> bool:
        if self.row_count == 0:
            return False
        return max(self.null_rate.values(), default=0) < 0.05 and not self.warnings
