"""Entry point to start the Quant Data Spider web dashboard."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from config.settings import settings
from src.core.database import init_db
from src.web.app import create_app
from src.web.config import WebSettings

web_settings = WebSettings()

engine, SessionLocal = init_db(settings.db.url)
from src.core.database import create_all_tables
create_all_tables(engine)
app = create_app(engine, SessionLocal)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=web_settings.host,
        port=web_settings.port,
        reload=web_settings.reload,
        log_level=settings.app.log_level.lower(),
    )
