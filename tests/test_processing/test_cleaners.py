"""Tests for DataFrame cleaners."""

import numpy as np
import pandas as pd

from src.processing.cleaners import (
    add_missing_columns,
    cast_types,
    clip_outliers,
    drop_duplicates,
    fill_missing_values,
    strip_strings,
)


class TestDropDuplicates:
    def test_removes_dups(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        result = drop_duplicates(df, subset=["a", "b"])
        assert len(result) == 2

    def test_preserves_data(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = drop_duplicates(df)
        assert len(result) == 2


class TestFillMissingValues:
    def test_fills_nan(self):
        df = pd.DataFrame({"a": [1, np.nan], "b": ["x", np.nan]})
        result = fill_missing_values(df, {"a": 0, "b": "N/A"})
        assert result.loc[1, "a"] == 0
        assert result.loc[1, "b"] == "N/A"

    def test_ignores_unknown_column(self):
        df = pd.DataFrame({"a": [1]})
        result = fill_missing_values(df, {"b": 0})
        assert "b" not in result.columns


class TestClipOutliers:
    def test_clips_values(self):
        df = pd.DataFrame({"x": [-10, 0, 5, 100]})
        result = clip_outliers(df, {"x": (0, 10)})
        assert result["x"].min() == 0
        assert result["x"].max() == 10

    def test_ignores_unknown_column(self):
        df = pd.DataFrame({"a": [1]})
        result = clip_outliers(df, {"b": (0, 1)})
        assert len(result.columns) == 1


class TestCastTypes:
    def test_cast_to_int(self):
        df = pd.DataFrame({"a": ["1", "2", "3"]})
        result = cast_types(df, {"a": "int64"})
        assert result["a"].dtype == "int64"

    def test_cast_to_float(self):
        df = pd.DataFrame({"a": ["1.5", "2.5"]})
        result = cast_types(df, {"a": "float64"})
        assert result["a"].dtype == "float64"

    def test_cast_datetime(self):
        df = pd.DataFrame({"d": ["2024-01-01"]})
        result = cast_types(df, {"d": "datetime64[ns]"})
        assert pd.api.types.is_datetime64_any_dtype(result["d"])


class TestStripStrings:
    def test_strips_whitespace(self):
        df = pd.DataFrame({"name": ["  foo ", " bar"]})
        result = strip_strings(df)
        assert result.loc[0, "name"] == "foo"
        assert result.loc[1, "name"] == "bar"


class TestAddMissingColumns:
    def test_adds_missing(self):
        df = pd.DataFrame({"a": [1]})
        result = add_missing_columns(df, {"b": 0, "c": "x"})
        assert result.loc[0, "b"] == 0
        assert result.loc[0, "c"] == "x"

    def test_keeps_existing(self):
        df = pd.DataFrame({"a": [99]})
        result = add_missing_columns(df, {"a": 0})
        assert result.loc[0, "a"] == 99
