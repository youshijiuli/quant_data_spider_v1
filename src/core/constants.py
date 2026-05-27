"""Global constants for the quant data pipeline."""

from enum import Enum
from typing import Final

TIMEZONE_ASIA_SHANGHAI: Final = "Asia/Shanghai"

DEFAULT_RATE_LIMIT_RPS: Final = 2.0
DEFAULT_RETRY_MAX: Final = 3
DEFAULT_RETRY_BACKOFF: Final = 2.0
DEFAULT_TIMEOUT_SECONDS: Final = 30

MARKET_CLOSE_HOUR: Final = 16
MARKET_CLOSE_MINUTE: Final = 30


class SyncStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SyncType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class CheckType(str, Enum):
    NULL_RATE = "null_rate"
    STALE_DATA = "stale_data"
    VALUE_RANGE = "value_range"
    ROW_COUNT = "row_count"
    DUPLICATE_RATE = "duplicate_rate"


class AssetClass(str, Enum):
    STOCK = "stock"
    INDEX = "index"
    FUTURES = "futures"
    OPTION = "option"


EXCHANGE_SUFFIX_MAP: Final = {
    "000001": "SH",
    "000002": "SZ",
    "000003": "BJ",
    "sh": "SH",
    "sz": "SZ",
    "bj": "BJ",
}
