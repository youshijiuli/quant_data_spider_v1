"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.web.config import WebSettings
from src.web.routers import (
    api,
    charts,
    dashboard,
    data,
    monitoring,
    quality,
    scheduler,
    sync,
)

web_settings = WebSettings()


def create_app(engine, session_factory):
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Quant Data Spider", version="0.1.0")

    import logging

    from src.acquisition.source_registry import SourceRegistry
    from src.monitoring.seed import seed_monitoring_rules
    from src.scheduler.jobs import (
        make_sync_financials,
        make_sync_indices,
        make_sync_stock_basic,
        make_sync_stock_daily,
    )
    from src.scheduler.monitoring_job import make_monitoring_job
    from src.scheduler.scheduler import QuantScheduler
    from src.storage.sync_service import SyncService

    logger = logging.getLogger(__name__)

    app.state.engine = engine
    app.state.session_factory = session_factory

    registry = SourceRegistry()
    svc = SyncService(session_factory, registry)
    app.state.sync_service = svc

    quant_scheduler = QuantScheduler()
    quant_scheduler.register("sync_all_stocks", make_sync_stock_daily(svc))
    quant_scheduler.register("sync_indices", make_sync_indices(svc))
    quant_scheduler.register("sync_financials", make_sync_financials(svc))
    quant_scheduler.register("sync_stock_basic", make_sync_stock_basic(svc))
    quant_scheduler.register("run_monitoring", make_monitoring_job(session_factory))

    @app.on_event("startup")
    async def _start_scheduler():
        seed_monitoring_rules(session_factory)
        quant_scheduler.load_and_start()
        logger.info("Scheduler started with monitoring rules seeded")

    @app.on_event("shutdown")
    async def _stop_scheduler():
        quant_scheduler.shutdown()
        logger.info("Scheduler stopped")

    app.state.scheduler = quant_scheduler

    app.mount("/static", StaticFiles(directory=str(web_settings.static_dir)), name="static")

    app.include_router(dashboard.router)
    app.include_router(data.router, prefix="/data")
    app.include_router(charts.router, prefix="/charts")
    app.include_router(sync.router, prefix="/sync")
    app.include_router(monitoring.router, prefix="/monitoring")
    app.include_router(quality.router, prefix="/quality")
    app.include_router(scheduler.router, prefix="/scheduler")
    app.include_router(api.router, prefix="/api")

    return app
