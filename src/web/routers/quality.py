"""Data quality routes — quality reports and checks."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["quality"])
TEMPLATE_DIR = __import__("src.web.config", fromlist=["WebSettings"]).WebSettings().template_dir


def _load_template(name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(name)


@router.get("/", response_class=HTMLResponse)
async def quality_page(request: Request):
    from src.web.dependencies import get_db
    from sqlalchemy import text

    db = next(get_db(request))
    try:
        tables = ["stock_basic", "stock_daily_quote", "stock_index_daily", "stock_financial"]
        stats = {}
        for table in tables:
            row = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            stats[table] = row[0] if row else 0
    finally:
        db.close()

    template = _load_template("pages/quality.html")
    return template.render(request=request, stats=stats)
