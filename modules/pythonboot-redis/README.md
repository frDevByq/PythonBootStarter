# pythonboot-redis

PythonBoot 的 redis-py 集成实现包。分发名为 `pythonboot-redis`，导入名为
`pythonboot_redis`；应用推荐安装依赖聚合包 `pythonboot-starter-redis`。

- Configuration Properties 绑定 `pythonboot.redis` 并注册 `RedisProperties` Bean。
- 默认同步模式，可选择异步；自动注入原生 `RedisClient` / `AsyncRedisClient`。
- 客户端类别名直接指向 redis-py 的 Redis 类，没有模板或代理包装。
- `RedisUtil` / `AsyncRedisUtil` 提供字符串、TTL、计数器、Hash、List、Set、有序集合操作。
- 原生分布式锁支持获取、释放、续期及归属判断；不通过直接删除键解锁。
- 工具类从当前 ContextVar 绑定的容器解析客户端，不持有全局客户端；支持命名 Bean。
- 默认池和客户端接入容器生命周期，异步关闭由容器等待。应用 Bean 优先。
- 创建对象不连接 Redis；首次命令才连接。异常按原生语义抛出，不静默返回默认值。

```yaml
pythonboot:
  redis:
    url: redis://localhost:6379/0
    mode: sync
    decode_responses: true
```

```python
from pythonboot import autowired, service
from pythonboot_redis import RedisClient, RedisUtil

@service
class CacheService:
    redis_client: RedisClient = autowired()

    def save(self, value: str) -> None:
        self.redis_client.set("example:value", value, ex=60)

RedisUtil.set("example:value", "hello", ex=60)
value = RedisUtil.get("example:value")
RedisUtil.rpush("example:list", "a", "b")
values = RedisUtil.lrange("example:list")
client = RedisUtil.get_client()
```

静态调用需要在已绑定容器的请求／生命周期中，独立任务使用 `ContextUtil.use(context)`。
异步模式注入 `AsyncRedisClient`，使用 `await AsyncRedisUtil.get(...)`；
不要在异步方法中直接执行同步客户端命令。
工具锁默认租期 30 秒、获取等待 5 秒；每次操作创建独立锁对象，成功获取后在 finally 中释放。
没有自动续期，超过租期需要业务显式续期；释放过期或非本方持有的锁会抛出原生异常。

完整配置、公共 API 和锁示例见 [中文文档](../../viteDocs/docs/zh/redis.md)、
[English documentation](../../viteDocs/docs/en/redis.md) 和 [示例](../../examples/redis/README.md)。

## English

The implementation distribution is `pythonboot-redis`; import `pythonboot_redis`.
Install `pythonboot-starter-redis` in applications. Configuration Properties bind `pythonboot.redis`.
Native client aliases support concrete-class Bean injection; sync is the default, async is optional.
Static utilities resolve the current application context and provide common commands and native locks.
Default clients and pools are lifecycle-managed without connecting during import or construction.
Application Beans override defaults; providers declare cleanup for custom resources.
Locks use native ownership tokens, bounded acquisition, explicit renewal, and atomic release.
There is no automatic renewal. Use a distinct lock object per task or thread and release in finally.
Standalone tasks bind their container through `ContextUtil.use(context)`.
