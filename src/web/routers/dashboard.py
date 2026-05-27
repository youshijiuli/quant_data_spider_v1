"""Dashboard home page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from src.web.dependencies import get_db

router = APIRouter(tags=["dashboard"])

TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    db = next(get_db(request))
    try:
        stats = _get_stats(db)
    finally:
        db.close()

    template = _load_template("pages/dashboard.html")
    return template.render(request=request, stats=stats)


def _get_stats(db):
    def count(table: str) -> int:
        row = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
        return row[0] if row else 0

    def active_alerts() -> int:
        row = db.execute(text("SELECT COUNT(*) FROM monitoring_alerts WHERE status='open'")).fetchone()
        return row[0] if row else 0

    def recent_syncs(limit: int = 10):
        rows = db.execute(
            text("SELECT source_code, status, total_rows, inserted_rows, started_at, finished_at "
                 "FROM data_sync_log ORDER BY started_at DESC LIMIT :limit"),
            {"limit": limit},
        ).fetchall()
        return rows

    def active_sources_count() -> int:
        row = db.execute(text("SELECT COUNT(*) FROM data_sources WHERE is_active=1")).fetchone()
        return row[0] if row else 0

    return {
        "total_stocks": count("stock_basic"),
        "total_daily_quotes": count("stock_daily_quote"),
        "total_index_records": count("stock_index_daily"),
        "total_financials": count("stock_financial"),
        "alert_count": active_alerts(),
        "active_sources_count": active_sources_count(),
        "recent_syncs": recent_syncs(),
    }


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)
