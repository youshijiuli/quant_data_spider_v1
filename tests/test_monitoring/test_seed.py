"""Tests for seed monitoring rules."""

from sqlalchemy import text

from src.monitoring.seed import seed_monitoring_rules


class TestSeedMonitoringRules:
    def test_seeds_from_toml(self, sqlite_session_factory):
        count = seed_monitoring_rules(sqlite_session_factory)
        assert count >= 8

        session = sqlite_session_factory()
        try:
            rows = session.execute(
                text("SELECT rule_code FROM monitoring_rules WHERE is_active = 1")
            ).fetchall()
            codes = {r.rule_code for r in rows}
            assert "daily_null_rate" in codes
            assert "daily_row_count" in codes
            assert "daily_stale" in codes
            assert "index_null_rate" in codes
            assert "index_stale" in codes
            assert "financial_push" in codes
            assert "sync_failure" in codes
            assert "duplicate_daily" in codes
        finally:
            session.close()

    def test_idempotent(self, sqlite_session_factory):
        count1 = seed_monitoring_rules(sqlite_session_factory)
        count2 = seed_monitoring_rules(sqlite_session_factory)
        assert count1 == count2
