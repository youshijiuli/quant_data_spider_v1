"""Sync control routes — trigger syncs and view history."""

import asyncio

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from src.web.dependencies import get_db

router = APIRouter(tags=["sync"])
TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)


@router.get("/", response_class=HTMLResponse)
async def sync_page(request: Request):
    db = next(get_db(request))
    try:
        sources = db.execute(
            text("SELECT source_code, source_name, source_type, is_active FROM data_sources ORDER BY source_code")
        ).fetchall()
        history = db.execute(
            text("SELECT source_code, sync_type, status, total_rows, inserted_rows, "
                 "updated_rows, skipped_rows, error_message, started_at, finished_at "
                 "FROM data_sync_log ORDER BY started_at DESC LIMIT 20")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("pages/sync.html")
    return template.render(request=request, sources=sources, history=history)


@router.post("/trigger", response_class=HTMLResponse)
async def sync_trigger(
    request: Request,
    source_code: str = Form(""),
    group_name: str = Form(""),
    symbol: str = Form(""),
    index_code: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
):
    from src.acquisition.source_registry import SourceRegistry

    registry = SourceRegistry()
    sources_to_sync: list[str] = []

    if group_name:
        sources_to_sync = registry.get_sync_group(group_name)
    elif source_code:
        sources_to_sync = [source_code]

    if not sources_to_sync:
        return HTMLResponse(
            '<div class="toast toast-error">Please select a source or group to sync</div>'
        )

    sync_service = request.app.state.sync_service
    results_html: list[str] = []

    for src in sources_to_sync:
        params = {}
        if src in ("akshare_stock_daily",) and symbol:
            params["symbol"] = symbol.strip()
            if start_date:
                params["start_date"] = start_date.strip()
            if end_date:
                params["end_date"] = end_date.strip()
        elif src in ("akshare_index_daily",) and index_code:
            params["index_code"] = index_code.strip()
            if start_date:
                params["start_date"] = start_date.strip()
            if end_date:
                params["end_date"] = end_date.strip()
        elif src in ("akshare_financial",) and symbol:
            params["symbol"] = symbol.strip()

        result = await sync_service.trigger_sync(src, **params)
        color = "#2ecc71" if result.status == "success" else "#e74c3c"
        results_html.append(
            f'<div style="border-left:3px solid {color};padding:8px 12px;margin:4px 0;background:var(--pico-card-background-color)">'
            f'<strong>{result.source_code}</strong>: {result.status} '
            f'(rows={result.total_rows}, inserted={result.inserted_rows}, '
            f'duration={result.duration_ms}ms)'
            f'{" — " + result.error_message if result.error_message else ""}'
            f'</div>'
        )

    # Also return the updated history table
    db = next(get_db(request))
    try:
        history = db.execute(
            text("SELECT source_code, sync_type, status, total_rows, inserted_rows, "
                 "updated_rows, skipped_rows, error_message, started_at, finished_at "
                 "FROM data_sync_log ORDER BY started_at DESC LIMIT 20")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("partials/sync_history_rows.html")
    history_html = template.render(request=request, history=history)

    return HTMLResponse(
        '<div style="margin-bottom:12px">' + "".join(results_html) + "</div>"
        + history_html
    )


@router.get("/history", response_class=HTMLResponse)
async def sync_history(request: Request):
    db = next(get_db(request))
    try:
        history = db.execute(
            text("SELECT source_code, sync_type, status, total_rows, inserted_rows, "
                 "updated_rows, skipped_rows, error_message, started_at, finished_at "
                 "FROM data_sync_log ORDER BY started_at DESC LIMIT 50")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("partials/sync_history_rows.html")
    return template.render(request=request, history=history)
