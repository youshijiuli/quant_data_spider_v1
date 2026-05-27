"""Tests for monitoring evaluator."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import text

from src.core.models import DataSyncLog, StockDailyQuote
from src.monitoring.dispatcher import AlertDispatcher
from src.monitoring.evaluator import MonitoringEvaluator


class TestMonitoringEvaluator:
    def test_init(self, sqlite_session_factory):
        evaluator = MonitoringEvaluator(sqlite_session_factory)
        assert evaluator.session_factory is sqlite_session_factory
        assert isinstance(evaluator.dispatcher, AlertDispatcher)

    def test_run_no_rules(self, sqlite_session_factory):
        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        assert alerts == []

    def test_null_rate_check(self, sqlite_session_factory):
        # Seed a rule and data
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
            "check_type, threshold_max, lookback_hours, severity, is_active) "
            "VALUES ('test_null', 'Test null', 'stock_basic', 'name', 'null_rate', 0.5, 1000, 'warning', 1)"
        ))
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        # No data in stock_basic -> rate is 0, not breached
        assert len(alerts) == 0

    def test_row_count_check_breached(self, sqlite_session_factory):
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
            "check_type, threshold_min, lookback_hours, severity, is_active) "
            "VALUES ('test_rows', 'Test rows', 'stock_basic', '', 'row_count', 100, 1000, 'critical', 1)"
        ))
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"

    def test_stale_data_no_data(self, sqlite_session_factory):
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
            "check_type, lookback_hours, severity, is_active) "
            "VALUES ('test_stale', 'Test stale', 'stock_basic', 'list_date', 'stale_data', 24, 'warning', 1)"
        ))
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        # No dates in stock_basic -> should alert
        assert len(alerts) == 1

    def test_unknown_check_type(self, sqlite_session_factory):
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
            "check_type, lookback_hours, severity, is_active) "
            "VALUES ('test_unknown', 'Unknown', 'stock_basic', '', 'bogus', 24, 'info', 1)"
        ))
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        assert alerts == []

    def test_value_range_breached(self, sqlite_session_factory):
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
            "check_type, threshold_value, lookback_hours, severity, is_active) "
            "VALUES ('test_vrange', 'Value range', 'data_sync_log', 'status', 'value_range', 0, 1000, 'critical', 1)"
        ))
        # Insert a failed sync log
        log = DataSyncLog(
            batch_id="test-uuid",
            source_code="test_source",
            sync_type="full",
            status="failed",
            started_at=datetime.utcnow(),
        )
        session.add(log)
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        assert len(alerts) >= 1

    def test_value_range_not_breached(self, sqlite_session_factory):
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
            "check_type, threshold_value, lookback_hours, severity, is_active) "
            "VALUES ('test_vrange2', 'Value range ok', 'data_sync_log', 'status', 'value_range', 10, 1000, 'warning', 1)"
        ))
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        assert len(alerts) == 0

    def test_duplicate_rate_no_breach(self, sqlite_session_factory):
        session = sqlite_session_factory()
        session.execute(text(
            "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, "
            "check_type, threshold_max, lookback_hours, severity, is_active) "
            "VALUES ('test_dup', 'Duplicate check', 'stock_daily_quote', 'duplicate_rate', 0.5, 1000, 'warning', 1)"
        ))
        # Insert unique rows (unique constraint prevents actual duplicates)
        q1 = StockDailyQuote(
            ts_code="000001.SZ", trade_date=date(2024, 1, 31),
            open=10.5, high=11.0, low=10.3, close=10.8,
            volume=5000000, amount=53000000,
        )
        q2 = StockDailyQuote(
            ts_code="000002.SZ", trade_date=date(2024, 1, 31),
            open=15.0, high=16.0, low=14.5, close=15.5,
            volume=3000000, amount=46000000,
        )
        session.add_all([q1, q2])
        session.commit()
        session.close()

        evaluator = MonitoringEvaluator(sqlite_session_factory)
        alerts = evaluator.run_all_checks()
        # No duplicates found, no breach
        assert len(alerts) == 0
