"""Demonstrate synchronous and asynchronous Redis commands through HTTP."""

from typing import Any

from pythonboot import autowired
from pythonboot_web import controller, post
from starter_example.domain.common import BaseResult
from starter_example.service.redis_service import RedisService
from starter_example.service.sync_redis_service import SyncRedisService


@controller(prefix="/redis", tags=["Redis 示例"])
class RedisController:
    redis_service: RedisService = autowired()
    sync_redis_service: SyncRedisService = autowired()

    @post("/demo", summary="演示异步 Redis 全部工具与分布式锁", response_model=BaseResult[dict[str, Any]])
    async def asynchronous(self) -> BaseResult[dict[str, Any]]:
        return BaseResult.success(await self.redis_service.demonstrate())

    @post("/sync/demo", summary="演示同步 Redis 全部工具与分布式锁", response_model=BaseResult[dict[str, Any]])
    def synchronous(self) -> BaseResult[dict[str, Any]]:
        return BaseResult.success(self.sync_redis_service.demonstrate())
