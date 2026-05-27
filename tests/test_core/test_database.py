"""Tests for database module and models."""

from datetime import date

import pytest
from sqlalchemy import inspect, text

from src.core.database import create_db_engine, create_session_factory, get_db_session, init_db


class TestDatabaseCreate:
    def test_create_all_tables(self, sqlite_engine):
        inspector = inspect(sqlite_engine)
        tables = inspector.get_table_names()
        assert "stock_basic" in tables
        assert "stock_daily_quote" in tables
        assert "stock_index_daily" in tables
        assert "stock_financial" in tables
        assert "data_sources" in tables
        assert "data_sync_log" in tables
        assert "monitoring_rules" in tables
        assert "monitoring_alerts" in tables

    def test_create_session_factory(self, sqlite_engine):
        factory = create_session_factory(sqlite_engine)
        session = factory()
        assert session is not None
        assert session.is_active
        session.close()


class TestStockBasicModel:
    def test_create_and_read(self, sqlite_session):
        from src.core.models import StockBasic

        s = StockBasic(
            ts_code="000001.SZ", symbol="000001", name="平安银行",
            exchange="SZ", industry_l1="银行", list_date=date(1991, 4, 3),
        )
        sqlite_session.add(s)
        sqlite_session.commit()

        rows = sqlite_session.query(StockBasic).filter_by(symbol="000001").all()
        assert len(rows) == 1
        assert rows[0].name == "平安银行"
        assert rows[0].exchange == "SZ"


class TestStockDailyQuoteModel:
    def test_create_and_read(self, sqlite_session):
        from datetime import date
        from src.core.models import StockDailyQuote

        q = StockDailyQuote(
            ts_code="000001.SZ", trade_date=date(2024, 1, 31),
            open=10.5, high=11.0, low=10.3, close=10.8,
            volume=5000000, amount=53000000,
        )
        sqlite_session.add(q)
        sqlite_session.commit()

        rows = sqlite_session.query(StockDailyQuote).filter_by(ts_code="000001.SZ").all()
        assert len(rows) == 1
        assert rows[0].close == 10.8


class TestMonitoringRuleModel:
    def test_create_and_read(self, sqlite_session):
        from src.core.models import MonitoringRule

        r = MonitoringRule(
            rule_code="test_rule", rule_name="Test rule",
            target_table="stock_daily_quote", target_column="close",
            check_type="null_rate", threshold_max=0.05,
            lookback_hours=24, severity="warning",
        )
        sqlite_session.add(r)
        sqlite_session.commit()

        rows = sqlite_session.query(MonitoringRule).filter_by(rule_code="test_rule").all()
        assert len(rows) == 1
        assert rows[0].check_type == "null_rate"


class TestMonitoringAlertModel:
    def test_create_and_read(self, sqlite_session):
        from datetime import datetime
        from src.core.models import MonitoringAlert

        a = MonitoringAlert(
            rule_code="test_rule", alert_time=datetime.utcnow(),
            severity="warning", title="Test alert",
            message="Something is wrong", status="open",
        )
        sqlite_session.add(a)
        sqlite_session.commit()

        rows = sqlite_session.query(MonitoringAlert).filter_by(rule_code="test_rule").all()
        assert len(rows) == 1
        assert rows[0].status == "open"


class TestDatabaseModule:
    def test_create_db_engine_calls_create_engine(self, mocker):
        mock_create = mocker.patch("src.core.database.create_engine")
        create_db_engine("mysql+pymysql://user:pass@localhost/db")
        mock_create.assert_called_once()

    def test_init_db_returns_engine_and_factory(self, mocker):
        mock_engine = mocker.MagicMock()
        mock_create = mocker.patch("src.core.database.create_db_engine", return_value=mock_engine)
        mock_sf = mocker.patch("src.core.database.create_session_factory", return_value=lambda: mocker.MagicMock())

        engine, factory = init_db("mysql+pymysql://user:pass@localhost/db")
        mock_create.assert_called_once()
        assert engine is mock_engine
        assert factory is not None

    def test_get_db_session_context_manager(self, sqlite_engine):
        factory = create_session_factory(sqlite_engine)
        gen = get_db_session(factory)
        session = next(gen)
        try:
            assert session.is_active
        finally:
            try:
                next(gen)
            except StopIteration:
                pass


class TestDataSyncLogModel:
    def test_create_and_read(self, sqlite_session):
        from datetime import datetime
        from src.core.models import DataSyncLog

        log = DataSyncLog(
            batch_id="uuid-123", source_code="akshare_stock_daily",
            sync_type="incremental", status="success",
            total_rows=100, inserted_rows=90, updated_rows=10,
            started_at=datetime.utcnow(),
        )
        sqlite_session.add(log)
        sqlite_session.commit()

        rows = sqlite_session.query(DataSyncLog).filter_by(batch_id="uuid-123").all()
        assert len(rows) == 1
        assert rows[0].status == "success"
