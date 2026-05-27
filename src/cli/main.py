"""CLI entry point for Quant Data Spider."""

import asyncio
from pathlib import Path

import typer

app = typer.Typer(name="quant", help="Quant Data Spider CLI")


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Start the web dashboard."""
    import uvicorn

    from config.settings import settings
    from src.core.database import create_all_tables, init_db
    from src.web.app import create_app
    from src.web.config import WebSettings

    web_settings = WebSettings()
    engine, SessionLocal = init_db(settings.db.url)
    create_all_tables(engine)
    app_instance = create_app(engine, SessionLocal)

    uvicorn.run(
        app_instance,
        host=host,
        port=port,
        reload=reload,
        log_level=settings.app.log_level.lower(),
    )


@app.command()
def sync(
    source: str = typer.Option("akshare_stock_basic", help="Source code to sync"),
    symbol: str = typer.Option("", help="Stock symbol (for daily/financial)"),
    start: str = typer.Option("", help="Start date YYYYMMDD"),
    end: str = typer.Option("", help="End date YYYYMMDD"),
    index: str = typer.Option("", help="Index code (for index daily)"),
):
    """Trigger a data sync from the command line."""
    from config.settings import settings
    from src.core.database import create_all_tables, init_db
    from src.acquisition.source_registry import SourceRegistry
    from src.storage.sync_service import SyncService

    engine, SessionLocal = init_db(settings.db.url)
    create_all_tables(engine)
    registry = SourceRegistry()
    svc = SyncService(SessionLocal, registry)

    params = {}
    if symbol:
        params["symbol"] = symbol
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    if index:
        params["index_code"] = index

    async def _run():
        result = await svc.trigger_sync(source, **params)
        print(f"Source: {result.source_code}")
        print(f"Status: {result.status}")
        print(f"Rows: {result.total_rows} | Inserted: {result.inserted_rows} | Skipped: {result.skipped_rows}")
        print(f"Duration: {result.duration_ms}ms")
        if result.error_message:
            print(f"Error: {result.error_message}")

    asyncio.run(_run())


@app.command()
def schedule():
    """Start the scheduler daemon."""
    from config.settings import settings
    from src.core.database import create_all_tables, init_db
    from src.acquisition.source_registry import SourceRegistry
    from src.storage.sync_service import SyncService
    from src.scheduler.scheduler import QuantScheduler
    from src.monitoring.seed import seed_monitoring_rules
    from src.scheduler.jobs import (
        make_sync_financials,
        make_sync_indices,
        make_sync_stock_basic,
        make_sync_stock_daily,
    )
    from src.scheduler.monitoring_job import make_monitoring_job

    engine, SessionLocal = init_db(settings.db.url)
    create_all_tables(engine)
    registry = SourceRegistry()
    svc = SyncService(SessionLocal, registry)

    seed_monitoring_rules(SessionLocal)

    sched = QuantScheduler()
    sched.register("sync_all_stocks", make_sync_stock_daily(svc))
    sched.register("sync_indices", make_sync_indices(svc))
    sched.register("sync_financials", make_sync_financials(svc))
    sched.register("sync_stock_basic", make_sync_stock_basic(svc))
    sched.register("run_monitoring", make_monitoring_job(SessionLocal))
    sched.load_and_start()

    import signal

    def _shutdown(sig, frame):
        print("\nShutting down scheduler...")
        sched.shutdown()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("Scheduler running. Press Ctrl+C to stop.")
    try:
        signal.pause()
    except AttributeError:
        import time
        while True:
            time.sleep(1)


if __name__ == "__main__":
    app()
