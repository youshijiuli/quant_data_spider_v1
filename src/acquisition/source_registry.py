"""Source registry — loads data source definitions and creates clients."""

import tomli

from src.acquisition.akshare_client import AKShareClient
from src.acquisition.client_base import BaseDataClient
from src.acquisition.rate_limiter import RateLimiterRegistry

CONFIG_DIR = __import__("config.settings", fromlist=["settings"]).ROOT_DIR / "config"


class SourceRegistry:
    """Registry that loads source configs from TOML and creates typed clients."""

    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path or str(CONFIG_DIR / "sources.toml")
        self._sources: dict[str, dict] = {}
        self._limiter_registry = RateLimiterRegistry()
        self._load()

    def _load(self) -> None:
        with open(self._config_path, "rb") as f:
            data = tomli.load(f)

        for key, value in data.items():
            if key.startswith("akshare_") and isinstance(value, dict):
                self._sources[key] = value

    def get_source(self, source_code: str) -> dict:
        if source_code not in self._sources:
            raise ValueError(f"Unknown source: {source_code}")
        return self._sources[source_code]

    def list_active_sources(self) -> list[str]:
        return [k for k, v in self._sources.items() if v.get("is_active", False)]

    def get_sync_group(self, name: str) -> list[str]:
        with open(self._config_path, "rb") as f:
            data = tomli.load(f)
        groups = data.get("sync_groups", {})
        return groups.get(name, [])

    def get_client(self, source_code: str) -> BaseDataClient:
        cfg = self.get_source(source_code)
        source_type = cfg.get("source_type", "")

        limiter = self._limiter_registry.get(source_code, cfg.get("rate_limit_rps", 2.0))

        if source_type == "akshare":
            return AKShareClient(
                source_code=source_code,
                rate_limiter=limiter,
                retry_max=cfg.get("retry_max", 3),
                retry_backoff=cfg.get("retry_backoff", 2.0),
            )

        raise ValueError(f"Unsupported source type: {source_type}")
