"""
Rate Limit Middleware
Sliding-window rate limiter backed by Redis.
Default: 60 requests / minute per user/IP.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request

from app.services.redis_client import redis_client

RATE_LIMIT = 60       # max requests
WINDOW_SECS = 60      # per minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Identify by user ID if auth'd, else by IP
        user = getattr(request.state, "user", None)
        identifier = user.get("sub") if user else request.client.host
        key = f"rate_limit:{identifier}"

        try:
            allowed = await _check_rate_limit(key)
        except Exception:
            # If Redis is down, fail open (don't block users)
            allowed = True

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again in a minute.",
                    "limit": RATE_LIMIT,
                    "window_seconds": WINDOW_SECS,
                },
                headers={"Retry-After": str(WINDOW_SECS)},
            )

        return await call_next(request)


async def _check_rate_limit(key: str) -> bool:
    """
    Sliding window counter using Redis.
    Returns True if request is allowed, False if limit exceeded.
    """
    client = redis_client.client
    now = int(time.time())
    window_start = now - WINDOW_SECS

    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)   # Remove old entries
    pipe.zadd(key, {str(now): now})               # Add current request
    pipe.zcard(key)                                # Count requests in window
    pipe.expire(key, WINDOW_SECS + 1)             # Auto-cleanup
    results = await pipe.execute()

    request_count = results[2]
    return request_count <= RATE_LIMIT
