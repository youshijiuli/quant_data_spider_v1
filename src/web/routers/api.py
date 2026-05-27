"""JSON API routes for programmatic access and frontend JS."""

from datetime import datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.web.dependencies import get_db

router = APIRouter(tags=["api"])


@router.get("/health")
async def health_check(request: Request):
    db = next(get_db(request))
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    finally:
        db.close()

    return JSONResponse({
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    })


@router.get("/stats")
async def api_stats(request: Request):
    db = next(get_db(request))
    try:
        stocks = db.execute(text("SELECT COUNT(*) FROM stock_basic")).fetchone()[0]
        daily = db.execute(text("SELECT COUNT(*) FROM stock_daily_quote")).fetchone()[0]
        indexes = db.execute(text("SELECT COUNT(*) FROM stock_index_daily")).fetchone()[0]
        financials = db.execute(text("SELECT COUNT(*) FROM stock_financial")).fetchone()[0]
        alert = db.execute(text("SELECT COUNT(*) FROM monitoring_alerts WHERE status='open'")).fetchone()[0]
    finally:
        db.close()

    return JSONResponse({
        "stocks": stocks,
        "daily_quotes": daily,
        "index_records": indexes,
        "financials": financials,
        "open_alerts": alert,
    })


@router.get("/search/stock")
async def search_stock(request: Request, q: str = Query("", min_length=1)):
    db = next(get_db(request))
    try:
        rows = db.execute(
            text("SELECT ts_code, name FROM stock_basic WHERE ts_code LIKE :q OR name LIKE :q "
                 "ORDER BY ts_code LIMIT 20"),
            {"q": f"%{q}%"},
        ).fetchall()
    finally:
        db.close()

    return JSONResponse([{"ts_code": r.ts_code, "name": r.name} for r in rows])
