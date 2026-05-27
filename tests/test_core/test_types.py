"""Tests for core type definitions."""

from src.core.types_ import DataQualityReport, SyncResult


class TestSyncResult:
    def test_defaults(self):
        r = SyncResult(source_code="test_source", status="success")
        assert r.source_code == "test_source"
        assert r.status == "success"
        assert r.total_rows == 0
        assert r.inserted_rows == 0
        assert r.error_message is None
        assert r.duration_ms == 0

    def test_failed_factory(self):
        r = SyncResult.failed("src", "connection refused")
        assert r.source_code == "src"
        assert r.status == "failed"
        assert r.error_message == "connection refused"

    def test_full_populated(self):
        r = SyncResult(
            source_code="s", status="success", total_rows=100,
            inserted_rows=80, updated_rows=20, skipped_rows=0,
            duration_ms=1500,
        )
        assert r.total_rows == 100
        assert r.inserted_rows == 80
        assert r.updated_rows == 20
        assert r.skipped_rows == 0
        assert r.duration_ms == 1500


class TestDataQualityReport:
    def test_empty_report(self):
        r = DataQualityReport(source_code="s")
        assert r.source_code == "s"
        assert r.row_count == 0
        assert r.null_counts == {}
        assert r.is_healthy is False

    def test_null_rate_empty_df(self):
        r = DataQualityReport(source_code="s", row_count=0)
        assert r.null_rate == {}

    def test_null_rate_calculation(self):
        r = DataQualityReport(
            source_code="s", row_count=100,
            null_counts={"close": 5, "volume": 10},
        )
        assert r.null_rate == {"close": 0.05, "volume": 0.10}

    def test_is_healthy_with_no_warnings(self):
        r = DataQualityReport(source_code="s", row_count=10)
        assert r.is_healthy is True

    def test_is_healthy_with_warnings(self):
        r = DataQualityReport(source_code="s", row_count=10, warnings=["issue"])
        assert r.is_healthy is False

    def test_is_healthy_high_null_rate(self):
        r = DataQualityReport(source_code="s", row_count=100, null_counts={"x": 80})
        assert r.is_healthy is False
