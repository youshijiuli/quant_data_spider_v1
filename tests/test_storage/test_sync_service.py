"""Tests for SyncService and _dataframe_to_rows."""

import uuid

import numpy as np
import pandas as pd
import pytest

from src.core.models import StockBasic, StockDailyQuote
from src.storage.sync_service import (
    SOURCE_DEFAULTS,
    SOURCE_MODEL_MAP,
    SyncService,
    _dataframe_to_rows,
)


class TestDataframeToRows:
    def test_basic_conversion(self):
        df = pd.DataFrame([
            {"ts_code": "000001.SZ", "trade_date": "2024-01-31", "open": 10.5, "close": 10.8,
             "high": 11.0, "low": 10.3, "volume": 5000000, "amount": 53000000},
        ])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockDailyQuote, "akshare_stock_daily", batch_id)

        assert len(rows) == 1
        assert rows[0]["ts_code"] == "000001.SZ"
        assert rows[0]["trade_date"] == "2024-01-31"
        assert rows[0]["source_code"] == "akshare_stock_daily"
        assert rows[0]["sync_batch_id"] == batch_id

    def test_adds_source_code_when_missing(self):
        df = pd.DataFrame([
            {"ts_code": "000002.SZ", "trade_date": "2024-02-01", "open": 15.0, "close": 15.5,
             "high": 16.0, "low": 14.5, "volume": 3000000, "amount": 46000000},
        ])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockDailyQuote, "akshare_stock_daily", batch_id)

        assert rows[0]["source_code"] == "akshare_stock_daily"

    def test_keeps_existing_source_code(self):
        df = pd.DataFrame([
            {"ts_code": "000003.SZ", "trade_date": "2024-03-01", "open": 20.0, "close": 19.5,
             "high": 21.0, "low": 19.0, "volume": 2000000, "amount": 40000000,
             "source_code": "custom_source"},
        ])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockDailyQuote, "akshare_stock_daily", batch_id)

        assert rows[0]["source_code"] == "custom_source"

    def test_filters_extra_columns(self):
        df = pd.DataFrame([
            {"ts_code": "000004.SZ", "trade_date": "2024-04-01", "open": 8.0, "close": 8.5,
             "high": 9.0, "low": 7.5, "volume": 1000000, "amount": 8500000,
             "extra_col": "should_be_removed", "another_extra": 123},
        ])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockDailyQuote, "akshare_stock_daily", batch_id)

        assert "extra_col" not in rows[0]
        assert "another_extra" not in rows[0]

    def test_nan_to_none(self):
        df = pd.DataFrame([
            {"ts_code": "000005.SZ", "trade_date": "2024-05-01", "open": 10.0, "close": 10.5,
             "high": 11.0, "low": 9.5, "volume": 500000, "amount": np.nan},
        ])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockDailyQuote, "akshare_stock_daily", batch_id)

        assert rows[0]["amount"] is None

    def test_does_not_add_sync_batch_id_for_model_without_it(self):
        """StockBasic model does not have sync_batch_id column."""
        df = pd.DataFrame([
            {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "exchange": "SZ"},
        ])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockBasic, "akshare_stock_basic", batch_id)

        assert "sync_batch_id" not in rows[0]
        assert "source_code" not in rows[0]

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["ts_code", "trade_date", "open", "close", "high", "low", "volume", "amount"])
        batch_id = str(uuid.uuid4())
        rows = _dataframe_to_rows(df, StockDailyQuote, "akshare_stock_daily", batch_id)

        assert rows == []


class TestSourceMappings:
    def test_model_map_has_all_sources(self):
        assert "akshare_stock_basic" in SOURCE_MODEL_MAP
        assert "akshare_stock_daily" in SOURCE_MODEL_MAP
        assert "akshare_index_daily" in SOURCE_MODEL_MAP
        assert "akshare_financial" in SOURCE_MODEL_MAP

    def test_model_map_stock_basic(self):
        model, unique_cols = SOURCE_MODEL_MAP["akshare_stock_basic"]
        assert model == StockBasic
        assert unique_cols == ["ts_code"]

    def test_model_map_stock_daily(self):
        model, unique_cols = SOURCE_MODEL_MAP["akshare_stock_daily"]
        assert model == StockDailyQuote
        assert unique_cols == ["ts_code", "trade_date"]

    def test_source_defaults_have_all_sources(self):
        for key in SOURCE_MODEL_MAP:
            assert key in SOURCE_DEFAULTS

    def test_source_defaults_stock_basic(self):
        defaults = SOURCE_DEFAULTS["akshare_stock_basic"]
        assert defaults["endpoint"] == "stock_info_a_code_name"


class TestSyncService:
    def test_init_with_default_registry(self, sqlite_session_factory):
        svc = SyncService(sqlite_session_factory)
        assert svc.session_factory is sqlite_session_factory
        assert svc.registry is not None
