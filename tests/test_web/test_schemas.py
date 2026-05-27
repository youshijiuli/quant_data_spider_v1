"""Tests for web schemas."""

from src.web.schemas import (
    AlertFilter,
    DashboardStats,
    PaginationParams,
    StockFilter,
    SyncTriggerRequest,
)


class TestDashboardStats:
    def test_default_values(self):
        stats = DashboardStats()
        assert stats.total_stocks == 0
        assert stats.total_daily_quotes == 0
        assert stats.alert_count == 0

    def test_full_populated(self):
        stats = DashboardStats(
            total_stocks=5000, total_daily_quotes=100000,
            total_index_records=5000, total_financials=20000,
            active_sync_count=10, alert_count=3,
        )
        assert stats.total_stocks == 5000
        assert stats.alert_count == 3


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.page == 1
        assert p.page_size == 20

    def test_custom(self):
        p = PaginationParams(page=3, page_size=50)
        assert p.page == 3
        assert p.page_size == 50


class TestStockFilter:
    def test_defaults(self):
        f = StockFilter()
        assert f.ts_code == ""
        assert f.name == ""
        assert f.exchange == ""

    def test_with_values(self):
        f = StockFilter(ts_code="000001", name="平安", exchange="SZ")
        assert f.ts_code == "000001"
        assert f.name == "平安"


class TestSyncTriggerRequest:
    def test_defaults(self):
        r = SyncTriggerRequest()
        assert r.source_code is None
        assert r.group_name is None

    def test_with_source(self):
        r = SyncTriggerRequest(source_code="akshare_stock_daily")
        assert r.source_code == "akshare_stock_daily"


class TestAlertFilter:
    def test_defaults(self):
        f = AlertFilter()
        assert f.severity == ""
        assert f.status == ""
        assert f.days == 7

    def test_with_values(self):
        f = AlertFilter(severity="critical", status="open", days=3)
        assert f.severity == "critical"
        assert f.status == "open"
