"""DataFrame cleaning operations."""

import pandas as pd


def drop_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Remove duplicate rows."""
    return df.drop_duplicates(subset=subset).copy()


def fill_missing_values(df: pd.DataFrame, fill_map: dict[str, object]) -> pd.DataFrame:
    """Fill NaN values in specified columns with given defaults."""
    df = df.copy()
    for col, value in fill_map.items():
        if col in df.columns:
            df[col] = df[col].fillna(value)
    return df


def clip_outliers(df: pd.DataFrame, col_ranges: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """Clip numeric column values to [min, max] range."""
    df = df.copy()
    for col, (lo, hi) in col_ranges.items():
        if col in df.columns:
            df[col] = df[col].clip(lower=lo, upper=hi)
    return df


def cast_types(df: pd.DataFrame, type_map: dict[str, str]) -> pd.DataFrame:
    """Cast columns to specified dtypes (e.g. 'int64', 'float64', 'datetime64[ns]')."""
    df = df.copy()
    for col, dtype in type_map.items():
        if col in df.columns:
            try:
                if dtype == "datetime64[ns]":
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                else:
                    df[col] = df[col].astype(dtype)
            except (ValueError, TypeError):
                pass
    return df


def strip_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from all string columns."""
    df = df.copy()
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    return df


def add_missing_columns(df: pd.DataFrame, columns: dict[str, object]) -> pd.DataFrame:
    """Add missing columns with default values."""
    df = df.copy()
    for col, default in columns.items():
        if col not in df.columns:
            df[col] = default
    return df
