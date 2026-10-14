"""Exercise every public Redis utility with isolated keys and bounded native locks."""

from typing import Any
from uuid import uuid4

from pythonboot import autowired, service
from pythonboot_starter_redis import AsyncRedisClient, AsyncRedisUtil
from starter_example.config.logging_aspect import logged


@service
class RedisService:
    redis_client: AsyncRedisClient = autowired()

    @logged
    async def demonstrate(self) -> dict[str, Any]:
        prefix = f"starter-example:{uuid4().hex}"
        key, counter, hash_key, list_key, set_key, sorted_key, lock_key = (
            f"{prefix}:{suffix}" for suffix in ("value", "counter", "hash", "list", "set", "sorted", "lock")
        )
        keys = (key, counter, hash_key, list_key, set_key, sorted_key)
        results: dict[str, Any] = {}
        lock = None
        acquired = False
        try:
            results["native_ping"] = await self.redis_client.ping()
            client = await AsyncRedisUtil.get_client(name="redisAsyncClient")
            results["named_client"] = client is self.redis_client
            results["set"] = await AsyncRedisUtil.set(key, "hello", ex=60, nx=True)
            results["get"] = await AsyncRedisUtil.get(key)
            results["exists"] = await AsyncRedisUtil.exists(key)
            results["expire"] = await AsyncRedisUtil.expire(key, 120)
            results["ttl"] = await AsyncRedisUtil.ttl(key)
            results["incr"] = await AsyncRedisUtil.incr(counter, 3)
            results["decr"] = await AsyncRedisUtil.decr(counter)
            results["hset"] = await AsyncRedisUtil.hset(hash_key, {"name": "Alice", "role": "reader"})
            results["hget"] = await AsyncRedisUtil.hget(hash_key, "name")
            results["hgetall"] = await AsyncRedisUtil.hgetall(hash_key)
            results["hdel"] = await AsyncRedisUtil.hdel(hash_key, "role")
            results["lpush"] = await AsyncRedisUtil.lpush(list_key, "first")
            results["rpush"] = await AsyncRedisUtil.rpush(list_key, "last")
            results["lrange"] = await AsyncRedisUtil.lrange(list_key)
            results["lpop"] = await AsyncRedisUtil.lpop(list_key)
            results["rpop"] = await AsyncRedisUtil.rpop(list_key)
            results["sadd"] = await AsyncRedisUtil.sadd(set_key, "a", "b")
            results["smembers"] = sorted(await AsyncRedisUtil.smembers(set_key))
            results["srem"] = await AsyncRedisUtil.srem(set_key, "b")
            results["zadd"] = await AsyncRedisUtil.zadd(sorted_key, {"low": 1.0, "high": 2.0})
            results["zrange"] = await AsyncRedisUtil.zrange(sorted_key)
            results["zrem"] = await AsyncRedisUtil.zrem(sorted_key, "high")
            lock = await AsyncRedisUtil.get_lock(lock_key, timeout=30, blocking_timeout=5)
            acquired = await AsyncRedisUtil.acquire_lock(lock)
            if not acquired:
                raise TimeoutError("Could not acquire the demo lock")
            results["acquire_lock"] = acquired
            results["lock_owned"] = await AsyncRedisUtil.lock_owned(lock)
            results["extend_lock"] = await AsyncRedisUtil.extend_lock(lock, 5)
            await AsyncRedisUtil.release_lock(lock)
            acquired = False
            results["released_lock_owned"] = await AsyncRedisUtil.lock_owned(lock)
            results["delete"] = await AsyncRedisUtil.delete(*keys)
            results["remaining_keys"] = await AsyncRedisUtil.exists(*keys)
            return results
        finally:
            if acquired and lock is not None:
                await AsyncRedisUtil.release_lock(lock)
            await AsyncRedisUtil.delete(*keys)
