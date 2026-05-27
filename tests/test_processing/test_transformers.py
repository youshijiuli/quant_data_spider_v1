"""Tests for DataFrame transformers."""

import pandas as pd

from src.processing.transformers import (
    add_exchange,
    add_ts_code,
    format_date,
    normalize_financial,
    rename_columns,
)


class TestRenameColumns:
    def test_renames_existing(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        result = rename_columns(df, {"a": "x", "b": "y"})
        assert list(result.columns) == ["x", "y"]

    def test_ignores_missing(self):
        df = pd.DataFrame({"a": [1]})
        result = rename_columns(df, {"a": "x", "c": "z"})
        assert list(result.columns) == ["x"]


class TestAddTsCode:
    def test_shanghai_prefix(self):
        df = pd.DataFrame({"symbol": ["600519", "688981"]})
        result = add_ts_code(df, "symbol")
        assert result.loc[0, "ts_code"] == "600519.SH"
        assert result.loc[1, "ts_code"] == "688981.SH"

    def test_shenzhen_prefix(self):
        df = pd.DataFrame({"symbol": ["000001", "300750"]})
        result = add_ts_code(df, "symbol")
        assert result.loc[0, "ts_code"] == "000001.SZ"
        assert result.loc[1, "ts_code"] == "300750.SZ"

    def test_beijing_prefix(self):
        df = pd.DataFrame({"symbol": ["830799", "430047"]})
        result = add_ts_code(df, "symbol")
        assert result.loc[0, "ts_code"] == "830799.BJ"

    def test_no_symbol_column(self):
        df = pd.DataFrame({"a": [1]})
        result = add_ts_code(df, "symbol")
        assert "ts_code" not in result.columns


class TestAddExchange:
    def test_extracts_exchange(self):
        df = pd.DataFrame({"ts_code": ["000001.SZ", "600519.SH", "830799.BJ"]})
        result = add_exchange(df)
        assert result.loc[0, "exchange"] == "SZ"
        assert result.loc[1, "exchange"] == "SH"
        assert result.loc[2, "exchange"] == "BJ"


class TestFormatDate:
    def test_formats_dates(self):
        df = pd.DataFrame({"date": ["2024-01-31", "2024-02-01"]})
        result = format_date(df, ["date"])
        assert result.loc[0, "date"] == "20240131"
        assert result.loc[1, "date"] == "20240201"


class TestNormalizeFinancial:
    def test_renames_chinese_columns(self):
        df = pd.DataFrame({
            "报告期": ["2024Q4"], "营业总收入": [1e10], "净利润": [2e9],
            "资产总计": [5e10], "负债合计": [3e10], "股东权益合计": [2e10],
        })
        result = normalize_financial(df)
        assert "report_period" in result.columns
        assert "total_revenue" in result.columns
        assert "net_profit" in result.columns
        assert "total_assets" in result.columns

    def test_derives_end_date(self):
        df = pd.DataFrame({"报告期": ["2024Q4"]})
        result = normalize_financial(df)
        assert "end_date" in result.columns
        assert "report_period" in result.columns
