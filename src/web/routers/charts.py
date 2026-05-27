"""Chart routes — ECharts candlestick and line charts."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text

from src.web.dependencies import get_db

router = APIRouter(tags=["charts"])
TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)


@router.get("/", response_class=HTMLResponse)
async def charts_page(request: Request):
    db = next(get_db(request))
    try:
        stocks = db.execute(
            text("SELECT ts_code, name FROM stock_basic WHERE is_active=1 ORDER BY ts_code LIMIT 100")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("pages/charts.html")
    return template.render(request=request, stocks=stocks)


@router.get("/stock/{ts_code}", response_class=HTMLResponse)
async def stock_chart_page(request: Request, ts_code: str):
    db = next(get_db(request))
    try:
        stock = db.execute(
            text("SELECT ts_code, name FROM stock_basic WHERE ts_code=:code"),
            {"code": ts_code},
        ).fetchone()
    finally:
        db.close()

    template = _load_template("pages/charts.html")
    return template.render(request=request, stocks=None, selected_stock=stock)


@router.get("/stock/{ts_code}/data")
async def stock_chart_data(request: Request, ts_code: str):
    db = next(get_db(request))
    try:
        rows = db.execute(
            text("SELECT trade_date, open, high, low, close, volume, pct_change "
                 "FROM stock_daily_quote WHERE ts_code=:code ORDER BY trade_date LIMIT 250"),
            {"code": ts_code},
        ).fetchall()

        stock = db.execute(
            text("SELECT name FROM stock_basic WHERE ts_code=:code"),
            {"code": ts_code},
        ).fetchone()
        stock_name = stock[0] if stock else ts_code
    finally:
        db.close()

    return JSONResponse({
        "ts_code": ts_code,
        "stock_name": stock_name,
        "dates": [str(r.trade_date) for r in rows],
        "ohlc": [[float(r.open), float(r.close), float(r.low), float(r.high)] for r in rows],
        "volumes": [int(r.volume) if r.volume else 0 for r in rows],
    })


@router.get("/index/{index_code}/data")
async def index_chart_data(request: Request, index_code: str):
    db = next(get_db(request))
    try:
        rows = db.execute(
            text("SELECT trade_date, open, high, low, close, volume, pct_change "
                 "FROM stock_index_daily WHERE index_code=:code ORDER BY trade_date LIMIT 250"),
            {"code": index_code},
        ).fetchall()

        idx = db.execute(
            text("SELECT DISTINCT index_name FROM stock_index_daily WHERE index_code=:code LIMIT 1"),
            {"code": index_code},
        ).fetchone()
        idx_name = idx[0] if idx else index_code
    finally:
        db.close()

    return JSONResponse({
        "index_code": index_code,
        "index_name": idx_name,
        "dates": [str(r.trade_date) for r in rows],
        "data": [[float(r.open), float(r.close), float(r.low), float(r.high)] for r in rows],
        "volumes": [int(r.volume) if r.volume else 0 for r in rows],
    })
