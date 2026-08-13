# AI Rate Limiter

A reusable FastAPI package for per-user and per-API-key sliding window rate limiting, with Redis and in-memory fallback support.

## Features
- Sliding window rate limiting per API key and per user
- Configurable per-minute, per-hour, per-day limits
- Redis backend with in-memory fallback
- Returns HTTP 429 with `Retry-After` header
- FastAPI middleware, easy integration
- Override identity resolution logic or headers

## Installation

For development:
```sh
pip install -e ".[test]"
```

For production use:
```sh
pip install git+https://github.com/YOUR_USERNAME/ai-rate-limiter.git
```

## Usage Example

```python
from fastapi import FastAPI
from ai_rate_limiter import RateLimiterMiddleware, RateLimitConfig
app = FastAPI()
app.add_middleware(
    RateLimiterMiddleware,
    config=RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=500,
        redis_enabled=True, # Requires Redis running
        redis_url="redis://localhost:6379/0",
        api_key_header="X-API-Key",
        user_id_header="X-User-Id"
    )
)
```

## Running the Example App

```sh
uvicorn example_app:app --reload
```

Then call:

```sh
curl -H "X-API-Key: test123" -H "X-User-Id: user1" http://localhost:8000/test
```

## Running Tests

```sh
pytest tests/
```

## Development

To set up for development:

```sh
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-rate-limiter.git
cd ai-rate-limiter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[test,dev]"

# Run tests
pytest tests/

# Run example app
uvicorn example_app:app --reload
```

## Configuration
- `requests_per_minute`, `requests_per_hour`, `requests_per_day`: Limits per identity
- `api_key_header`, `user_id_header`: Header names (default `X-API-Key`, `X-User-Id`)
- `redis_url`: Redis connection URL
- `redis_enabled`: Use Redis if available, fallback to memory store

## Custom Identity Resolution
Pass a custom async callback to the middleware for advanced extraction of user/API key from headers or cookies.

## License
MIT
