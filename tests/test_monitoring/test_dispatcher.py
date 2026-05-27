"""Tests for alert dispatcher."""

import json
import tempfile
from pathlib import Path

from src.monitoring.dispatcher import AlertDispatcher


class TestAlertDispatcher:
    def test_console_dispatch(self, capsys):
        dispatcher = AlertDispatcher(console=True)
        alert = {"severity": "critical", "title": "Test", "message": "Something broke"}
        dispatcher.dispatch(alert)
        # No exception = success

    def test_file_dispatch(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            tmp = Path(f.name)

        try:
            dispatcher = AlertDispatcher(console=False, log_file=str(tmp))
            alert = {"severity": "warning", "title": "T", "message": "M"}
            dispatcher.dispatch(alert)

            content = tmp.read_text(encoding="utf-8")
            entry = json.loads(content.strip())
            assert entry["alert"]["severity"] == "warning"
            assert entry["alert"]["title"] == "T"
        finally:
            tmp.unlink(missing_ok=True)

    def test_no_channels_no_error(self):
        dispatcher = AlertDispatcher(console=False, log_file=None, webhook_url=None)
        dispatcher.dispatch({"severity": "info", "title": "T", "message": "M"})
