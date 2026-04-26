"""FraudShield — Request timing and rate limiting middleware."""

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class TimingMiddleware(BaseHTTPMiddleware):
    """Add X-Process-Time header to all API responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{elapsed:.2f}ms"
        response.headers["X-Powered-By"] = "FraudShield"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter: 60 requests/minute per IP."""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_limited(self, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        timestamps = self._requests[ip]
        # Prune old entries
        self._requests[ip] = [t for t in timestamps if t > cutoff]
        if len(self._requests[ip]) >= self.max_requests:
            return True
        self._requests[ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting on docs/openapi paths
        if request.url.path in ("/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        ip = self._client_ip(request)
        if self._is_limited(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(self.window_seconds)},
            )

        response = await call_next(request)
        remaining = self.max_requests - len(self._requests[ip])
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
