"""Abstract base class for data source clients with retry logic."""

import asyncio
import random
import time
from abc import ABC, abstractmethod

import httpx
import pandas as pd

from src.acquisition.rate_limiter import TokenBucketRateLimiter
from src.core.exceptions import EmptyDataError, RateLimitError, SourceUnavailableError


class BaseDataClient(ABC):
    """Contract for all data source clients.

    Encapsulates HTTP transport, rate limiting, and exponential backoff retry.
    Subclasses implement `fetch()` to call the actual data source.
    """

    def __init__(
        self,
        source_code: str,
        rate_limiter: TokenBucketRateLimiter,
        retry_max: int = 3,
        retry_backoff: float = 2.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.source_code = source_code
        self._limiter = rate_limiter
        self._retry_max = retry_max
        self._retry_backoff = retry_backoff
        self._http = http_client or httpx.AsyncClient(timeout=30.0)
        self._owns_http = http_client is None

    @abstractmethod
    async def fetch(self, **kwargs) -> pd.DataFrame:
        """Fetch data from the source. Implement in subclass."""

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _retry_call(self, fn, *args, **kwargs):
        """Call `fn` with exponential backoff + jitter on failure."""
        last_exc: Exception | None = None
        for attempt in range(self._retry_max + 1):
            try:
                result = fn(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
                    raise RateLimitError(f"{self.source_code}: rate limited") from exc
                if attempt == self._retry_max:
                    break
                delay = self._retry_backoff ** attempt + random.uniform(0, 1)
                await asyncio.sleep(delay)

        raise SourceUnavailableError(f"{self.source_code}: {last_exc}") from last_exc

    async def _rate_limited_request(self, url: str, **kwargs) -> httpx.Response:
        """Make an HTTP request respecting the rate limiter token bucket."""
        await self._limiter.acquire()
        return await self._retry_call(self._http.get, url, **kwargs)

    def _check_empty(self, df: pd.DataFrame, source_code: str) -> pd.DataFrame:
        if df.empty:
            raise EmptyDataError(f"{source_code}: returned empty DataFrame")
        return df
