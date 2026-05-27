"""Web-layer Pydantic schemas."""

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_stocks: int = 0
    total_daily_quotes: int = 0
    total_index_records: int = 0
    total_financials: int = 0
    active_sync_count: int = 0
    alert_count: int = 0


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class StockFilter(BaseModel):
    ts_code: str = ""
    name: str = ""
    exchange: str = ""
    industry: str = ""


class SyncTriggerRequest(BaseModel):
    source_code: str | None = None
    group_name: str | None = None


class AlertFilter(BaseModel):
    severity: str = ""
    status: str = ""
    days: int = 7
