from fastapi import FastAPI, Request
from ai_rate_limiter import RateLimiterMiddleware, RateLimitConfig

app = FastAPI()

app.add_middleware(
    RateLimiterMiddleware,
    config=RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=10,
        requests_per_day=100,
        redis_enabled=False  # Set True with Redis running
    )
)

@app.get("/test")
async def test_endpoint(request: Request):
    return {"message": "Request allowed!"}
