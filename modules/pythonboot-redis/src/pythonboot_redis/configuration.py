"""Conditional native Redis clients and application-owned pool lifecycle."""

import logging

from redis import ConnectionPool
from redis.asyncio import ConnectionPool as AsyncConnectionPool

from pythonboot import auto_configuration, bean, conditional_on_missing_bean, conditional_on_property
from pythonboot_redis.client import AsyncRedisClient, RedisClient
from pythonboot_redis.properties import RedisProperties

logger = logging.getLogger(__name__)


@auto_configuration(order=2900, imports=(RedisProperties,))
@conditional_on_property("pythonboot.redis.enabled", having_value=True, match_if_missing=True)
class RedisPropertiesAutoConfiguration:
    """Register typed Redis connection configuration before resource factories."""


@auto_configuration(order=3000)
@conditional_on_property("pythonboot.redis.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.redis.mode", having_value="sync", match_if_missing=True)
class RedisSyncPoolAutoConfiguration:
    """Create a pool only when neither an application client nor a pool is available."""

    @bean(name="redisConnectionPool", destroy_method="disconnect")
    @conditional_on_missing_bean(ConnectionPool, RedisClient, "redisConnectionPool", "redisClient")
    def connection_pool(self, properties: RedisProperties) -> ConnectionPool:
        logger.info("Creating synchronous Redis connection pool with max_connections=%d.", properties.max_connections)
        return ConnectionPool.from_url(properties.connection_url("sync"), **properties.connection_options())


@auto_configuration(order=3000)
@conditional_on_property("pythonboot.redis.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.redis.mode", having_value="async")
class RedisAsyncPoolAutoConfiguration:
    """Create an asynchronous pool with awaited shutdown."""

    @bean(name="redisAsyncConnectionPool", destroy_method="disconnect")
    @conditional_on_missing_bean(
        AsyncConnectionPool, AsyncRedisClient, "redisAsyncConnectionPool", "redisAsyncClient",
    )
    def connection_pool(self, properties: RedisProperties) -> AsyncConnectionPool:
        logger.info("Creating asynchronous Redis connection pool with max_connections=%d.", properties.max_connections)
        return AsyncConnectionPool.from_url(properties.connection_url("async"), **properties.connection_options())


@auto_configuration(order=3100)
@conditional_on_property("pythonboot.redis.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.redis.mode", having_value="sync", match_if_missing=True)
class RedisSyncClientAutoConfiguration:
    """Register a native synchronous Redis client using the selected pool."""

    @bean(name="redisClient", destroy_method="close")
    @conditional_on_missing_bean(RedisClient, "redisClient")
    def client(self, pool: ConnectionPool) -> RedisClient:
        logger.info("Creating synchronous Redis client from the managed connection pool.")
        return RedisClient(connection_pool=pool)


@auto_configuration(order=3100)
@conditional_on_property("pythonboot.redis.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.redis.mode", having_value="async")
class RedisAsyncClientAutoConfiguration:
    """Register a native asynchronous Redis client without opening connections during import."""

    @bean(name="redisAsyncClient", destroy_method="aclose")
    @conditional_on_missing_bean(AsyncRedisClient, "redisAsyncClient")
    def client(self, pool: AsyncConnectionPool) -> AsyncRedisClient:
        logger.info("Creating asynchronous Redis client from the managed connection pool.")
        return AsyncRedisClient(connection_pool=pool)
