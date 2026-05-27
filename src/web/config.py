"""Web layer configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    model_config = SettingsConfigDict(env_prefix="QUANT_WEB_")

    @property
    def static_dir(self) -> Path:
        return Path(__file__).parent / "static"

    @property
    def template_dir(self) -> Path:
        return Path(__file__).parent / "templates"
