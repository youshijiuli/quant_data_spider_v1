"""Tests for core constants and enums."""

from src.core.constants import (
    AlertSeverity,
    AlertStatus,
    CheckType,
    SyncStatus,
    SyncType,
    TIMEZONE_ASIA_SHANGHAI,
)


class TestSyncStatus:
    def test_values(self):
        assert SyncStatus.SUCCESS == "success"
        assert SyncStatus.PARTIAL == "partial"
        assert SyncStatus.FAILED == "failed"

    def test_value_attribute(self):
        assert SyncStatus.SUCCESS.value == "success"


class TestSyncType:
    def test_values(self):
        assert SyncType.FULL == "full"
        assert SyncType.INCREMENTAL == "incremental"


class TestAlertSeverity:
    def test_values(self):
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.CRITICAL == "critical"


class TestAlertStatus:
    def test_values(self):
        assert AlertStatus.OPEN == "open"
        assert AlertStatus.ACKNOWLEDGED == "acknowledged"
        assert AlertStatus.RESOLVED == "resolved"


class TestCheckType:
    def test_values(self):
        assert CheckType.NULL_RATE == "null_rate"
        assert CheckType.STALE_DATA == "stale_data"
        assert CheckType.VALUE_RANGE == "value_range"
        assert CheckType.ROW_COUNT == "row_count"
        assert CheckType.DUPLICATE_RATE == "duplicate_rate"


class TestConstants:
    def test_timezone(self):
        assert TIMEZONE_ASIA_SHANGHAI == "Asia/Shanghai"
