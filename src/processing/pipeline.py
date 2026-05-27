"""Processing pipeline — orchestrates validate → clean → transform."""

import pandas as pd

from src.processing.cleaners import (
    add_missing_columns,
    cast_types,
    clip_outliers,
    drop_duplicates,
    fill_missing_values,
    strip_strings,
)
from src.processing.quality import generate_quality_report
from src.processing.transformers import add_exchange, add_ts_code, rename_columns
from src.processing.validators import (
    validate_date_range,
    validate_duplicates,
    validate_no_empty,
    validate_required_columns,
    validate_row_count,
)
from src.core.types_ import DataQualityReport


# Per-source pipeline configurations
PIPELINE_CONFIGS = {
    "akshare_stock_basic": {
        "required_columns": ["symbol", "name"],
        "transform": ["_stock_basic"],
    },
    "akshare_stock_daily": {
        "required_columns": ["open", "close", "high", "low", "volume"],
        "clean": ["_daily_clean"],
        "transform": ["_daily_transform"],
    },
    "akshare_index_daily": {
        "required_columns": ["open", "close", "high", "low"],
        "clean": ["_daily_clean"],
        "transform": ["_index_transform"],
    },
    "akshare_financial": {
        "required_columns": [],
        "clean": ["_financial_clean"],
        "transform": ["_financial_transform"],
    },
}


def run_pipeline(df: pd.DataFrame, source_code: str) -> tuple[pd.DataFrame, DataQualityReport]:
    """Run the processing pipeline for a given source."""
    config = PIPELINE_CONFIGS.get(source_code, {})

    # Validate
    required = config.get("required_columns", [])
    if required:
        result = validate_required_columns(df, required)
        if not result:
            return df, DataQualityReport(source_code=source_code, warnings=result.errors)

    if len(df) == 0:
        return df, DataQualityReport(source_code=source_code, row_count=0)

    # Clean
    for step_name in config.get("clean", []):
        cleaner = globals().get(step_name)
        if cleaner:
            df = cleaner(df)

    # Transform
    for step_name in config.get("transform", []):
        transformer = globals().get(step_name)
        if transformer:
            df = transformer(df)

    # Quality report
    report = generate_quality_report(df, source_code)

    return df, report


# ── Stock basic transforms ──

def _stock_basic(df: pd.DataFrame) -> pd.DataFrame:
    df = add_ts_code(df, symbol_col="symbol")
    df = add_exchange(df)
    df = cast_types(df, {"symbol": "str", "name": "str"})
    df = strip_strings(df)
    return df


# ── Daily OHLCV cleaning + transform ──

def _daily_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = cast_types(df, {
        "open": "float64", "high": "float64", "low": "float64", "close": "float64",
        "volume": "int64", "amount": "float64",
    })
    df = clip_outliers(df, {"pct_change": (-20, 20), "turnover_rate": (0, 100)})
    return df


def _daily_transform(df: pd.DataFrame) -> pd.DataFrame:
    # Add ts_code if only symbol present
    if "symbol" in df.columns and "ts_code" not in df.columns:
        df = add_ts_code(df, symbol_col="symbol")
    df = add_missing_columns(df, {
        "amplitude": None, "pct_change": None, "change_amount": None,
        "turnover_rate": None, "volume_ratio": None,
    })
    return df


def _index_transform(df: pd.DataFrame) -> pd.DataFrame:
    df = add_missing_columns(df, {"pct_change": None, "volume": None, "amount": None})
    return df


# ── Financial cleaning + transform ──

def _financial_clean(df: pd.DataFrame) -> pd.DataFrame:
    from src.processing.transformers import normalize_financial
    df = normalize_financial(df)
    df = _normalize_financial_values(df)
    df = fill_missing_values(df, {
        "total_revenue": 0, "net_profit": 0, "eps": 0, "bvps": 0, "roe": 0,
    })
    return df


def _normalize_financial_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert AKShare financial values with Chinese units to float."""
    import re

    def _parse_num(val) -> float | None:
        if val is None or val == "" or val is False or val == "False":
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val = str(val).strip()
        if val in ("", "-", "--", "N/A", "False"):
            return None
        # Remove commas, spaces
        val = val.replace(",", "").replace(" ", "")
        # Handle percentage
        pct_match = re.match(r"^([\d.]+)\s*%$", val)
        if pct_match:
            return float(pct_match.group(1))
        # Handle Chinese units
        yi_match = re.match(r"^([\d.]+)亿$", val)
        if yi_match:
            return float(yi_match.group(1)) * 1_0000_0000
        wan_match = re.match(r"^([\d.]+)万$", val)
        if wan_match:
            return float(wan_match.group(1)) * 1_0000
        try:
            return float(val)
        except ValueError:
            return None

    numeric_cols = [
        "total_revenue", "revenue_yoy", "net_profit", "profit_yoy",
        "total_assets", "total_liabilities", "shareholders_equity",
        "eps", "bvps", "roe",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(_parse_num)
    return df


def _financial_transform(df: pd.DataFrame) -> pd.DataFrame:
    df = cast_types(df, {
        "total_revenue": "float64", "revenue_yoy": "float64",
        "net_profit": "float64", "profit_yoy": "float64",
        "total_assets": "float64", "total_liabilities": "float64",
        "shareholders_equity": "float64", "eps": "float64", "bvps": "float64", "roe": "float64",
    })
    if "end_date" in df.columns:
        df = cast_types(df, {"end_date": "datetime64[ns]"})
    return df
