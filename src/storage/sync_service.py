"""Sync service orchestrating acquire → process → store → log."""

import time
import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from src.acquisition.source_registry import SourceRegistry
from src.core.models import (
    DataSyncLog,
    StockBasic,
    StockDailyQuote,
    StockFinancial,
    StockIndexDaily,
)
from src.core.types_ import SyncResult
from src.processing.pipeline import run_pipeline
from src.storage.repository import BaseRepository

SOURCE_MODEL_MAP: dict[str, tuple[type, list[str]]] = {
    "akshare_stock_basic": (StockBasic, ["ts_code"]),
    "akshare_stock_daily": (StockDailyQuote, ["ts_code", "trade_date"]),
    "akshare_index_daily": (StockIndexDaily, ["index_code", "trade_date"]),
    "akshare_financial": (StockFinancial, ["ts_code", "report_period"]),
}

SOURCE_DEFAULTS: dict[str, dict] = {
    "akshare_stock_basic": {"endpoint": "stock_info_a_code_name"},
    "akshare_stock_daily": {"endpoint": "stock_zh_a_hist", "period": "daily", "adjust": "qfq"},
    "akshare_index_daily": {"endpoint": "index_zh_a_hist"},
    "akshare_financial": {"endpoint": "stock_financial_abstract_ths"},
}


class SyncService:
    """Orchestrates the full acquire→process→store cycle with logging."""

    def __init__(self, session_factory, registry: SourceRegistry | None = None):
        self.session_factory = session_factory
        self.registry = registry or SourceRegistry()

    async def trigger_sync(self, source_code: str, **params) -> SyncResult:
        batch_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        t0 = time.perf_counter()

        result = SyncResult(
            source_code=source_code,
            status="running",
            started_at=started_at,
        )

        session = self.session_factory()
        try:
            # 1 — Acquire
            client = self.registry.get_client(source_code)
            fetch_params = {**SOURCE_DEFAULTS.get(source_code, {}), **params}
            df = await client.fetch(**fetch_params)

            # 2 — Process
            df, quality_report = run_pipeline(df, source_code)
            result.skipped_rows = quality_report.invalid_rows

            if df.empty:
                result.status = "success"
                result.finished_at = datetime.utcnow()
                result.duration_ms = int((time.perf_counter() - t0) * 1000)
                self._write_log(session, batch_id, source_code, result)
                session.commit()
                return result

            # 3 — Store
            model_info = SOURCE_MODEL_MAP.get(source_code)
            if model_info is None:
                raise ValueError(f"No model mapping for source: {source_code}")

            model_class, unique_cols = model_info
            rows = _dataframe_to_rows(df, model_class, source_code, batch_id)
            repo = BaseRepository(session, model_class)
            rowcount = repo.bulk_upsert(rows, unique_cols)

            result.total_rows = len(rows)
            result.inserted_rows = rowcount
            result.status = "success"

        except Exception as exc:
            result.status = "failed"
            result.error_message = str(exc)
            session.rollback()
        else:
            session.commit()
        finally:
            result.finished_at = datetime.utcnow()
            result.duration_ms = int((time.perf_counter() - t0) * 1000)
            # Write log within a fresh session if the original failed
            self._write_log(session, batch_id, source_code, result)
            try:
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()

        return result

    def _write_log(self, session: Session, batch_id: str, source_code: str, result: SyncResult) -> None:
        log = DataSyncLog(
            batch_id=batch_id,
            source_code=source_code,
            sync_type="full",
            status=result.status,
            total_rows=result.total_rows,
            inserted_rows=result.inserted_rows,
            updated_rows=result.updated_rows,
            skipped_rows=result.skipped_rows,
            error_message=result.error_message,
            duration_ms=result.duration_ms,
            started_at=result.started_at,
            finished_at=result.finished_at,
        )
        session.add(log)


def _dataframe_to_rows(df: pd.DataFrame, model_class: type, source_code: str, batch_id: str) -> list[dict]:
    """Convert DataFrame to list of dicts for DB insert, normalizing columns."""
    model_cols = {c.name for c in model_class.__table__.columns}

    # Add tracking columns only if the model has them
    if "source_code" in df.columns:
        pass  # already present
    elif "source_code" in model_cols:
        df = df.copy()
        df["source_code"] = source_code

    if "sync_batch_id" in model_cols and "sync_batch_id" not in df.columns:
        df = df.copy()
        df["sync_batch_id"] = batch_id

    # Keep only columns that exist in the model
    valid_cols = [c for c in df.columns if c in model_cols]
    rows = df[valid_cols].to_dict(orient="records")

    for r in rows:
        for k, v in list(r.items()):
            if pd.isna(v):
                r[k] = None
    return rows
