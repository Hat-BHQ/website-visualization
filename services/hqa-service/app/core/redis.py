from __future__ import annotations

from uuid import uuid4

import redis

_LOCK_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
else
  return 0
end
"""


def create_redis_client(redis_url: str) -> redis.Redis:
    return redis.Redis.from_url(redis_url, decode_responses=True)


class RedisLockManager:
    def __init__(self, client: redis.Redis, ttl_seconds: int = 3600) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    def acquire(self, key: str, owner: str | None = None) -> str | None:
        token = owner or str(uuid4())
        acquired = self.client.set(key, token, nx=True, ex=self.ttl_seconds)
        if acquired:
            return token
        return None

    def current_owner(self, key: str) -> str | None:
        return self.client.get(key)

    def release(self, key: str, owner: str) -> bool:
        result = self.client.eval(_LOCK_RELEASE_SCRIPT, 1, key, owner)
        return bool(result)
