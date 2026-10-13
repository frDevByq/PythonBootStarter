"""Concrete aliases of native redis-py client classes for Bean injection."""

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

RedisClient = Redis
AsyncRedisClient = AsyncRedis

RedisKey = str | bytes
RedisValue = str | bytes | int | float
RedisResult = str | bytes
