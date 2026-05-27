"""AKShare data client wrapping synchronous akshare functions."""

import asyncio
import logging

import pandas as pd

from src.acquisition.client_base import BaseDataClient

logger = logging.getLogger(__name__)


def _to_tx_symbol(code: str) -> str:
    """Convert code to Tencent format: sz000001 or sh600000."""
    code = str(code).zfill(6)
    if code.startswith(("60", "68")):
        return f"sh{code}"
    return f"sz{code}"


def _symbol_to_ts_code(code: str) -> str:
    """Convert code to ts_code with exchange suffix: 000001 → 000001.SZ."""
    code = str(code).zfill(6)
    if code.startswith(("60", "68")):
        return f"{code}.SH"
    elif code.startswith(("00", "30", "002", "003")):
        return f"{code}.SZ"
    elif code.startswith(("8", "4")):
        return f"{code}.BJ"
    return f"{code}.SZ"


class AKShareClient(BaseDataClient):
    """Concrete client for AKShare data sources.

    AKShare functions are synchronous — we call them via asyncio.to_thread().
    Uses Tencent (tx) endpoints as primary since Sina/Eastmoney are unstable.
    """

    ENDPOINT_HANDLERS: dict[str, str] = {
        "stock_info_a_code_name": "_fetch_stock_basic",
        "stock_zh_a_hist": "_fetch_stock_daily",
        "index_zh_a_hist": "_fetch_index_daily",
        "stock_financial_abstract_ths": "_fetch_financial",
    }

    async def fetch(self, **kwargs) -> pd.DataFrame:
        handler_name = self.ENDPOINT_HANDLERS.get(kwargs.get("endpoint", ""))
        if handler_name is None:
            raise ValueError(f"Unknown endpoint for AKShareClient: {kwargs.get('endpoint')}")

        handler = getattr(self, handler_name)
        df = await handler(**kwargs)
        return self._check_empty(df, self.source_code)

    # ── Stock basic ──

    async def _fetch_stock_basic(self, **kwargs) -> pd.DataFrame:
        import akshare as ak

        df = await asyncio.to_thread(ak.stock_info_a_code_name)
        df = df.rename(columns={
            "代码": "symbol", "code": "symbol",
            "名称": "name",
        })
        if "symbol" in df.columns and "name" in df.columns:
            df = df[["symbol", "name"]]
        return df

    # ── Stock daily ──

    async def _fetch_stock_daily(self, **kwargs) -> pd.DataFrame:
        symbol = kwargs.get("symbol", "")
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        adjust = kwargs.get("adjust", "qfq")

        if "." in symbol:
            symbol = symbol.split(".")[0]

        # Try Tencent source first (more reliable), fall back to Sina
        df = await self._fetch_stock_daily_tx(symbol, start_date, end_date)
        if df is None:
            df = await self._fetch_stock_daily_sina(symbol, start_date, end_date, adjust)
        return df

    async def _fetch_stock_daily_tx(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        import akshare as ak

        try:
            tx_sym = _to_tx_symbol(symbol)
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist_tx,
                symbol=tx_sym,
                start_date=start_date,
                end_date=end_date,
            )
            if not df.empty:
                df = df.rename(columns={"date": "trade_date"})
                df["symbol"] = symbol
                # Tencent source missing columns — default to 0 for NOT NULL fields
                for col in ["volume", "amplitude", "pct_change", "change_amount",
                           "turnover_rate", "volume_ratio"]:
                    if col not in df.columns:
                        df[col] = 0
            return df
        except Exception:
            logger.debug("Tencent stock daily failed, trying Sina", exc_info=True)
            return None

    async def _fetch_stock_daily_sina(self, symbol: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
        import akshare as ak

        df = await asyncio.to_thread(
            ak.stock_zh_a_hist,
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        return self._normalize_ohlcv_columns(df)

    # ── Index daily ──

    async def _fetch_index_daily(self, **kwargs) -> pd.DataFrame:
        index_code = kwargs.get("index_code", "")
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")

        # Try Tencent source first
        df = await self._fetch_index_daily_tx(index_code, start_date, end_date)
        if df is None:
            df = await self._fetch_index_daily_sina(index_code, start_date, end_date)
        return df

    async def _fetch_index_daily_tx(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        import akshare as ak

        try:
            code = str(index_code).zfill(6)
            tx_sym = f"sh{code}"  # All indices use sh prefix in Tencent
            df = await asyncio.to_thread(
                ak.stock_zh_index_daily_tx,
                symbol=tx_sym,
                start_date=start_date,
                end_date=end_date,
            )
            if not df.empty:
                df = df.rename(columns={"date": "trade_date"})
                for col in ["volume", "pct_change"]:
                    if col not in df.columns:
                        df[col] = 0
                if "index_code" not in df.columns:
                    df["index_code"] = index_code
                if "index_name" not in df.columns:
                    df["index_name"] = f"指数{index_code}"
            return df
        except Exception:
            logger.debug("Tencent index daily failed, trying Sina", exc_info=True)
            return None

    async def _fetch_index_daily_sina(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        import akshare as ak

        df = await asyncio.to_thread(
            ak.index_zh_a_hist,
            symbol=index_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
        )
        return self._normalize_ohlcv_columns(df)

    # ── Financial ──

    async def _fetch_financial(self, **kwargs) -> pd.DataFrame:
        import akshare as ak

        symbol = kwargs.get("symbol", "")
        if "." in symbol:
            symbol = symbol.split(".")[0]

        df = await asyncio.to_thread(ak.stock_financial_abstract_ths, symbol=symbol)
        if not df.empty:
            df["symbol"] = symbol
            df["ts_code"] = df["symbol"].apply(_symbol_to_ts_code)
        return df

    # ── Helpers ──

    @staticmethod
    def _normalize_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
        column_map = {
            "日期": "trade_date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_change",
            "涨跌额": "change_amount",
            "换手率": "turnover_rate",
            "量比": "volume_ratio",
        }
        existing = {k: v for k, v in column_map.items() if k in df.columns}
        return df.rename(columns=existing)
