"""Initial schema — all 8 tables.

Revision ID: 001
Revises:
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_code", sa.String(64), nullable=False, comment="Unique source identifier"),
        sa.Column("source_name", sa.String(128), nullable=False, comment="Human-readable name"),
        sa.Column("source_type", sa.String(32), nullable=False, comment="akshare / tushare / custom"),
        sa.Column("endpoint", sa.String(256), nullable=False, comment="API function name or URL"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("rate_limit_rps", sa.Float(), nullable=False, server_default=sa.text("2.0")),
        sa.Column("retry_max", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("retry_backoff", sa.Float(), nullable=False, server_default=sa.text("2.0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_code"),
        comment="Data source configurations",
    )
    op.create_index("idx_source_code", "data_sources", ["source_code"])
    op.create_index("idx_is_active", "data_sources", ["is_active"])

    op.create_table(
        "stock_basic",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts_code", sa.String(16), nullable=False, comment="Stock code with exchange suffix"),
        sa.Column("symbol", sa.String(8), nullable=False, comment="Short code without exchange"),
        sa.Column("name", sa.String(64), nullable=False, comment="Stock name in Chinese"),
        sa.Column("exchange", sa.String(8), nullable=False, comment="SZ/SH/BJ"),
        sa.Column("industry_l1", sa.String(64), nullable=True, comment="Shenwan Level 1 industry"),
        sa.Column("industry_l2", sa.String(64), nullable=True, comment="Shenwan Level 2 industry"),
        sa.Column("list_date", sa.Date(), nullable=True, comment="IPO date"),
        sa.Column("delist_date", sa.Date(), nullable=True, comment="Delisting date"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("market_cap", sa.Float(), nullable=True, comment="Total market cap CNY"),
        sa.Column("float_cap", sa.Float(), nullable=True, comment="Free-float market cap CNY"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ts_code"),
        comment="Stock basic information",
    )
    op.create_index("idx_symbol", "stock_basic", ["symbol"])
    op.create_index("idx_exchange", "stock_basic", ["exchange"])
    op.create_index("idx_industry", "stock_basic", ["industry_l1"])
    op.create_index("idx_active", "stock_basic", ["is_active", "list_date"])

    op.create_table(
        "stock_daily_quote",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts_code", sa.String(16), nullable=False, comment="Stock code with exchange suffix"),
        sa.Column("trade_date", sa.Date(), nullable=False, comment="Trading date"),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("pre_close", sa.Float(), nullable=True, comment="Previous close"),
        sa.Column("volume", sa.Integer(), nullable=False, comment="Trading volume shares"),
        sa.Column("amount", sa.Float(), nullable=False, comment="Trading amount CNY"),
        sa.Column("amplitude", sa.Float(), nullable=True, comment="Amplitude %"),
        sa.Column("pct_change", sa.Float(), nullable=True, comment="Price change %"),
        sa.Column("change_amount", sa.Float(), nullable=True, comment="Absolute price change"),
        sa.Column("turnover_rate", sa.Float(), nullable=True, comment="Turnover rate %"),
        sa.Column("volume_ratio", sa.Float(), nullable=True, comment="Volume ratio vs 5-day avg"),
        sa.Column("source_code", sa.String(64), nullable=False, server_default="akshare_stock_daily"),
        sa.Column("sync_batch_id", sa.String(36), nullable=True, comment="UUID of sync batch"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ts_code", "trade_date", name="uk_code_date"),
        comment="A-share daily OHLCV quotes",
    )
    op.create_index("idx_trade_date", "stock_daily_quote", ["trade_date"])
    op.create_index("idx_code_date", "stock_daily_quote", ["ts_code", "trade_date"])

    op.create_table(
        "stock_index_daily",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("index_code", sa.String(16), nullable=False, comment="Index code"),
        sa.Column("index_name", sa.String(64), nullable=False, comment="Index name"),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=True, comment="Total market volume"),
        sa.Column("amount", sa.Float(), nullable=True, comment="Total market amount CNY"),
        sa.Column("pct_change", sa.Float(), nullable=True, comment="Percentage change"),
        sa.Column("source_code", sa.String(64), nullable=False, server_default="akshare_index_daily"),
        sa.Column("sync_batch_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("index_code", "trade_date", name="uk_index_date"),
        comment="Stock index daily data",
    )
    op.create_index("idx_index_trade_date", "stock_index_daily", ["trade_date"])

    op.create_table(
        "stock_financial",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts_code", sa.String(16), nullable=False),
        sa.Column("report_period", sa.String(8), nullable=False, comment="2024Q4"),
        sa.Column("end_date", sa.Date(), nullable=False, comment="Period end date"),
        sa.Column("total_revenue", sa.Float(), nullable=True, comment="Operating revenue CNY"),
        sa.Column("revenue_yoy", sa.Float(), nullable=True, comment="Revenue YoY growth %"),
        sa.Column("net_profit", sa.Float(), nullable=True, comment="Net profit attr to parent"),
        sa.Column("profit_yoy", sa.Float(), nullable=True, comment="Net profit YoY growth %"),
        sa.Column("total_assets", sa.Float(), nullable=True),
        sa.Column("total_liabilities", sa.Float(), nullable=True),
        sa.Column("shareholders_equity", sa.Float(), nullable=True),
        sa.Column("eps", sa.Float(), nullable=True, comment="Earnings per share"),
        sa.Column("bvps", sa.Float(), nullable=True, comment="Book value per share"),
        sa.Column("roe", sa.Float(), nullable=True, comment="Return on equity %"),
        sa.Column("source_code", sa.String(64), nullable=False, server_default="akshare_financial"),
        sa.Column("sync_batch_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ts_code", "report_period", name="uk_code_period"),
        comment="Stock financial statement summaries",
    )
    op.create_index("idx_end_date", "stock_financial", ["end_date"])

    op.create_table(
        "data_sync_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.String(36), nullable=False, comment="UUID for this sync batch"),
        sa.Column("source_code", sa.String(64), nullable=False, comment="Which data source was synced"),
        sa.Column("sync_type", sa.String(32), nullable=False, comment="full / incremental"),
        sa.Column("status", sa.String(16), nullable=False, comment="success / partial / failed"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("inserted_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_rows", sa.Integer(), nullable=False, server_default=sa.text("0"), comment="Rows skipped due to validation"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        comment="Data sync operation logs",
    )
    op.create_index("idx_batch_id", "data_sync_log", ["batch_id"])
    op.create_index("idx_source_code", "data_sync_log", ["source_code"])
    op.create_index("idx_status", "data_sync_log", ["status"])
    op.create_index("idx_started_at", "data_sync_log", ["started_at"])

    op.create_table(
        "monitoring_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("rule_name", sa.String(128), nullable=False),
        sa.Column("target_table", sa.String(64), nullable=False, comment="Table to check"),
        sa.Column("target_column", sa.String(64), nullable=True, comment="Column to check"),
        sa.Column("check_type", sa.String(32), nullable=False),
        sa.Column("threshold_min", sa.Float(), nullable=True),
        sa.Column("threshold_max", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("lookback_hours", sa.Integer(), nullable=False, server_default=sa.text("24")),
        sa.Column("severity", sa.String(16), nullable=False, server_default="warning", comment="info / warning / critical"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code"),
        comment="Monitoring rule definitions",
    )

    op.create_table(
        "monitoring_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("alert_time", sa.DateTime(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="open", comment="open / acknowledged / resolved"),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        comment="Monitoring alert records",
    )
    op.create_index("idx_rule_code", "monitoring_alerts", ["rule_code"])
    op.create_index("idx_alert_time", "monitoring_alerts", ["alert_time"])
    op.create_index("idx_status", "monitoring_alerts", ["status"])


def downgrade() -> None:
    op.drop_table("monitoring_alerts")
    op.drop_table("monitoring_rules")
    op.drop_table("data_sync_log")
    op.drop_table("stock_financial")
    op.drop_table("stock_index_daily")
    op.drop_table("stock_daily_quote")
    op.drop_table("stock_basic")
    op.drop_table("data_sources")
