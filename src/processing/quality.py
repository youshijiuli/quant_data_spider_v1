"""Data quality report generation."""

import pandas as pd

from src.core.types_ import DataQualityReport


def generate_quality_report(df: pd.DataFrame, source_code: str) -> DataQualityReport:
    """Generate a DataQualityReport from a DataFrame."""
    if df.empty:
        return DataQualityReport(source_code=source_code, warnings=["Empty DataFrame"])

    # Null counts per column
    null_counts = {col: int(df[col].isna().sum()) for col in df.columns}

    # Duplicate count
    duplicate_count = int(df.duplicated().sum())

    # Outlier detection (IQR method for numeric columns)
    outlier_counts: dict[str, int] = {}
    for col in df.select_dtypes(include=["number"]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
            outlier_counts[col] = int(len(outliers))

    # Warnings
    warnings = []
    for col, count in null_counts.items():
        if count > 0:
            null_rate = count / len(df)
            if null_rate > 0.1:
                warnings.append(f"{col}: {null_rate:.1%} null rate")

    if duplicate_count > 0:
        warnings.append(f"{duplicate_count} duplicate rows detected")

    return DataQualityReport(
        source_code=source_code,
        row_count=len(df),
        null_counts=null_counts,
        outlier_counts=outlier_counts,
        duplicate_count=duplicate_count,
        invalid_rows=0,
        warnings=warnings,
    )
