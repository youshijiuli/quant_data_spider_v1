"""Unified configuration via Pydantic-settings.

Load order: .env → TOML files → defaults.  Sensitive values in .env, other in TOML.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"


class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    name: str = "quant_data"

    model_config = SettingsConfigDict(env_prefix="QUANT_DB_")

    @property
    def url(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class AppSettings(BaseSettings):
    env: str = "dev"
    log_level: str = "INFO"
    timezone: str = "Asia/Shanghai"
    rate_limit_rps: float = 2.0
    retry_max: int = 3
    retry_backoff: float = 2.0
    timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_prefix="QUANT_")

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"


class SchedulerSettings(BaseSettings):
    enabled: bool = True
    timezone: str = "Asia/Shanghai"
    max_workers: int = 4

    model_config = SettingsConfigDict(env_prefix="QUANT_SCHEDULER_")


class MonitoringSettings(BaseSettings):
    enabled: bool = True
    alert_dispatchers: list[str] = ["console", "file"]
    webhook_url: str = ""

    model_config = SettingsConfigDict(env_prefix="QUANT_MONITORING_")


class Settings(BaseSettings):
    db: DatabaseSettings = DatabaseSettings()
    app: AppSettings = AppSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
