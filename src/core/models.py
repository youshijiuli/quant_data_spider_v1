"""SQLAlchemy ORM models for the quant data warehouse."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="Unique source identifier")
    source_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="Human-readable name")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="akshare / tushare / custom")
    endpoint: Mapped[str] = mapped_column(String(256), nullable=False, comment="API function name or URL")
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rate_limit_rps: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    retry_max: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_backoff: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_source_code", "source_code"),
        Index("idx_is_active", "is_active"),
        {"comment": "Data source configurations"},
    )


class StockBasic(Base):
    __tablename__ = "stock_basic"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, comment="Stock code with exchange suffix")
    symbol: Mapped[str] = mapped_column(String(8), nullable=False, comment="Short code without exchange")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="Stock name in Chinese")
    exchange: Mapped[str] = mapped_column(String(8), nullable=False, comment="SZ/SH/BJ")
    industry_l1: Mapped[str | None] = mapped_column(String(64), comment="Shenwan Level 1 industry")
    industry_l2: Mapped[str | None] = mapped_column(String(64), comment="Shenwan Level 2 industry")
    list_date: Mapped[str | None] = mapped_column(Date, comment="IPO date")
    delist_date: Mapped[str | None] = mapped_column(Date, comment="Delisting date")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    market_cap: Mapped[float | None] = mapped_column(Float, comment="Total market cap CNY")
    float_cap: Mapped[float | None] = mapped_column(Float, comment="Free-float market cap CNY")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_symbol", "symbol"),
        Index("idx_exchange", "exchange"),
        Index("idx_industry", "industry_l1"),
        Index("idx_active", "is_active", "list_date"),
        {"comment": "Stock basic information"},
    )


class StockDailyQuote(Base):
    __tablename__ = "stock_daily_quote"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, comment="Stock code with exchange suffix")
    trade_date: Mapped[str] = mapped_column(Date, nullable=False, comment="Trading date")
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    pre_close: Mapped[float | None] = mapped_column(Float, comment="Previous close")
    volume: Mapped[int] = mapped_column(Integer, nullable=False, comment="Trading volume shares")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="Trading amount CNY")
    amplitude: Mapped[float | None] = mapped_column(Float, comment="Amplitude %")
    pct_change: Mapped[float | None] = mapped_column(Float, comment="Price change %")
    change_amount: Mapped[float | None] = mapped_column(Float, comment="Absolute price change")
    turnover_rate: Mapped[float | None] = mapped_column(Float, comment="Turnover rate %")
    volume_ratio: Mapped[float | None] = mapped_column(Float, comment="Volume ratio vs 5-day avg")
    source_code: Mapped[str] = mapped_column(String(64), default="akshare_stock_daily", nullable=False)
    sync_batch_id: Mapped[str | None] = mapped_column(String(36), comment="UUID of sync batch")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uk_code_date"),
        Index("idx_trade_date", "trade_date"),
        Index("idx_code_date", "ts_code", "trade_date"),
        {"comment": "A-share daily OHLCV quotes"},
    )


class StockIndexDaily(Base):
    __tablename__ = "stock_index_daily"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    index_code: Mapped[str] = mapped_column(String(16), nullable=False, comment="Index code")
    index_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="Index name")
    trade_date: Mapped[str] = mapped_column(Date, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(Integer, comment="Total market volume")
    amount: Mapped[float | None] = mapped_column(Float, comment="Total market amount CNY")
    pct_change: Mapped[float | None] = mapped_column(Float, comment="Percentage change")
    source_code: Mapped[str] = mapped_column(String(64), default="akshare_index_daily", nullable=False)
    sync_batch_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("index_code", "trade_date", name="uk_index_date"),
        Index("idx_index_trade_date", "trade_date"),
        {"comment": "Stock index daily data"},
    )


class StockFinancial(Base):
    __tablename__ = "stock_financial"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False)
    report_period: Mapped[str] = mapped_column(String(8), nullable=False, comment="2024Q4")
    end_date: Mapped[str] = mapped_column(Date, nullable=False, comment="Period end date")
    total_revenue: Mapped[float | None] = mapped_column(Float, comment="Operating revenue CNY")
    revenue_yoy: Mapped[float | None] = mapped_column(Float, comment="Revenue YoY growth %")
    net_profit: Mapped[float | None] = mapped_column(Float, comment="Net profit attr to parent")
    profit_yoy: Mapped[float | None] = mapped_column(Float, comment="Net profit YoY growth %")
    total_assets: Mapped[float | None] = mapped_column(Float)
    total_liabilities: Mapped[float | None] = mapped_column(Float)
    shareholders_equity: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Float, comment="Earnings per share")
    bvps: Mapped[float | None] = mapped_column(Float, comment="Book value per share")
    roe: Mapped[float | None] = mapped_column(Float, comment="Return on equity %")
    source_code: Mapped[str] = mapped_column(String(64), default="akshare_financial", nullable=False)
    sync_batch_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("ts_code", "report_period", name="uk_code_period"),
        Index("idx_end_date", "end_date"),
        {"comment": "Stock financial statement summaries"},
    )


class DataSyncLog(Base):
    __tablename__ = "data_sync_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="UUID for this sync batch")
    source_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="Which data source was synced")
    sync_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="full / incremental")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="success / partial / failed")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    inserted_rows: Mapped[int] = mapped_column(Integer, default=0)
    updated_rows: Mapped[int] = mapped_column(Integer, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0, comment="Rows skipped due to validation")
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        Index("idx_batch_id", "batch_id"),
        Index("idx_source_code", "source_code"),
        Index("idx_status", "status"),
        Index("idx_started_at", "started_at"),
        {"comment": "Data sync operation logs"},
    )


class MonitoringRule(Base):
    __tablename__ = "monitoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_table: Mapped[str] = mapped_column(String(64), nullable=False, comment="Table to check")
    target_column: Mapped[str | None] = mapped_column(String(64), comment="Column to check")
    check_type: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_min: Mapped[float | None] = mapped_column(Float)
    threshold_max: Mapped[float | None] = mapped_column(Float)
    threshold_value: Mapped[float | None] = mapped_column(Float)
    lookback_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="warning", nullable=False, comment="info / warning / critical")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = {"comment": "Monitoring rule definitions"}


class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    alert_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actual_value: Mapped[float | None] = mapped_column(Float)
    threshold_value: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False, comment="open / acknowledged / resolved")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        Index("idx_rule_code", "rule_code"),
        Index("idx_alert_time", "alert_time"),
        Index("idx_status", "status"),
        {"comment": "Monitoring alert records"},
    )
