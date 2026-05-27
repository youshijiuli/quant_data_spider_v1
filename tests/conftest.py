"""Pytest fixtures shared across all test modules."""

import sys
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def sqlite_engine():
    """Per-test SQLite engine with StaticPool — all connections share the same in-memory DB."""
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from src.core.models import Base
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sqlite_session(sqlite_engine):
    """Per-test SQLite session."""
    SessionLocal = sessionmaker(bind=sqlite_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sqlite_session_factory(sqlite_engine):
    """Factory that creates a fresh session each call."""
    SessionLocal = sessionmaker(bind=sqlite_engine)
    return SessionLocal


@pytest.fixture
def sample_stock_df():
    """Minimal stock basic DataFrame."""
    return pd.DataFrame([
        {"symbol": "000001", "name": "平安银行", "industry_l1": "银行", "list_date": "19910403"},
        {"symbol": "000002", "name": "万科A", "industry_l1": "房地产", "list_date": "19910129"},
        {"symbol": "600519", "name": "贵州茅台", "industry_l1": "食品饮料", "list_date": "20010827"},
    ])


@pytest.fixture
def sample_daily_df():
    """Minimal stock daily OHLCV DataFrame."""
    return pd.DataFrame([
        {"symbol": "000001", "date": "2024-01-31", "open": 10.5, "close": 10.8, "high": 11.0, "low": 10.3, "volume": 5000000, "amount": 53000000},
        {"symbol": "000001", "date": "2024-01-30", "open": 10.3, "close": 10.5, "high": 10.7, "low": 10.2, "volume": 4500000, "amount": 47500000},
    ])


@pytest.fixture
def sample_index_df():
    """Minimal index daily DataFrame."""
    return pd.DataFrame([
        {"index_code": "000001", "index_name": "上证指数", "date": "2024-01-31", "open": 2850.0, "close": 2830.0, "high": 2870.0, "low": 2820.0, "amount": 350000000000},
        {"index_code": "399001", "index_name": "深证成指", "date": "2024-01-31", "open": 8900.0, "close": 8850.0, "high": 8950.0, "low": 8800.0, "amount": 420000000000},
    ])


@pytest.fixture
def sample_financial_df():
    """Minimal financial DataFrame with AKShare Chinese column names."""
    return pd.DataFrame([
        {
            "报告期": "2024Q4",
            "营业总收入": 10000000000.0,
            "净利润": 2000000000.0,
            "资产总计": 50000000000.0,
            "负债合计": 30000000000.0,
            "股东权益合计": 20000000000.0,
            "每股收益": 2.5,
            "每股净资产": 25.0,
            "净资产收益率": 10.0,
        },
    ])
