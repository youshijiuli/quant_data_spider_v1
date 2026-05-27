"""Tests for logging setup."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_logging_toml():
    content = """\
[logger]
level = "DEBUG"
format = "{time} | {level} | {message}"

[[handlers]]
sink = "sys.stderr"
level = "INFO"
colorize = true

[[handlers]]
sink = "test_log.log"
level = "DEBUG"
format = "{time} | {level} | {message}"
rotation = "1 MB"
retention = "7 days"
compression = "gz"
"""
    tmp = Path(tempfile.mktemp(suffix=".toml"))
    tmp.write_text(content, encoding="utf-8")
    yield str(tmp)
    try:
        tmp.unlink(missing_ok=True)
    except Exception:
        pass


class TestLoggingSetup:
    def test_setup_logging_with_toml(self, temp_logging_toml):
        from src.core.logging_setup import setup_logging
        setup_logging(temp_logging_toml)

    def test_setup_logging_with_defaults(self):
        from src.core.logging_setup import setup_logging
        setup_logging("/nonexistent/path/config.toml")

    def test_setup_logging_writes_log(self, temp_logging_toml):
        from loguru import logger
        from src.core.logging_setup import setup_logging

        setup_logging(temp_logging_toml)
        logger.info("test message")
