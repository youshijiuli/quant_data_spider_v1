"""Tests for core exceptions."""

import pytest

from src.core.exceptions import (
    AcquisitionError,
    AlertDispatchError,
    EmptyDataError,
    MonitoringError,
    QuantException,
    RateLimitError,
    RuleEvaluationError,
    SourceUnavailableError,
    StorageError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_base_exception(self):
        e = QuantException("base error")
        assert str(e) == "base error"
        assert isinstance(e, Exception)

    def test_acquisition_error(self):
        e = AcquisitionError("acq failed")
        assert isinstance(e, QuantException)

    def test_rate_limit_error(self):
        e = RateLimitError("rate limit")
        assert isinstance(e, AcquisitionError)
        assert isinstance(e, QuantException)

    def test_empty_data_error(self):
        e = EmptyDataError("empty")
        assert isinstance(e, AcquisitionError)

    def test_source_unavailable_error(self):
        e = SourceUnavailableError("down")
        assert isinstance(e, AcquisitionError)

    def test_monitoring_error(self):
        e = MonitoringError("mon failed")
        assert isinstance(e, QuantException)

    def test_rule_evaluation_error(self):
        e = RuleEvaluationError("rule failed")
        assert isinstance(e, MonitoringError)

    def test_alert_dispatch_error(self):
        e = AlertDispatchError("dispatch failed")
        assert isinstance(e, MonitoringError)

    def test_storage_error(self):
        e = StorageError("storage failed")
        assert isinstance(e, QuantException)

    def test_validation_error_is_processing(self):
        e = ValidationError("invalid")
        assert isinstance(e, QuantException)
