"""Exercise every public Redis utility with isolated keys and bounded native locks."""

from typing import Any
from uuid import uuid4

from pythonboot import autowired, service
from pythonboot_starter_redis import RedisClient, RedisUtil
from starter_example.config.logging_aspect import logged


@service
class SyncRedisService:
    redis_client: RedisClient = autowired(qualifier="sync")

    @logged
    def demonstrate(self) -> dict[str, Any]:
        prefix = f"starter-example:{uuid4().hex}"
        key, counter, hash_key, list_key, set_key, sorted_key, lock_key = (
            f"{prefix}:{suffix}" for suffix in ("value", "counter", "hash", "list", "set", "sorted", "lock")
        )
        keys = (key, counter, hash_key, list_key, set_key, sorted_key)
        results: dict[str, Any] = {}
        lock = None
        acquired = False
        try:
            results["native_ping"] = self.redis_client.ping()
            client = RedisUtil.get_client(name="exampleSyncRedisClient")
            results["named_client"] = client is self.redis_client
            results["set"] = RedisUtil.set(key, "hello", ex=60, nx=True)
            results["get"] = RedisUtil.get(key)
            results["exists"] = RedisUtil.exists(key)
            results["expire"] = RedisUtil.expire(key, 120)
            results["ttl"] = RedisUtil.ttl(key)
            results["incr"] = RedisUtil.incr(counter, 3)
            results["decr"] = RedisUtil.decr(counter)
            results["hset"] = RedisUtil.hset(hash_key, {"name": "Alice", "role": "reader"})
            results["hget"] = RedisUtil.hget(hash_key, "name")
            results["hgetall"] = RedisUtil.hgetall(hash_key)
            results["hdel"] = RedisUtil.hdel(hash_key, "role")
            results["lpush"] = RedisUtil.lpush(list_key, "first")
            results["rpush"] = RedisUtil.rpush(list_key, "last")
            results["lrange"] = RedisUtil.lrange(list_key)
            results["lpop"] = RedisUtil.lpop(list_key)
            results["rpop"] = RedisUtil.rpop(list_key)
            results["sadd"] = RedisUtil.sadd(set_key, "a", "b")
            results["smembers"] = sorted(RedisUtil.smembers(set_key))
            results["srem"] = RedisUtil.srem(set_key, "b")
            results["zadd"] = RedisUtil.zadd(sorted_key, {"low": 1.0, "high": 2.0})
            results["zrange"] = RedisUtil.zrange(sorted_key)
            results["zrem"] = RedisUtil.zrem(sorted_key, "high")
            lock = RedisUtil.get_lock(lock_key, timeout=30, blocking_timeout=5)
            acquired = RedisUtil.acquire_lock(lock)
            if not acquired:
                raise TimeoutError("Could not acquire the demo lock")
            results["acquire_lock"] = acquired
            results["lock_owned"] = RedisUtil.lock_owned(lock)
            results["extend_lock"] = RedisUtil.extend_lock(lock, 5)
            RedisUtil.release_lock(lock)
            acquired = False
            results["released_lock_owned"] = RedisUtil.lock_owned(lock)
            results["delete"] = RedisUtil.delete(*keys)
            results["remaining_keys"] = RedisUtil.exists(*keys)
            return results
        finally:
            if acquired and lock is not None:
                RedisUtil.release_lock(lock)
            RedisUtil.delete(*keys)
