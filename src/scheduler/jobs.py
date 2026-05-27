"""Scheduled sync job functions."""

import logging

logger = logging.getLogger(__name__)


def make_sync_stock_basic(sync_service):
    async def job():
        logger.info("Scheduled: sync stock basic")
        result = await sync_service.trigger_sync("akshare_stock_basic")
        logger.info(f"Stock basic sync: {result.status} rows={result.total_rows}")
        return result
    return job


def make_sync_stock_daily(sync_service):
    async def job():
        logger.info("Scheduled: sync stock daily")
        # Sync last 3 days for all tracked stocks
        from datetime import date, timedelta
        from sqlalchemy import text

        end = date.today().strftime("%Y%m%d")
        start = (date.today() - timedelta(days=3)).strftime("%Y%m%d")

        session = sync_service.session_factory()
        try:
            stocks = session.execute(text("SELECT symbol FROM stock_basic WHERE is_active = 1 LIMIT 100")).fetchall()
            results = []
            for (symbol,) in stocks:
                result = await sync_service.trigger_sync(
                    "akshare_stock_daily",
                    endpoint="stock_zh_a_hist",
                    symbol=symbol,
                    start_date=start,
                    end_date=end,
                )
                results.append(result)
            success = sum(1 for r in results if r.status == "success")
            logger.info(f"Stock daily sync done: {success}/{len(results)} success")
        finally:
            session.close()
    return job


def make_sync_indices(sync_service):
    async def job():
        logger.info("Scheduled: sync index daily")
        from datetime import date, timedelta

        end = date.today().strftime("%Y%m%d")
        start = (date.today() - timedelta(days=3)).strftime("%Y%m%d")

        indices = ["000001", "000300", "399001", "399006", "000016", "000688", "000905"]
        results = []
        for idx in indices:
            result = await sync_service.trigger_sync(
                "akshare_index_daily",
                endpoint="index_zh_a_hist",
                index_code=idx,
                start_date=start,
                end_date=end,
            )
            results.append(result)
        success = sum(1 for r in results if r.status == "success")
        logger.info(f"Index daily sync done: {success}/{len(results)} success")
    return job


def make_sync_financials(sync_service):
    async def job():
        logger.info("Scheduled: sync financials")
        from sqlalchemy import text

        session = sync_service.session_factory()
        try:
            stocks = session.execute(
                text("SELECT symbol FROM stock_basic WHERE is_active = 1 LIMIT 50")
            ).fetchall()
            results = []
            for (symbol,) in stocks:
                result = await sync_service.trigger_sync(
                    "akshare_financial",
                    endpoint="stock_financial_abstract_ths",
                    symbol=symbol,
                )
                results.append(result)
            success = sum(1 for r in results if r.status == "success")
            logger.info(f"Financial sync done: {success}/{len(results)} success")
        finally:
            session.close()
    return job
