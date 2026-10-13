# Redis Starter

## Installation and modules

```bash
uv add pythonboot-starter-redis
```

Dependency chain: `pythonboot-starter-redis` → `pythonboot-redis` → `pythonboot` and `redis`.
The redis-py distribution is named `redis`; no separate driver is required. Supply a reachable Redis
server. The Starter aggregates dependencies; import implementation APIs from `pythonboot_redis`.

## Configuration Properties

`RedisProperties` registers through `@configuration_properties("pythonboot.redis")`.

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

| Property under `pythonboot.redis` | Default | Purpose |
| --- | --- | --- |
| `enabled` | `true` | Enable auto-configuration through YAML |
| `mode` | `sync` | Select `sync` or `async` through YAML |
| `url` | `redis://localhost:6379/0` | Native redis/rediss/unix URL including authentication and database |
| `username` | Unset | Redis ACL user |
| `password` | Unset | SecretStr password |
| `decode_responses` | `true` | Return strings; false returns bytes |
| `encoding` | `utf-8` | Encoding and decoding |
| `max_connections` | `50` | Pool capacity, minimum 1; exhausted default pools raise natively |
| `socket_timeout` | `5` | Positive socket operation timeout in seconds |
| `socket_connect_timeout` | `5` | Positive connection timeout in seconds |
| `health_check_interval` | `30` | Health check interval; 0 disables checks |

URL and password use SecretStr to avoid plaintext configuration representations. Native URL option
precedence remains intact: URL options override matching keyword arguments. Avoid specifying the
same option both in the URL and in individual properties. Ordinary fields support environment
overrides such as `PYTHONBOOT_REDIS_URL` and `PYTHONBOOT_REDIS_PASSWORD`. Configure `enabled` and
`mode` in YAML because auto-configuration conditions do not read environment mode switches.

## Native client injection

`RedisClient` is a concrete class alias of `redis.Redis`; `AsyncRedisClient` aliases `redis.asyncio.Redis`.
There is no RedisTemplate or wrapper. Native pipelines, Pub/Sub, Lua, transactions, and commands remain
available. Redis commands do not require a SQLAlchemy-style commit.

```python
from pythonboot import autowired, service
from pythonboot_redis import RedisClient

@service
class CacheService:
    redis_client: RedisClient = autowired()

    def save(self, user_id: int, name: str) -> None:
        self.redis_client.set(f"user:{user_id}:name", name, ex=300)
```

Select `mode: async` for asynchronous business code:

```python
from pythonboot import autowired, service
from pythonboot_redis import AsyncRedisClient

@service
class CacheService:
    redis_client: AsyncRedisClient = autowired()

    async def save(self, user_id: int, name: str) -> None:
        await self.redis_client.set(f"user:{user_id}:name", name, ex=300)
```

Clients are application singletons using pools. Do not close container-managed clients in business code.
Create and release pipelines, Pub/Sub, and lock objects per operation rather than sharing operation state
between concurrent tasks.

## Static utilities

```python
from pythonboot_redis import RedisUtil

RedisUtil.set("example:name", "Alice", ex=60)
value = RedisUtil.get("example:name")
RedisUtil.hset("example:user", {"name": "Alice", "age": 20})
RedisUtil.rpush("example:queue", "first", "second")
items = RedisUtil.lrange("example:queue")
client = RedisUtil.get_client()
```

All asynchronous utility methods, including client resolution, are awaited:

```python
from pythonboot_redis import AsyncRedisUtil

await AsyncRedisUtil.set("example:name", "Alice", ex=60)
value = await AsyncRedisUtil.get("example:name")
client = await AsyncRedisUtil.get_client()
```

Utilities resolve the current container through ContextUtil without a global mutable client. Web
requests already bind their context. Standalone tasks explicitly bind the owning ApplicationContext:

```python
from pythonboot import ContextUtil
from pythonboot_redis import RedisUtil

with ContextUtil.use(context):
    value = RedisUtil.get("example:name")
```

For example, `context` may be `application.context`. Missing bindings, missing clients, and ambiguous
unqualified candidates raise errors. Sync helpers never select async clients or vice versa. Use async
helpers in async methods to avoid blocking the event loop.

### Common methods

Sync and async utilities have matching method names. Command helpers and `get_lock` accept keyword
`name` for client selection; `get_client` also accepts `qualifier`. Lock-operation helpers receive
native lock objects and use the client already associated with each object.

| Category | Methods and arguments |
| --- | --- |
| Client | `get_client(*, name=None, qualifier=None)` |
| Strings | `get(key)`, `set(key, value, *, ex=None, px=None, nx=False, xx=False, keepttl=False)` |
| Keys and TTL | `delete(*keys)`, `exists(*keys)`, `expire(key, seconds)`, `ttl(key)` |
| Counters | `incr(key, amount=1)`, `decr(key, amount=1)` |
| Hash | `hset(key, mapping)`, `hget(key, field)`, `hgetall(key)`, `hdel(key, *fields)` |
| List | `lpush/rpush(key, *values)`, `lpop/rpop(key)`, `lrange(key, start=0, end=-1)`, `llen(key)` |
| Set | `sadd/srem(key, *values)`, `smembers(key)` |
| Sorted Set | `zadd(key, mapping)`, `zrange(key, start=0, end=-1)`, `zrem(key, *values)` |
| Lock | `get_lock(key, *, timeout=30, blocking_timeout=5, sleep=0.1, thread_local=True)` |
| Acquire | `acquire_lock(lock, *, blocking=True)` |
| Release and renew | `release_lock(lock)`, `extend_lock(lock, seconds, *, replace_ttl=False)` |
| Ownership | `lock_owned(lock)` |

Return values preserve native semantics: set returns True or None, exists returns a count, TTL -1
means no expiration and -2 means missing. Values support str, bytes, int, and float without implicit
JSON or object serialization. List range end is inclusive and -1 selects the last item.

## Distributed locks

Native redis-py Lock provides ownership tokens and Lua-based atomic release and renewal. Helpers do
not delete lock keys directly. Acquisition failure returns False; command and ownership errors propagate.

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

`get_lock` constructs a lock without acquiring it. Create a separate object per contender; never share
one concurrently. Defaults: 30-second lease, 5-second acquisition wait, 0.1-second polling interval.
Lease and polling interval must be positive and finite; acquisition wait is finite and non-negative.
Use `blocking=False` for immediate acquisition attempts.

There is no automatic watchdog renewal. `extend_lock(lock, seconds)` adds to the remaining TTL;
`replace_ttl=True` replaces it. Only the current owner can renew or release. Ownership inspection does
not replace atomic release. Other clients may acquire after lease expiration, and former owners then
receive native ownership errors. Finish within the lease or renew explicitly. These locks do not provide
fencing tokens or strict mutual exclusion across Redis failover. Use native transactions or Lua when
multiple commands require atomicity; locks do not roll back commands.

## Auto-configuration and lifecycle

Entry-point name: `redis`. Properties, pools, and clients assemble at orders 2900, 3000, and 3100.
Default pools and clients use conditional-on-missing-Bean semantics; application definitions take priority.

| Bean | Type | Mode and cleanup |
| --- | --- | --- |
| `redisProperties` | `RedisProperties` | Module enabled |
| `redisConnectionPool` | `redis.ConnectionPool` | sync; disconnect |
| `redisClient` | `RedisClient` | sync; close |
| `redisAsyncConnectionPool` | `redis.asyncio.ConnectionPool` | async; await disconnect |
| `redisAsyncClient` | `AsyncRedisClient` | async; await aclose |

The client depends on the pool, so the container closes the client before disconnecting the pool.
No connection, startup ping, or installation happens during import or construction. Web applications
use the existing ASGI lifespan; standalone programs own the core container lifecycle.
A custom client suppresses default pool creation. A custom pool is reused by the default client.
Providers declare cleanup for custom clients and pools.

For multiple servers, register application Configuration Properties and named native client Beans.
Inject using `autowired(name="cacheRedisClient")` or pass `name="cacheRedisClient"` to helpers.
Default configuration targets standalone Redis. Configure Sentinel or Cluster explicitly through
native APIs, with matching Bean and injection types, instead of inferring topology from a URL.

## Public API and example

`pythonboot_redis` and `pythonboot_starter_redis` explicitly export `RedisClient`, `AsyncRedisClient`,
`RedisProperties`, `RedisUtil`, and `AsyncRedisUtil`. Import native locks, pools, and exceptions from
their redis-py modules. Repository `examples/redis/` demonstrates async client injection, static utilities,
List commands, and distributed locks through a Web application.
