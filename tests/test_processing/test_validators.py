"""Tests for DataFrame validators."""

import pandas as pd
import pytest

from src.processing.validators import (
    validate_date_range,
    validate_duplicates,
    validate_no_empty,
    validate_required_columns,
    validate_row_count,
)


class TestValidateRequiredColumns:
    def test_all_present(self):
        df = pd.DataFrame(columns=["open", "close", "high", "low"])
        r = validate_required_columns(df, ["open", "close"])
        assert r.valid is True

    def test_missing_column(self):
        df = pd.DataFrame(columns=["open"])
        r = validate_required_columns(df, ["open", "close"])
        assert r.valid is False
        assert "close" in r.errors[0]

    def test_empty_df(self):
        df = pd.DataFrame()
        r = validate_required_columns(df, ["any"])
        assert r.valid is False


class TestValidateNoEmpty:
    def test_no_nulls(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        r = validate_no_empty(df, ["a"])
        assert r.valid is True

    def test_has_nulls(self):
        df = pd.DataFrame({"a": [1, None, 3]})
        r = validate_no_empty(df, ["a"])
        assert r.valid is False
        assert "null values" in r.errors[0]

    def test_column_not_present(self):
        df = pd.DataFrame({"a": [1, 2]})
        r = validate_no_empty(df, ["b"])
        assert r.valid is True


class TestValidateRowCount:
    def test_enough_rows(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        r = validate_row_count(df, min_rows=2)
        assert r.valid is True

    def test_too_few_rows(self):
        df = pd.DataFrame({"a": [1]})
        r = validate_row_count(df, min_rows=5)
        assert r.valid is False

    def test_default_min(self):
        df = pd.DataFrame({"a": [1]})
        r = validate_row_count(df)
        assert r.valid is True


class TestValidateDateRange:
    def test_valid_dates(self):
        df = pd.DataFrame({"date": ["2024-01-01", "2024-06-15"]})
        r = validate_date_range(df, "date", max_future_days=365)
        assert r.valid is True

    def test_column_missing(self):
        df = pd.DataFrame({"a": [1]})
        r = validate_date_range(df, "date")
        assert r.valid is True


class TestValidateDuplicates:
    def test_no_duplicates(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        r = validate_duplicates(df, ["a", "b"])
        assert r.valid is True

    def test_has_duplicates(self):
        df = pd.DataFrame({"a": [1, 1, 3], "b": [4, 4, 6]})
        r = validate_duplicates(df, ["a", "b"])
        assert r.valid is False
        assert "duplicate" in r.errors[0]
