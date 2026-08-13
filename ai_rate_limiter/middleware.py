from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable, Awaitable
import asyncio
from .config import RateLimitConfig
from .identity import default_identity_resolver
from .storage import SlidingWindowRedis, SlidingWindowMemory
from redis.asyncio import Redis, ConnectionError as RedisConnectionError

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app,
        config: RateLimitConfig = RateLimitConfig(),
        identity_resolver: Optional[Callable[[Request, str, str], Awaitable[tuple[str, Optional[str]]]]] = None
    ):
        super().__init__(app)
        self.config = config
        self.identity_resolver = identity_resolver or default_identity_resolver
        self._redis = None
        self._memory = SlidingWindowMemory()
        self._redis_ready = False
        if self.config.redis_enabled and self.config.redis_url:
            asyncio.create_task(self._init_redis())

    async def _init_redis(self):
        try:
            self._redis = Redis.from_url(self.config.redis_url, decode_responses=True)
            await self._redis.ping()
            self._redis_ready = True
        except Exception:
            self._redis_ready = False

    async def dispatch(self, request: Request, call_next):
        api_key, user_id = await self.identity_resolver(
            request, 
            self.config.api_key_header, 
            self.config.user_id_header
        )
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key header."}
            )

        # Check both user and API key limits
        # API key is always present (validated above)
        # User ID is optional
        retry_after = 0
        
        # Check API key limits
        api_key_identity = f"api_key:{api_key}"
        for limit, window in [
            (self.config.requests_per_minute, 60),
            (self.config.requests_per_hour, 3600),
            (self.config.requests_per_day, 86400)
        ]:
            allowed, ra = await self._is_allowed(api_key_identity, limit, window)
            if not allowed:
                retry_after = max(retry_after, ra or 1)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={"Retry-After": str(retry_after)}
                )
        
        # If user_id present, check user-specific limits as well
        if user_id:
            user_identity = f"user:{user_id}"
            for limit, window in [
                (self.config.requests_per_minute, 60),
                (self.config.requests_per_hour, 3600),
                (self.config.requests_per_day, 86400)
            ]:
                allowed, ra = await self._is_allowed(user_identity, limit, window)
                if not allowed:
                    retry_after = max(retry_after, ra or 1)
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Try again later."},
                        headers={"Retry-After": str(retry_after)}
                    )
        response = await call_next(request)
        return response

    async def _is_allowed(self, key: str, limit: int, window_seconds: int):
        if self.config.redis_enabled and self._redis_ready:
            try:
                store = SlidingWindowRedis(self._redis)
                return await store.is_allowed(key, limit, window_seconds)
            except RedisConnectionError:
                self._redis_ready = False
        # fallback
        return await self._memory.is_allowed(key, limit, window_seconds)
