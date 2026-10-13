"""Redis client injection, static helpers, List commands and native distributed locks."""

from pathlib import Path

from pydantic import BaseModel, Field

from pythonboot import autowired, service
from pythonboot_redis import AsyncRedisClient, AsyncRedisUtil
from pythonboot_web import PythonBootApplication, controller, get, post, pythonboot_application


class Message(BaseModel):
    """Validated Redis queue input."""

    value: str = Field(min_length=1, title="消息内容", description="需要加入队列的消息")


@service
class QueueService:
    """Use the injected native client and context-resolved utilities interchangeably."""

    redis_client: AsyncRedisClient = autowired()

    async def messages(self) -> list[str]:
        return await self.redis_client.lrange("examples:queue", 0, -1)

    async def append(self, value: str) -> int:
        lock = await AsyncRedisUtil.get_lock("locks:examples:queue", timeout=30, blocking_timeout=5)
        if not await AsyncRedisUtil.acquire_lock(lock):
            raise TimeoutError("Could not acquire the queue lock")
        try:
            await AsyncRedisUtil.set("examples:last-message", value, ex=60)
            return await AsyncRedisUtil.rpush("examples:queue", value)
        finally:
            await AsyncRedisUtil.release_lock(lock)


@controller(prefix="/redis", tags=["Redis 示例"])
class RedisController:
    """Expose a queue example backed by the configured Redis server."""

    queue_service: QueueService = autowired()

    @get("/messages", summary="查询消息列表", response_model=list[str])
    async def messages(self) -> list[str]:
        return await self.queue_service.messages()

    @post("/messages", summary="加锁追加消息", response_model=int)
    async def append(self, payload: Message) -> int:
        return await self.queue_service.append(payload.value)


@pythonboot_application(scan_packages=("examples.redis",))
class Application(PythonBootApplication):
    """Start the Redis client through installed entry-point auto-configuration."""


application = Application(config_dir=Path(__file__).parent / "config")
app = application.app
