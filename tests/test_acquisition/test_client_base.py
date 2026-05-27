"""Tests for BaseDataClient."""

import pandas as pd
import pytest

from src.acquisition.client_base import BaseDataClient
from src.acquisition.rate_limiter import TokenBucketRateLimiter
from src.core.exceptions import EmptyDataError


class _ConcreteClient(BaseDataClient):
    """Concrete client for testing BaseDataClient."""

    async def fetch(self, **kwargs) -> pd.DataFrame:
        return pd.DataFrame(kwargs.get("data", []))


@pytest.fixture
def limiter():
    return TokenBucketRateLimiter(rate=10.0, burst=10)


@pytest.fixture
def client(limiter):
    return _ConcreteClient(source_code="test_source", rate_limiter=limiter)


class TestBaseDataClient:
    def test_init_defaults(self, limiter):
        client = _ConcreteClient(source_code="test", rate_limiter=limiter)
        assert client.source_code == "test"
        assert client._retry_max == 3
        assert client._retry_backoff == 2.0
        assert client._http is not None

    def test_init_custom_retry(self, limiter):
        client = _ConcreteClient(
            source_code="test",
            rate_limiter=limiter,
            retry_max=5,
            retry_backoff=3.0,
        )
        assert client._retry_max == 5
        assert client._retry_backoff == 3.0

    def test_check_empty_raises(self, client):
        with pytest.raises(EmptyDataError):
            client._check_empty(pd.DataFrame(), "test_source")

    def test_check_empty_passes(self, client):
        df = pd.DataFrame([{"a": 1}])
        result = client._check_empty(df, "test_source")
        assert result is df

    def test_owns_http_when_not_provided(self, limiter):
        client = _ConcreteClient(source_code="test", rate_limiter=limiter)
        assert client._owns_http is True

    @pytest.mark.asyncio
    async def test_fetch_returns_dataframe(self, client):
        df = await client.fetch(data=[{"col": 1}])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @pytest.mark.asyncio
    async def test_close(self, client):
        await client.close()
