"""Tests for quality report generation."""

import numpy as np
import pandas as pd

from src.processing.quality import generate_quality_report


class TestGenerateQualityReport:
    def test_empty_df(self):
        report = generate_quality_report(pd.DataFrame(), "test_source")
        assert report.source_code == "test_source"
        assert report.row_count == 0
        assert "Empty" in report.warnings[0]

    def test_basic_stats(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        report = generate_quality_report(df, "src")
        assert report.row_count == 3
        assert report.duplicate_count == 0

    def test_detects_nulls(self):
        df = pd.DataFrame({"a": [1, np.nan, np.nan, 4, 5, 6, 7, 8, 9, 10, 11]})
        report = generate_quality_report(df, "src")
        assert report.null_counts["a"] == 2
        assert any("null rate" in w for w in report.warnings)

    def test_detects_duplicates(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        report = generate_quality_report(df, "src")
        assert report.duplicate_count == 1

    def test_detects_outliers(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]})
        report = generate_quality_report(df, "src")
        assert "x" in report.outlier_counts
        assert report.outlier_counts["x"] > 0
