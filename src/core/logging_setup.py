"""Loguru configuration — loaded at application startup."""

import sys
import tomli
from pathlib import Path

from loguru import logger

from config.settings import CONFIG_DIR


def setup_logging(config_path: str | None = None) -> None:
    """Configure loguru from logging.toml or sensible defaults."""
    toml_path = Path(config_path) if config_path else CONFIG_DIR / "logging.toml"

    # Remove default handler
    logger.remove()

    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomli.load(f)

        log_cfg = data.get("logger", {})
        fmt = log_cfg.get("format",
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
        )
        level = log_cfg.get("level", "INFO")

        for handler in data.get("handlers", []):
            sink = handler["sink"]
            if sink == "sys.stderr":
                sink = sys.stderr
            kwargs = {}
            for opt in ("rotation", "retention", "compression"):
                if opt in handler:
                    kwargs[opt] = handler[opt]
            if isinstance(sink, str):
                kwargs["encoding"] = "utf-8"
            logger.add(
                sink,
                format=handler.get("format", fmt),
                level=handler.get("level", level),
                colorize=handler.get("colorize", False),
                **kwargs,
            )
    else:
        # Sensible defaults: stderr for WARNING+, file for INFO+
        logger.add(
            sys.stderr,
            format="<level>{level: <8}</level> | <level>{message}</level>",
            level="WARNING",
            colorize=True,
        )
        logger.add(
            "logs/quant.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            encoding="utf-8",
        )
