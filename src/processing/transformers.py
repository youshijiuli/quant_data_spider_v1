"""DataFrame transformation operations — column mapping and derived fields."""

import pandas as pd


def rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Rename columns using a mapping dict."""
    existing = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=existing)


def add_ts_code(df: pd.DataFrame, symbol_col: str = "symbol") -> pd.DataFrame:
    """Add ts_code column with exchange suffix based on stock code prefix."""
    df = df.copy()
    if symbol_col not in df.columns:
        return df

    def _suffix(code: str) -> str:
        code = str(code).zfill(6)
        if code.startswith(("60", "68")):
            return f"{code}.SH"
        elif code.startswith(("00", "30", "002", "003")):
            return f"{code}.SZ"
        elif code.startswith(("8", "4")):
            return f"{code}.BJ"
        return f"{code}.SZ"

    df["ts_code"] = df[symbol_col].apply(_suffix)
    return df


def add_exchange(df: pd.DataFrame, ts_code_col: str = "ts_code") -> pd.DataFrame:
    """Extract exchange from ts_code suffix."""
    df = df.copy()
    if ts_code_col in df.columns:
        df["exchange"] = df[ts_code_col].str.extract(r"\.(S[HZ]|BJ)$", expand=False).fillna("SZ")
    return df


def format_date(df: pd.DataFrame, date_cols: list[str]) -> pd.DataFrame:
    """Normalize date columns to date strings (YYYYMMDD)."""
    df = df.copy()
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y%m%d")
    return df


def normalize_financial(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize financial DataFrame column names from AKShare format."""
    col_map = {
        "报告期": "report_period",
        "营业收入": "total_revenue",
        "营业总收入": "total_revenue",
        "营业收入同比增长": "revenue_yoy",
        "营业总收入同比增长": "revenue_yoy",
        "净利润": "net_profit",
        "净利润同比增长": "profit_yoy",
        "资产总计": "total_assets",
        "负债合计": "total_liabilities",
        "股东权益合计": "shareholders_equity",
        "每股收益": "eps",
        "每股净资产": "bvps",
        "净资产收益率": "roe",
        "截止日期": "end_date",
    }
    existing = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=existing)
    # Derive end_date from report_period if missing
    if "end_date" not in df.columns and "report_period" in df.columns:
        df["end_date"] = pd.to_datetime(df["report_period"], errors="coerce")
    return df
