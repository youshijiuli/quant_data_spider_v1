"""Alert dispatch — console, file, and webhook output."""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Dispatches alerts to configured output channels."""

    def __init__(
        self,
        console: bool = True,
        log_file: str | None = None,
        webhook_url: str | None = None,
    ):
        self.console = console
        self.log_file = log_file
        self.webhook_url = webhook_url

    def dispatch(self, alert: dict) -> None:
        """Send alert to all enabled channels."""
        if self.console:
            self._to_console(alert)
        if self.log_file:
            self._to_file(alert)
        if self.webhook_url:
            self._to_webhook(alert)

    def _to_console(self, alert: dict) -> None:
        severity = alert.get("severity", "info")
        title = alert.get("title", "")
        message = alert.get("message", "")
        level = (
            logging.CRITICAL if severity == "critical"
            else logging.WARNING if severity == "warning"
            else logging.INFO
        )
        logger.log(level, f"[{severity.upper()}] {title}: {message}")

    def _to_file(self, alert: dict) -> None:
        path = Path(self.log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert": {k: str(v) if isinstance(v, datetime) else v for k, v in alert.items()},
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _to_webhook(self, alert: dict) -> None:
        try:
            import httpx

            httpx.post(
                self.webhook_url,
                json={
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": alert.get("severity"),
                    "title": alert.get("title"),
                    "message": alert.get("message"),
                },
                timeout=5,
            )
        except Exception:
            logger.exception("Webhook dispatch failed")
