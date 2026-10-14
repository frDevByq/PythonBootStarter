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
