"""Data browser routes — stock, index, financial data tables."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import text

from src.web.dependencies import get_db

router = APIRouter(tags=["data"])
TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)


@router.get("/stocks", response_class=HTMLResponse)
async def stocks_page(request: Request):
    template = _load_template("pages/stocks.html")
    return template.render(request=request)


@router.get("/stocks/table", response_class=HTMLResponse)
async def stocks_table(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=200),
    search: str = Query(""),
    exchange: str = Query(""),
):
    db = next(get_db(request))
    try:
        offset = (page - 1) * page_size
        conditions = []
        params = {}
        if search:
            conditions.append("(ts_code LIKE :search OR name LIKE :search)")
            params["search"] = f"%{search}%"
        if exchange:
            conditions.append("exchange = :exchange")
            params["exchange"] = exchange

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = db.execute(
            text(f"SELECT id, ts_code, symbol, name, exchange, industry_l1, list_date, market_cap "
                 f"FROM stock_basic {where} ORDER BY ts_code LIMIT :limit OFFSET :offset"),
            {**params, "limit": page_size, "offset": offset},
        ).fetchall()

        total_row = db.execute(
            text(f"SELECT COUNT(*) FROM stock_basic {where}"), params
        ).fetchone()
        total = total_row[0] if total_row else 0
        total_pages = max(1, (total + page_size - 1) // page_size)
    finally:
        db.close()

    template = _load_template("partials/stock_table_rows.html")
    return template.render(request=request, rows=rows, page=page, total_pages=total_pages, total=total)


@router.get("/indexes", response_class=HTMLResponse)
async def indexes_page(request: Request):
    template = _load_template("pages/indexes.html")
    return template.render(request=request)


@router.get("/indexes/table", response_class=HTMLResponse)
async def indexes_table(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=200),
    index_code: str = Query(""),
):
    db = next(get_db(request))
    try:
        offset = (page - 1) * page_size
        conditions = []
        params = {}
        if index_code:
            conditions.append("index_code LIKE :code")
            params["code"] = f"%{index_code}%"
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = db.execute(
            text(f"SELECT id, index_code, index_name, trade_date, open, high, low, close, volume, amount, pct_change "
                 f"FROM stock_index_daily {where} ORDER BY trade_date DESC, index_code "
                 f"LIMIT :limit OFFSET :offset"),
            {**params, "limit": page_size, "offset": offset},
        ).fetchall()

        total_row = db.execute(text(f"SELECT COUNT(*) FROM stock_index_daily {where}"), params).fetchone()
        total = total_row[0] if total_row else 0
        total_pages = max(1, (total + page_size - 1) // page_size)
    finally:
        db.close()

    template = _load_template("partials/index_table_rows.html")
    return template.render(request=request, rows=rows, page=page, total_pages=total_pages, total=total)


@router.get("/financials", response_class=HTMLResponse)
async def financials_page(request: Request):
    template = _load_template("pages/financials.html")
    return template.render(request=request)


@router.get("/financials/table", response_class=HTMLResponse)
async def financials_table(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=200),
    ts_code: str = Query(""),
):
    db = next(get_db(request))
    try:
        offset = (page - 1) * page_size
        conditions = []
        params = {}
        if ts_code:
            conditions.append("ts_code LIKE :code")
            params["code"] = f"%{ts_code}%"
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = db.execute(
            text(f"SELECT id, ts_code, report_period, end_date, total_revenue, revenue_yoy, "
                 f"net_profit, profit_yoy, eps, bvps, roe "
                 f"FROM stock_financial {where} ORDER BY end_date DESC, ts_code "
                 f"LIMIT :limit OFFSET :offset"),
            {**params, "limit": page_size, "offset": offset},
        ).fetchall()

        total_row = db.execute(text(f"SELECT COUNT(*) FROM stock_financial {where}"), params).fetchone()
        total = total_row[0] if total_row else 0
        total_pages = max(1, (total + page_size - 1) // page_size)
    finally:
        db.close()

    template = _load_template("partials/financial_table_rows.html")
    return template.render(request=request, rows=rows, page=page, total_pages=total_pages, total=total)


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request):
    db = next(get_db(request))
    try:
        rows = db.execute(
            text("SELECT source_code, source_name, source_type, is_active, rate_limit_rps "
                 "FROM data_sources ORDER BY source_code")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("pages/sources.html")
    return template.render(request=request, rows=rows)
