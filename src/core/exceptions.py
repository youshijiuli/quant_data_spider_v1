"""Custom exception hierarchy for quant data pipeline."""


class QuantException(Exception):
    """Base exception for the quant data pipeline."""


# --- Acquisition ---
class AcquisitionError(QuantException):
    """Data acquisition failure."""


class SourceUnavailableError(AcquisitionError):
    """Data source is unreachable."""


class RateLimitError(AcquisitionError):
    """Rate limit exceeded."""


class EmptyDataError(AcquisitionError):
    """Source returned no rows (logged, not necessarily an error)."""


class InvalidResponseError(AcquisitionError):
    """Response schema does not match expected format."""


# --- Processing ---
class ProcessingError(QuantException):
    """Data processing failure."""


class ValidationError(ProcessingError):
    """DataFrame failed validation rules."""


class MissingColumnError(ValidationError):
    """Required column absent from source data."""


class OutlierThresholdError(ProcessingError):
    """Too many outliers detected."""


# --- Storage ---
class StorageError(QuantException):
    """Data storage failure."""


class ConnectionError(StorageError):
    """Database unreachable."""


class UpsertError(StorageError):
    """Bulk upsert operation failed."""


class TransactionError(StorageError):
    """Transaction rollback occurred."""


# --- Monitoring ---
class MonitoringError(QuantException):
    """Monitoring system failure."""


class RuleEvaluationError(MonitoringError):
    """Failed to evaluate a monitoring rule."""


class AlertDispatchError(MonitoringError):
    """Failed to dispatch an alert."""
