from pydantic import BaseModel
from typing import Optional

class RateLimitConfig(BaseModel):
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 20000
    api_key_header: str = "X-API-Key"
    user_id_header: str = "X-User-Id"
    redis_url: Optional[str] = "redis://localhost:6379/0"
    redis_enabled: bool = True
    # Future: configurable plan-based limits
