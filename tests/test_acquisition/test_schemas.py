"""Tests for acquisition schemas."""

from src.acquisition.schemas import FetchRequest, FetchResponse, SourceInfo


class TestFetchRequest:
    def test_defaults(self):
        r = FetchRequest(source_code="s")
        assert r.source_code == "s"
        assert r.params == {}

    def test_with_params(self):
        r = FetchRequest(source_code="s", params={"symbol": "000001"})
        assert r.params == {"symbol": "000001"}


class TestFetchResponse:
    def test_fields(self):
        r = FetchResponse(
            source_code="s", row_count=10,
            columns=["a", "b"], duration_ms=150,
        )
        assert r.row_count == 10
        assert r.columns == ["a", "b"]
        assert r.duration_ms == 150


class TestSourceInfo:
    def test_fields(self):
        s = SourceInfo(
            source_code="akshare_stock_daily",
            source_name="AKShare Stock Daily",
            is_active=True,
            rate_limit_rps=2.0,
        )
        assert s.source_code == "akshare_stock_daily"
        assert s.is_active is True
        assert s.rate_limit_rps == 2.0
