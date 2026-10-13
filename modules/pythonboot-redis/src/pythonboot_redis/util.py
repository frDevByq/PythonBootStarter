"""Synchronous static Redis operations resolved against the current application context."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from math import isfinite

from redis.lock import Lock

from pythonboot import ContextUtil
from pythonboot_redis.client import RedisClient, RedisKey, RedisResult, RedisValue


def validate_lock_options(timeout: float, blocking_timeout: float, sleep: float) -> None:
    """Require bounded acquisition and a positive finite lease."""
    if not isfinite(timeout) or timeout <= 0:
        raise ValueError("Lock timeout must be finite and positive")
    if not isfinite(blocking_timeout) or blocking_timeout < 0:
        raise ValueError("Lock blocking_timeout must be finite and non-negative")
    if not isfinite(sleep) or sleep <= 0:
        raise ValueError("Lock sleep must be finite and positive")


class RedisUtil:
    """Convenience methods backed by native RedisClient Beans, never a global client."""

    @staticmethod
    def get_client(*, name: str | None = None, qualifier: str | None = None) -> RedisClient:
        return ContextUtil.get_bean(RedisClient, name=name, qualifier=qualifier)

    @staticmethod
    def get(key: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return RedisUtil.get_client(name=name).get(key)

    @staticmethod
    def set(
        key: RedisKey, value: RedisValue, *, ex: int | timedelta | None = None,
        px: int | timedelta | None = None, nx: bool = False, xx: bool = False,
        keepttl: bool = False, name: str | None = None,
    ) -> bool | None:
        return RedisUtil.get_client(name=name).set(key, value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl)

    @staticmethod
    def delete(*keys: RedisKey, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).delete(*keys)

    @staticmethod
    def exists(*keys: RedisKey, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).exists(*keys)

    @staticmethod
    def expire(key: RedisKey, seconds: int | timedelta, *, name: str | None = None) -> bool:
        return RedisUtil.get_client(name=name).expire(key, seconds)

    @staticmethod
    def ttl(key: RedisKey, *, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).ttl(key)

    @staticmethod
    def incr(key: RedisKey, amount: int = 1, *, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).incr(key, amount)

    @staticmethod
    def decr(key: RedisKey, amount: int = 1, *, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).decr(key, amount)

    @staticmethod
    def hset(key: RedisKey, mapping: Mapping[RedisKey, RedisValue], *, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).hset(key, mapping=mapping)

    @staticmethod
    def hget(key: RedisKey, field: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return RedisUtil.get_client(name=name).hget(key, field)

    @staticmethod
    def hgetall(key: RedisKey, *, name: str | None = None) -> dict[RedisResult, RedisResult]:
        return RedisUtil.get_client(name=name).hgetall(key)

    @staticmethod
    def hdel(key: RedisKey, *fields: RedisKey, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).hdel(key, *fields)

    @staticmethod
    def lpush(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).lpush(key, *values)

    @staticmethod
    def rpush(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).rpush(key, *values)

    @staticmethod
    def lpop(key: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return RedisUtil.get_client(name=name).lpop(key)

    @staticmethod
    def rpop(key: RedisKey, *, name: str | None = None) -> RedisResult | None:
        return RedisUtil.get_client(name=name).rpop(key)

    @staticmethod
    def lrange(key: RedisKey, start: int = 0, end: int = -1, *, name: str | None = None) -> list[RedisResult]:
        return RedisUtil.get_client(name=name).lrange(key, start, end)

    @staticmethod
    def llen(key: RedisKey, *, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).llen(key)

    @staticmethod
    def sadd(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).sadd(key, *values)

    @staticmethod
    def smembers(key: RedisKey, *, name: str | None = None) -> set[RedisResult]:
        return RedisUtil.get_client(name=name).smembers(key)

    @staticmethod
    def srem(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).srem(key, *values)

    @staticmethod
    def zadd(key: RedisKey, mapping: Mapping[RedisKey, float], *, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).zadd(key, mapping)

    @staticmethod
    def zrange(key: RedisKey, start: int = 0, end: int = -1, *, name: str | None = None) -> list[RedisResult]:
        return RedisUtil.get_client(name=name).zrange(key, start, end)

    @staticmethod
    def zrem(key: RedisKey, *values: RedisValue, name: str | None = None) -> int:
        return RedisUtil.get_client(name=name).zrem(key, *values)

    @staticmethod
    def get_lock(
        key: RedisKey, *, timeout: float = 30, blocking_timeout: float = 5,
        sleep: float = 0.1, thread_local: bool = True, name: str | None = None,
    ) -> Lock:
        validate_lock_options(timeout, blocking_timeout, sleep)
        return RedisUtil.get_client(name=name).lock(
            key, timeout=timeout, blocking_timeout=blocking_timeout, sleep=sleep, thread_local=thread_local,
        )

    @staticmethod
    def acquire_lock(lock: Lock, *, blocking: bool = True) -> bool:
        return lock.acquire(blocking=blocking)

    @staticmethod
    def release_lock(lock: Lock) -> None:
        lock.release()

    @staticmethod
    def extend_lock(lock: Lock, seconds: float, *, replace_ttl: bool = False) -> bool:
        if not isfinite(seconds) or seconds <= 0:
            raise ValueError("Lock extension must be positive")
        return lock.extend(seconds, replace_ttl=replace_ttl)

    @staticmethod
    def lock_owned(lock: Lock) -> bool:
        return lock.owned()
