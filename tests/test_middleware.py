import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from ai_rate_limiter import RateLimiterMiddleware, RateLimitConfig

@pytest.mark.asyncio
async def test_per_api_key_rate_limit():
    import asyncio
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        config=RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=10,
            requests_per_day=20,
            redis_enabled=False
        )
    )
    @app.get("/rl")
    async def rl():
        return {"ok": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-API-Key": "testkey"}
        r1 = await ac.get("/rl", headers=headers)
        assert r1.status_code == 200
        await asyncio.sleep(0.01)  # Ensure different timestamps
        r2 = await ac.get("/rl", headers=headers)
        assert r2.status_code == 200
        await asyncio.sleep(0.01)  # Ensure different timestamps
        r3 = await ac.get("/rl", headers=headers)
        assert r3.status_code == 429
        assert "Retry-After" in r3.headers

@pytest.mark.asyncio
async def test_per_user_and_api_key_rate_limit():
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        config=RateLimitConfig(
            requests_per_minute=1,
            requests_per_hour=10,
            requests_per_day=20,
            redis_enabled=False
        )
    )
    @app.get("/rl")
    async def rl():
        return {"ok": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-API-Key": "testkey2", "X-User-Id": "user1"}
        r1 = await ac.get("/rl", headers=headers)
        assert r1.status_code == 200
        r2 = await ac.get("/rl", headers=headers)
        assert r2.status_code == 429
        assert "Retry-After" in r2.headers

@pytest.mark.asyncio
async def test_missing_api_key():
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        config=RateLimitConfig(redis_enabled=False)
    )
    @app.get("/rl")
    async def rl():
        return {"ok": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/rl")
        assert r.status_code == 401
