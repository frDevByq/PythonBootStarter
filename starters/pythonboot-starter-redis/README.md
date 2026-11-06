# pythonboot-starter-redis

Redis 启动依赖聚合包：`pythonboot-starter-redis` → `pythonboot-redis` → `pythonboot`、`redis`。
实际客户端、配置和工具实现位于 `pythonboot-redis`。

```bash
uv add pythonboot-starter-redis
```

通过 `pythonboot.redis` 配置 URL、同步／异步模式及连接池参数。
Redis 类型从 `pythonboot_redis` 导入：
`RedisClient`、`AsyncRedisClient`、`RedisProperties`、`RedisUtil`、`AsyncRedisUtil`。
本包的导入名为 `pythonboot_starter_redis`，也显式重导出这些公共类型。

业务通过 `redis_client: RedisClient = autowired()` 注入原生客户端；
静态工具类提供 get/set、List 等常用命令及 redis-py 分布式锁。
工具类不保存全局客户端，独立任务须绑定当前容器。

[中文文档](../../viteDocs/docs/zh/redis.md) · [English documentation](../../viteDocs/docs/en/redis.md)
· [示例 / Example](../../examples/redis/README.md)

## English

Install distribution `pythonboot-starter-redis`; its import package is `pythonboot_starter_redis`.
Prefer importing public integration types from `pythonboot_redis` and decorators from `pythonboot`.
The Starter aggregates dependencies without implementing Redis commands.
Configure native clients through `pythonboot.redis`, inject clients with `autowired()`, or use
context-resolved static utilities. Both synchronous and asynchronous clients and native locks are supported.


完整分层应用见 [全量 Starter 示例](../../example/README.md)，包含全部 Starter、PostgreSQL／Redis 和同步／异步 HTTP 用法。
See the [complete Starter application](../../example/README.md) for all Starters and sync/async HTTP examples.

`RedisUtil` / `AsyncRedisUtil` 的 set/get 默认 JSON 序列化对象（Pydantic、dataclass、普通对象），
读取可用 `get(key, target_type=User)` 还原类型。`pythonboot.redis.serializer` 可配置 `json`、
`raw` 或继承 `RedisSerializer` 的自定义类完整路径；应用序列化器 Bean 优先。
仅工具 set/get 使用此配置，原生客户端和其他命令保持原生行为；切换格式需迁移旧值或使用新键。

Utility set/get serialize objects as JSON by default, including Pydantic models, dataclasses, and ordinary objects.
Use `get(key, target_type=User)` to reconstruct a type. Configure `pythonboot.redis.serializer` as
`json`, `raw`, or a fully qualified `RedisSerializer` subclass; application serializer Beans override defaults.
Native clients and other commands retain native behavior. Migrate existing values or use new keys when switching formats.
