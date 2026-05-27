"""Tests for rate limiter and limiter registry."""

import asyncio
import pytest

from src.acquisition.rate_limiter import RateLimiterRegistry, TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    def test_init_defaults(self):
        lim = TokenBucketRateLimiter(rate=5.0)
        assert lim.rate == 5.0
        assert lim.burst == 10

    def test_init_custom_burst(self):
        lim = TokenBucketRateLimiter(rate=3.0, burst=5)
        assert lim.burst == 5

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(rate=0)

    def test_try_acquire_succeeds_initial(self):
        lim = TokenBucketRateLimiter(rate=100.0, burst=10)
        for _ in range(10):
            assert lim.try_acquire() is True
        assert lim.try_acquire() is False

    @pytest.mark.asyncio
    async def test_acquire_waits(self):
        lim = TokenBucketRateLimiter(rate=5.0, burst=1)
        assert lim.try_acquire() is True
        assert lim.try_acquire() is False
        await asyncio.sleep(0.3)
        # 5.0 tokens/s * 0.3s = 1.5 tokens, capped at burst=1
        assert lim.try_acquire() is True

    def test_refill_respects_burst(self):
        lim = TokenBucketRateLimiter(rate=100.0, burst=5)
        for _ in range(5):
            lim.try_acquire()
        lim.try_acquire()
        assert lim._tokens <= 5


class TestRateLimiterRegistry:
    def test_get_creates_new(self):
        reg = RateLimiterRegistry()
        lim = reg.get("source_a", 3.0)
        assert isinstance(lim, TokenBucketRateLimiter)
        assert lim.rate == 3.0

    def test_get_returns_same(self):
        reg = RateLimiterRegistry()
        a = reg.get("src", 2.0)
        b = reg.get("src", 5.0)
        assert a is b

    def test_multiple_sources(self):
        reg = RateLimiterRegistry()
        a = reg.get("src_a", 1.0)
        b = reg.get("src_b", 2.0)
        assert a is not b
