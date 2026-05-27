"""Monitoring routes — alerts, rules, and health."""

import asyncio
import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import text

from src.web.dependencies import get_db

router = APIRouter(tags=["monitoring"])
TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)


@router.get("/", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    db = next(get_db(request))
    try:
        alerts = db.execute(
            text("SELECT id, rule_code, alert_time, severity, title, message, status "
                 "FROM monitoring_alerts ORDER BY alert_time DESC LIMIT 50")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("pages/monitoring.html")
    return template.render(request=request, alerts=alerts)


@router.get("/alerts/table", response_class=HTMLResponse)
async def alerts_table(
    request: Request,
    severity: str = "",
    status: str = "",
):
    db = next(get_db(request))
    try:
        conditions = []
        params = {}
        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity
        if status:
            conditions.append("status = :status")
            params["status"] = status
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        alerts = db.execute(
            text(f"SELECT id, rule_code, alert_time, severity, title, message, status "
                 f"FROM monitoring_alerts {where} ORDER BY alert_time DESC LIMIT 50"),
            params,
        ).fetchall()
    finally:
        db.close()

    template = _load_template("partials/alert_table_rows.html")
    return template.render(request=request, alerts=alerts)


@router.post("/alerts/{alert_id}/acknowledge", response_class=HTMLResponse)
async def acknowledge_alert(request: Request, alert_id: int):
    db = next(get_db(request))
    try:
        db.execute(
            text("UPDATE monitoring_alerts SET status='acknowledged' WHERE id=:id AND status='open'"),
            {"id": alert_id},
        )
        db.commit()
    finally:
        db.close()

    return HTMLResponse('<span class="badge badge-warning">acknowledged</span>')


@router.post("/alerts/{alert_id}/resolve", response_class=HTMLResponse)
async def resolve_alert(request: Request, alert_id: int):
    db = next(get_db(request))
    try:
        db.execute(
            text("UPDATE monitoring_alerts SET status='resolved' WHERE id=:id"),
            {"id": alert_id},
        )
        db.commit()
    finally:
        db.close()

    return HTMLResponse('<span class="badge badge-success">resolved</span>')


@router.get("/rules", response_class=HTMLResponse)
async def rules_page(request: Request):
    db = next(get_db(request))
    try:
        rules = db.execute(
            text("SELECT id, rule_code, rule_name, target_table, target_column, check_type, "
                 "threshold_min, threshold_max, lookback_hours, severity, is_active "
                 "FROM monitoring_rules ORDER BY rule_code")
        ).fetchall()
    finally:
        db.close()

    template = _load_template("pages/rules.html")
    return template.render(request=request, rules=rules)


@router.get("/alerts/stream")
async def alert_stream(request: Request):
    """SSE endpoint — streams new open alerts every 30 seconds."""

    async def event_generator():
        last_id = 0
        while True:
            if await request.is_disconnected():
                break

            db = next(get_db(request))
            try:
                rows = db.execute(
                    text(
                        "SELECT id, rule_code, alert_time, severity, title, message, status "
                        "FROM monitoring_alerts WHERE id > :last_id AND status = 'open' "
                        "ORDER BY id ASC LIMIT 10"
                    ),
                    {"last_id": last_id},
                ).fetchall()
            finally:
                db.close()

            for row in rows:
                payload = {
                    "id": row.id,
                    "rule_code": row.rule_code,
                    "alert_time": str(row.alert_time),
                    "severity": row.severity,
                    "title": row.title,
                    "message": row.message,
                    "status": row.status,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last_id = max(last_id, row.id)

            await asyncio.sleep(30)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
