"""Tests for in-memory sliding window rate limiter."""


from app.api.deps import SlidingWindowRateLimiter


def test_rate_limiter_permits_within_limit():
    """Verify requests under max threshold are permitted."""
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
    for _ in range(5):
        assert limiter.is_allowed("192.168.1.1") is True


def test_rate_limiter_blocks_excessive_requests():
    """Verify requests exceeding threshold are blocked."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("10.0.0.1") is True
    assert limiter.is_allowed("10.0.0.1") is True
    assert limiter.is_allowed("10.0.0.1") is True
    # 4th request must be blocked
    assert limiter.is_allowed("10.0.0.1") is False

    # Different IP should still be allowed
    assert limiter.is_allowed("10.0.0.2") is True
