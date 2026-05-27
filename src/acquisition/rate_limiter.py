"""Token bucket rate limiter for API call throttling."""

import asyncio
import threading
import time


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter.

    Tokens refill at `rate` per second, up to `burst` max.
    """

    def __init__(self, rate: float, burst: int | None = None) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        self.rate = rate
        self.burst = burst if burst is not None else max(1, int(rate * 2))
        self._tokens = float(self.burst)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def try_acquire(self) -> bool:
        """Try to consume one token without blocking."""
        with self._lock:
            self._refill()
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_time = (1 - self._tokens) / self.rate
            await asyncio.sleep(max(wait_time, 0.05))


class RateLimiterRegistry:
    """Global registry mapping source_code -> TokenBucketRateLimiter."""

    def __init__(self) -> None:
        self._limiters: dict[str, TokenBucketRateLimiter] = {}
        self._lock = threading.Lock()

    def get(self, source_code: str, rate: float) -> TokenBucketRateLimiter:
        with self._lock:
            if source_code not in self._limiters:
                self._limiters[source_code] = TokenBucketRateLimiter(rate)
            return self._limiters[source_code]
