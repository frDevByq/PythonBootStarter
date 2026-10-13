"""Asynchronous static Redis operations resolved against the current application context."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from math import isfinite

from redis.asyncio.lock import Lock

from pythonboot import ContextUtil
from pythonboot_redis.client import AsyncRedisClient, RedisKey, RedisResult, RedisValue
from pythonboot_redis.util import validate_lock_options


class AsyncRedisUtil:
    """Awaitable Redis helpers without blocking calls or globally cached clients."""

    @staticmethod
    async def get_client(*, name: str | None = None, qualifier: str | None = None) -> AsyncRedisClient:
        return await ContextUtil.aget_bean(AsyncRedisClient, name=name, qualifier=qualifier)

    @staticmethod
    async def get(key: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return await (await AsyncRedisUtil.get_client(name=name)).get(key)

    @staticmethod
    async def set(
        key: RedisKey, value: RedisValue, *, ex: int | timedelta | None = None,
        px: int | timedelta | None = None, nx: bool = False, xx: bool = False,
        keepttl: bool = False, name: str | None = None,
    ) -> bool | None:
        client = await AsyncRedisUtil.get_client(name=name)
        return await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl)

    @staticmethod
    async def delete(*keys: RedisKey, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).delete(*keys)

    @staticmethod
    async def exists(*keys: RedisKey, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).exists(*keys)

    @staticmethod
    async def expire(key: RedisKey, seconds: int | timedelta, *, name: str | None = None) -> bool:
        return await (await AsyncRedisUtil.get_client(name=name)).expire(key, seconds)

    @staticmethod
    async def ttl(key: RedisKey, *, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).ttl(key)

    @staticmethod
    async def incr(key: RedisKey, amount: int = 1, *, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).incr(key, amount)

    @staticmethod
    async def decr(key: RedisKey, amount: int = 1, *, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).decr(key, amount)

    @staticmethod
    async def hset(key: RedisKey, mapping: Mapping[RedisKey, RedisValue], *, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).hset(key, mapping=mapping)

    @staticmethod
    async def hget(key: RedisKey, field: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return await (await AsyncRedisUtil.get_client(name=name)).hget(key, field)

    @staticmethod
    async def hgetall(key: RedisKey, *, name: str | None = None) -> dict[RedisResult, RedisResult]:
        return await (await AsyncRedisUtil.get_client(name=name)).hgetall(key)

    @staticmethod
    async def hdel(key: RedisKey, *fields: RedisKey, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).hdel(key, *fields)

    @staticmethod
    async def lpush(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).lpush(key, *values)

    @staticmethod
    async def rpush(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).rpush(key, *values)

    @staticmethod
    async def lpop(key: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return await (await AsyncRedisUtil.get_client(name=name)).lpop(key)

    @staticmethod
    async def rpop(key: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return await (await AsyncRedisUtil.get_client(name=name)).rpop(key)

    @staticmethod
    async def lrange(key: RedisKey, start: int = 0, end: int = -1, *, name: str | None = None) -> list[RedisResult]:
        return await (await AsyncRedisUtil.get_client(name=name)).lrange(key, start, end)

    @staticmethod
    async def llen(key: RedisKey, *, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).llen(key)

    @staticmethod
    async def sadd(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).sadd(key, *values)

    @staticmethod
    async def smembers(key: RedisKey, *, name: str | None = None) -> set[RedisResult]:
        return await (await AsyncRedisUtil.get_client(name=name)).smembers(key)

    @staticmethod
    async def srem(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).srem(key, *values)

    @staticmethod
    async def zadd(key: RedisKey, mapping: Mapping[RedisKey, float], *, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).zadd(key, mapping)

    @staticmethod
    async def zrange(key: RedisKey, start: int = 0, end: int = -1, *, name: str | None = None) -> list[RedisResult]:
        return await (await AsyncRedisUtil.get_client(name=name)).zrange(key, start, end)

    @staticmethod
    async def zrem(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return await (await AsyncRedisUtil.get_client(name=name)).zrem(key, *values)

    @staticmethod
    async def get_lock(
        key: RedisKey, *, timeout: float = 30, blocking_timeout: float = 5,
        sleep: float = 0.1, thread_local: bool = True, name: str | None = None,
    ) -> Lock:
        validate_lock_options(timeout, blocking_timeout, sleep)
        client = await AsyncRedisUtil.get_client(name=name)
        return client.lock(
            key, timeout=timeout, blocking_timeout=blocking_timeout, sleep=sleep, thread_local=thread_local,
        )

    @staticmethod
    async def acquire_lock(lock: Lock, *, blocking: bool = True) -> bool:
        return await lock.acquire(blocking=blocking)

    @staticmethod
    async def release_lock(lock: Lock) -> None:
        await lock.release()

    @staticmethod
    async def extend_lock(lock: Lock, seconds: float, *, replace_ttl: bool = False) -> bool:
        if not isfinite(seconds) or seconds <= 0:
            raise ValueError("Lock extension must be positive")
        return await lock.extend(seconds, replace_ttl=replace_ttl)

    @staticmethod
    async def lock_owned(lock: Lock) -> bool:
        return await lock.owned()
