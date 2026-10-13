# Redis Starter

## 安装与模块

```bash
uv add pythonboot-starter-redis
```

依赖链：`pythonboot-starter-redis` → `pythonboot-redis` → `pythonboot`、`redis`。
redis-py 的 Python 分发名是 `redis`，不需要另装 Redis 驱动；需要可用的 Redis 服务。
Starter 聚合依赖，实现包负责配置和客户端装配。业务导入 `pythonboot_redis`。

## Configuration Properties

`RedisProperties` 使用 `@configuration_properties("pythonboot.redis")` 注册配置 Bean。

```yaml
pythonboot:
  redis:
    enabled: true
    mode: sync
    url: redis://localhost:6379/0
    decode_responses: true
    encoding: utf-8
    max_connections: 50
    socket_timeout: 5
    socket_connect_timeout: 5
    health_check_interval: 30
```

| `pythonboot.redis` 下的属性 | 默认值 | 用途 |
| --- | --- | --- |
| `enabled` | `true` | YAML 选择是否启用自动配置 |
| `mode` | `sync` | YAML 选择 `sync` 或 `async` |
| `url` | `redis://localhost:6379/0` | 地址、端口、认证和数据库，支持原生 redis/rediss/unix URL |
| `username` | 未设置 | Redis ACL 用户名 |
| `password` | 未设置 | 密码，配置 Bean 使用 SecretStr |
| `decode_responses` | `true` | 返回字符串；关闭时返回 bytes |
| `encoding` | `utf-8` | 编解码方式 |
| `max_connections` | `50` | 最大池连接数，至少 1；默认池耗尽时按原生行为报错 |
| `socket_timeout` | `5` | Socket 操作超时秒数，必须大于 0 |
| `socket_connect_timeout` | `5` | 建连超时秒数，必须大于 0 |
| `health_check_interval` | `30` | 连接健康检查间隔秒数，0 关闭 |

URL 和密码使用 SecretStr，配置展示不输出明文；URL 中的用户、密码、数据库及查询参数
仍遵循 redis-py 原生优先级，URL 中指定的选项优先于同名关键字参数。
不要在 URL 中重复设置需要通过独立属性控制的参数。
普通字段可通过 `PYTHONBOOT_REDIS_URL`、`PYTHONBOOT_REDIS_PASSWORD` 等环境变量覆盖。
`enabled` 和 `mode` 是自动配置选择条件，必须在 YAML 中设置，不能通过环境变量切换模式。

## 原生 RedisClient 注入

`RedisClient` 是 `redis.Redis` 的类别名；`AsyncRedisClient` 是 `redis.asyncio.Redis`
的类别名。它们不是 RedisTemplate，也没有额外封装，可以使用原生 pipeline、Pub/Sub、
Lua、事务及其他命令。Redis 命令无需 SQLAlchemy 风格的 commit。

```python
from pythonboot import autowired, service
from pythonboot_redis import RedisClient

@service
class CacheService:
    redis_client: RedisClient = autowired()

    def save(self, user_id: int, name: str) -> None:
        self.redis_client.set(f"user:{user_id}:name", name, ex=300)
```

异步场景将 YAML 的 `mode` 改为 `async`：

```python
from pythonboot import autowired, service
from pythonboot_redis import AsyncRedisClient

@service
class CacheService:
    redis_client: AsyncRedisClient = autowired()

    async def save(self, user_id: int, name: str) -> None:
        await self.redis_client.set(f"user:{user_id}:name", name, ex=300)
```

客户端是应用级单例，通过连接池执行命令；业务不要关闭容器管理的客户端或池。
pipeline、Pub/Sub 和锁对象由具体操作创建与释放，不跨并发任务共享操作状态。

## RedisUtil 静态工具

```python
from pythonboot_redis import RedisUtil

RedisUtil.set("example:name", "Alice", ex=60)
value = RedisUtil.get("example:name")
RedisUtil.hset("example:user", {"name": "Alice", "age": 20})
RedisUtil.rpush("example:queue", "first", "second")
items = RedisUtil.lrange("example:queue")
client = RedisUtil.get_client()
```

异步工具使用 `AsyncRedisUtil`，包括获取客户端在内都显式 await：

```python
from pythonboot_redis import AsyncRedisUtil

await AsyncRedisUtil.set("example:name", "Alice", ex=60)
value = await AsyncRedisUtil.get("example:name")
client = await AsyncRedisUtil.get_client()
```

工具类每次通过 `ContextUtil` 解析当前容器，不保存全局可变客户端。
请求中的容器绑定由 Web 模块处理；独立任务显式绑定：

```python
from pythonboot import ContextUtil
from pythonboot_redis import RedisUtil

with ContextUtil.use(context):
    value = RedisUtil.get("example:name")
```

`context` 为任务所属 ApplicationContext，例如应用的 `application.context`。
没有容器绑定、缺少客户端或存在未限定的多候选时明确报错。
同步工具只解析同步客户端，异步工具只解析异步客户端，不静默互相转换。
异步方法中使用异步工具，避免同步命令阻塞事件循环。

### 常用方法

同步与异步工具提供同名方法，异步版本全部 await。命令方法和 `get_lock` 都支持
关键字 `name` 选择客户端 Bean；`get_client` 另支持 `qualifier`。
锁操作方法接收原生锁对象，直接使用该对象绑定的客户端。

| 分类 | 方法与参数 |
| --- | --- |
| 客户端 | `get_client(*, name=None, qualifier=None)` |
| 字符串 | `get(key)`、`set(key, value, *, ex=None, px=None, nx=False, xx=False, keepttl=False)` |
| 键和 TTL | `delete(*keys)`、`exists(*keys)`、`expire(key, seconds)`、`ttl(key)` |
| 计数器 | `incr(key, amount=1)`、`decr(key, amount=1)` |
| Hash | `hset(key, mapping)`、`hget(key, field)`、`hgetall(key)`、`hdel(key, *fields)` |
| List | `lpush/rpush(key, *values)`、`lpop/rpop(key)`、`lrange(key, start=0, end=-1)`、`llen(key)` |
| Set | `sadd/srem(key, *values)`、`smembers(key)` |
| Sorted Set | `zadd(key, mapping)`、`zrange(key, start=0, end=-1)`、`zrem(key, *values)` |
| 锁 | `get_lock(key, *, timeout=30, blocking_timeout=5, sleep=0.1, thread_local=True)` |
| 获取锁 | `acquire_lock(lock, *, blocking=True)` |
| 释放与续期 | `release_lock(lock)`、`extend_lock(lock, seconds, *, replace_ttl=False)` |
| 归属 | `lock_owned(lock)` |

返回值保留 redis-py 语义，例如 `set` 返回 True 或 None，`exists` 返回数量，
`ttl` 返回 -1 表示无过期时间、-2 表示键不存在。值支持 str、bytes、int、float，
工具不隐式序列化对象或 JSON。列表范围的 end 是包含边界，-1 为最后一项。

## 分布式锁

工具使用 redis-py 原生 Lock，保留令牌校验和 Lua 原子释放／续期，不直接 DELETE 锁键。
获取失败返回 False，命令或释放失败抛出原生异常。

```python
lock = RedisUtil.get_lock("locks:order:123", timeout=30, blocking_timeout=5)
if not RedisUtil.acquire_lock(lock):
    raise TimeoutError("Could not acquire the order lock")
try:
    process_order()
finally:
    RedisUtil.release_lock(lock)
```

```python
lock = await AsyncRedisUtil.get_lock("locks:order:123", timeout=30, blocking_timeout=5)
if not await AsyncRedisUtil.acquire_lock(lock):
    raise TimeoutError("Could not acquire the order lock")
try:
    await process_order()
finally:
    await AsyncRedisUtil.release_lock(lock)
```

`get_lock` 只创建锁对象，不获取锁；每次竞争创建自己的锁对象，不能并发共享。
默认租期 30 秒、阻塞等待 5 秒、轮询间隔 0.1 秒；租期和轮询间隔必须有限且大于 0，
等待必须有限且不小于 0。非阻塞获取使用 `blocking=False`。

没有自动 watchdog 续期；需要续期时调用 `extend_lock(lock, seconds)`，默认增加 TTL，
`replace_ttl=True` 改为替换剩余 TTL。只能续期当前仍持有的锁，归属判断不是原子释放的替代。
租期结束后其他客户端可获得锁，原持有者释放或续期会因失去所有权而报错。
业务必须在租期内完成或主动续期。该锁不提供 fencing token，也不保证 Redis 故障转移期间
严格互斥；多命令需要原子性时使用原生事务或 Lua，锁本身不提供事务回滚。

## 自动配置与生命周期

自动配置入口名称为 `redis`，配置属性、池、客户端的装配 order 分别为 2900、3000、3100。
池和客户端的条件使用 `@conditional_on_missing_bean`，应用定义优先。

| Bean | 类型 | 模式与关闭方式 |
| --- | --- | --- |
| `redisProperties` | `RedisProperties` | 模块启用 |
| `redisConnectionPool` | `redis.ConnectionPool` | sync；disconnect |
| `redisClient` | `RedisClient` | sync；close |
| `redisAsyncConnectionPool` | `redis.asyncio.ConnectionPool` | async；await disconnect |
| `redisAsyncClient` | `AsyncRedisClient` | async；await aclose |

默认客户端依赖池，容器先关闭客户端再关闭池。没有导入时连接、启动探活或安装副作用。
Web 场景随 ASGI lifespan 启停容器；独立程序使用核心容器生命周期。
用户提供客户端时不再创建默认池；只提供池时默认客户端复用该池。
自定义客户端／池的关闭责任由其提供方通过 Bean 元数据声明。

多 Redis 实例使用应用配置属性和命名客户端 Bean，注入时使用
`autowired(name="cacheRedisClient")`，工具使用 `name="cacheRedisClient"`。
当前默认装配面向 standalone Redis，Sentinel／Cluster 等拓扑由应用按原生客户端 API
显式配置，不通过 URL 猜测拓扑；注入类型须与提供的 Bean 类型匹配。

## 公共 API 与示例

`pythonboot_redis` 和 `pythonboot_starter_redis` 显式导出 `RedisClient`、`AsyncRedisClient`、
`RedisProperties`、`RedisUtil`、`AsyncRedisUtil`。原生锁、连接池和异常从 `redis` 对应模块导入。
完整异步 Web 示例位于仓库 `examples/redis/`，演示原生客户端注入、静态工具、List 与分布式锁。
