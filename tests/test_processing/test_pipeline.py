"""Tests for processing pipeline."""

import pandas as pd
import pytest

from src.processing.pipeline import (
    _daily_clean,
    _financial_clean,
    _financial_transform,
    _normalize_financial_values,
    _stock_basic,
    run_pipeline,
)


class TestStockBasicPipeline:
    def test_adds_ts_code_and_exchange(self):
        df = pd.DataFrame([
            {"symbol": "000001", "name": "平安银行"},
            {"symbol": "600519", "name": "贵州茅台"},
        ])
        result, _ = run_pipeline(df, "akshare_stock_basic")
        assert "ts_code" in result.columns
        assert "exchange" in result.columns
        assert result.loc[0, "ts_code"] == "000001.SZ"
        assert result.loc[1, "ts_code"] == "600519.SH"

    def test_missing_required_columns(self, sample_daily_df):
        df = pd.DataFrame({"wrong": [1]})
        _, report = run_pipeline(df, "akshare_stock_basic")
        assert len(report.warnings) > 0

    def test_empty_df(self):
        df = pd.DataFrame()
        _, report = run_pipeline(df, "akshare_stock_daily")
        assert report.row_count == 0


class TestDailyPipeline:
    def test_cleans_types(self, sample_daily_df):
        result, report = run_pipeline(sample_daily_df, "akshare_stock_daily")
        assert result["open"].dtype == "float64"
        assert result["volume"].dtype == "int64"
        assert report.row_count == 2

    def test_adds_missing_columns(self):
        df = pd.DataFrame([
            {"symbol": "000001", "date": "2024-01-31", "open": 10.5, "close": 10.8, "high": 11.0, "low": 10.3, "volume": 100, "amount": 1000},
        ])
        result, _ = run_pipeline(df, "akshare_stock_daily")
        assert "pct_change" in result.columns
        assert "turnover_rate" in result.columns


class TestFinancialPipeline:
    def test_normalize(self):
        df = pd.DataFrame([{
            "报告期": "2024Q4", "营业总收入": 1e10, "净利润": 2e9,
        }])
        result, _ = run_pipeline(df, "akshare_financial")
        assert "total_revenue" in result.columns

    def test_empty_required(self):
        df = pd.DataFrame({"a": [1]})
        result, _ = run_pipeline(df, "akshare_financial")
        assert len(result) == 1  # passes through


class TestNormalizeFinancialValues:
    def test_parses_yi(self):
        df = pd.DataFrame({"total_revenue": ["1.5亿"]})
        result = _normalize_financial_values(df)
        assert result.loc[0, "total_revenue"] == pytest.approx(150000000.0)

    def test_parses_wan(self):
        df = pd.DataFrame({"net_profit": ["500万"]})
        result = _normalize_financial_values(df)
        assert result.loc[0, "net_profit"] == pytest.approx(5000000.0)

    def test_parses_percent(self):
        df = pd.DataFrame({"revenue_yoy": ["15.5%"]})
        result = _normalize_financial_values(df)
        assert result.loc[0, "revenue_yoy"] == pytest.approx(15.5)

    def test_handles_none(self):
        df = pd.DataFrame({"total_revenue": [None]})
        result = _normalize_financial_values(df)
        assert result.loc[0, "total_revenue"] is None

    def test_handles_plain_float(self):
        df = pd.DataFrame({"total_revenue": [12345.67]})
        result = _normalize_financial_values(df)
        assert result.loc[0, "total_revenue"] == pytest.approx(12345.67)
