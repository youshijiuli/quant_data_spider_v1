"""DataFrame validation rules."""

import pandas as pd


class ValidationResult:
    def __init__(self, valid: bool = True, errors: list[str] | None = None):
        self.valid = valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.valid}, errors={self.errors})"


def validate_required_columns(df: pd.DataFrame, required: list[str]) -> ValidationResult:
    """Check that all required columns are present."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        return ValidationResult(False, [f"Missing columns: {missing}"])
    return ValidationResult(True)


def validate_no_empty(df: pd.DataFrame, columns: list[str]) -> ValidationResult:
    """Check that specified columns have no empty/null values."""
    errors = []
    for col in columns:
        if col in df.columns and df[col].isna().any():
            null_count = df[col].isna().sum()
            errors.append(f"Column '{col}' has {null_count} null values")
    return ValidationResult(len(errors) == 0, errors)


def validate_row_count(df: pd.DataFrame, min_rows: int = 1) -> ValidationResult:
    """Check that the DataFrame has at least min_rows."""
    if len(df) < min_rows:
        return ValidationResult(False, [f"Row count {len(df)} < {min_rows}"])
    return ValidationResult(True)


def validate_date_range(df: pd.DataFrame, date_col: str, max_future_days: int = 1) -> ValidationResult:
    """Check that dates are not in the far future."""
    if date_col not in df.columns:
        return ValidationResult(True)
    today = pd.Timestamp.now().normalize()
    future_threshold = today + pd.Timedelta(days=max_future_days)
    future_rows = df[pd.to_datetime(df[date_col]) > future_threshold]
    if len(future_rows) > 0:
        return ValidationResult(False, [f"{len(future_rows)} rows have future dates"])
    return ValidationResult(True)


def validate_duplicates(df: pd.DataFrame, key_cols: list[str]) -> ValidationResult:
    """Check for duplicate rows on key columns."""
    dup_count = df.duplicated(subset=key_cols).sum()
    if dup_count > 0:
        return ValidationResult(False, [f"{dup_count} duplicate rows on {key_cols}"])
    return ValidationResult(True)
