import time
from typing import Optional, Tuple
from redis.asyncio import Redis, ConnectionError as RedisConnectionError
from collections import defaultdict, deque
import asyncio

class SlidingWindowRedis:
    def __init__(self, redis: Redis, prefix: str = "rate:"):
        self.redis = redis
        self.prefix = prefix

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, Optional[int]]:
        now = int(time.time())
        window_start = now - window_seconds
        redis_key = f"{self.prefix}{key}:{window_seconds}"
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zadd(redis_key, {str(now): now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_seconds)
        try:
            results = await pipe.execute()
            count = results[2]  # Get count from pipeline results
        except RedisConnectionError:
            raise
        allowed = count <= limit
        retry_after = None
        if not allowed:
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now)
        return allowed, retry_after

class SlidingWindowMemory:
    def __init__(self):
        self.data = defaultdict(deque)
        self.lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, Optional[int]]:
        now = int(time.time())
        window_start = now - window_seconds
        # Include window_seconds in the key to separate different time windows
        storage_key = f"{key}:{window_seconds}"
        async with self.lock:
            q = self.data[storage_key]
            # Remove expired
            while q and q[0] <= window_start:
                q.popleft()
            q.append(now)
            allowed = len(q) <= limit
            retry_after = None
            if not allowed:
                retry_after = q[0] + window_seconds - now
            return allowed, retry_after
