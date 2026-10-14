# PythonBootStarters

基于 UV 管理的 PythonBoot Starter 多项目仓库。

- [全量示例工程](example/README.md)：全部 Starter、PostgreSQL／Redis、同步／异步功能与 HTTP 接口。

## 结构

- `starters/pythonboot-starter-web`：Web 应用启动依赖。
- `modules/pythonboot-web`：Web 功能实现，独立发布为 `pythonboot-web`。
- `starters/pythonboot-starter-sqlalchemy`：SQLAlchemy ORM 启动依赖。
- `modules/pythonboot-sqlalchemy`：原生 Engine、Session 工厂及配置属性集成。
- `examples/sqlalchemy`：SQLite 异步 ORM、工厂注入和显式提交示例。
- `starters/pythonboot-starter-redis`：Redis 启动依赖。
- `modules/pythonboot-redis`：redis-py 客户端、配置属性、静态工具与分布式锁。
- `examples/redis`：异步客户端注入、静态工具和分布式锁示例。

各 Starter 是独立的可发布 Python 包，并由根目录 UV workspace 统一管理。

`viteDocs/` 是全部 Starter 的统一中英文文档站；每个 Starter 的安装、配置、API 和示例
都在该站中维护。

依赖链：`pythonboot-starter-web` → `pythonboot-web` → `pythonboot`。
核心 `pythonboot` 保留在同级 `PythonBoot` 仓库；本地 UV sources 使用可编辑路径，
发布元数据仍使用包名和版本范围。每个实现包和 Starter 分别构建、发布到 PyPI。

应用安装 `pythonboot-starter-web`，核心接口从 `pythonboot` 导入，
Web 接口从 `pythonboot_web` 导入。本地工作区使用 `uv sync --all-packages` 同步。

## SQLAlchemy ORM

安装 `pythonboot-starter-sqlalchemy` 和所需数据库驱动，例如 `asyncpg`、`asyncmy` 或
`aiosqlite`；本模块不默认安装任何驱动。依赖链为 Starter → `pythonboot-sqlalchemy`
→ `pythonboot`、`sqlalchemy[asyncio]`。SQLAlchemy 根据 URL 原生选择方言和驱动。

通过 Configuration Properties 绑定 `pythonboot.datasource`、`pythonboot.sqlalchemy`，
默认异步模式。业务从 `pythonboot_sqlalchemy` 导入 `AsyncSessionFactory` / `SessionFactory`，
使用 `autowired()` 属性注入原生工厂，显式创建 Session 并调用 `commit()`。
关闭 Session 时清理未提交事务；需要在失败后继续使用同一 Session 时先 `rollback()`。
不提供 Mapper、隐式提交、事务拦截器或自动建表。

采用显式提交而非 `@transactional`，让提交位置与事务边界直接可见，更容易审阅和管理。
在 AI 辅助编写代码的工作流中，明确要求生成 Session 作用域与提交逻辑可以降低遗漏概率。

默认 Engine 由容器在关闭时 dispose；应用 Engine 和工厂优先，便于后续连接池 Starter 接入。
多数据源通过命名 Bean 显式声明，Session 不作为单例共享。
完整配置、API 和示例：[中文](viteDocs/docs/zh/sqlalchemy.md)、
[English](viteDocs/docs/en/sqlalchemy.md)、[示例](examples/sqlalchemy/README.md)。

SQLAlchemy integration installs native Engine and Session factory Beans through typed Configuration
Properties. Install a driver separately, scope Sessions explicitly, and commit in business code.
Custom Beans override defaults; the container disposes owned engines during shutdown.
Explicit commits keep transaction boundaries visible and manageable. Requiring Session scopes and
commit logic in AI-assisted code generation reduces omissions without relying on `@transactional`.

## Redis

安装 `pythonboot-starter-redis`，通过 Configuration Properties 绑定 `pythonboot.redis`。
依赖链为 Starter → `pythonboot-redis` → `pythonboot`、`redis`，无需额外数据库驱动。
默认同步模式，异步模式在 YAML 中选择 `mode: async`。

从 `pythonboot_redis` 导入 `RedisClient` / `AsyncRedisClient`，通过 `autowired()` 注入原生客户端。
`RedisUtil` / `AsyncRedisUtil` 提供 get/set、TTL、计数器、Hash、List、Set、有序集合及分布式锁。
`get_client()` 返回当前容器的原生客户端，不是 RedisTemplate，也不保存全局客户端。
独立任务通过 `ContextUtil.use(context)` 绑定容器，异步方法使用异步客户端和工具。

默认池与客户端由容器关闭，自定义 Bean 优先。锁使用 redis-py 原生令牌和原子释放／续期，
默认租期 30 秒、获取等待 5 秒，没有自动续期；操作结束后在 finally 中释放。
完整配置、API 和示例：[中文](viteDocs/docs/zh/redis.md)、
[English](viteDocs/docs/en/redis.md)、[示例](examples/redis/README.md)。

The Redis Starter configures native redis-py clients and lifecycle-managed pools, with sync and async
injection plus context-resolved static utilities. Native distributed locks support acquisition, release,
ownership checks, and explicit renewal. No global client is cached; independent tasks bind their container.


## 全量示例工程 / Complete example

`example/` 是独立的 `src` 布局 PythonBoot 应用，也是 UV workspace 成员；
安装三个 Starter 与应用自己的 `asyncpg`、`psycopg[binary]` PostgreSQL 驱动。
默认资源通过 entry point 自动配置，同步资源通过应用 Bean 声明，覆盖 ORM CRUD、
显式提交／回滚、Redis 全部工具和分布式锁，以及 Web 路由、异常、上下文、日期格式和文档。
配置、Service、Controller、模型与启动入口分层维护，详见 [示例说明](example/README.md)。

```bash
docker compose -f example/compose.yml up -d
uv sync --all-packages
uv run --package pythonboot-starter-example python -m starter_example.application
```

访问 `http://127.0.0.1:18000/docs`。已有同名容器使用 `docker start`；
用完执行 `docker stop pythonboot-starter-example-postgres pythonboot-starter-example-redis`，保留容器与数据。

The [complete example](example/README.md) is a workspace application with every Starter,
real PostgreSQL and Redis, both sync and async APIs, explicit transactions, all Redis utilities,
native locks, and the Web features. Run the commands above from the repository root.
Stop and retain the example containers after use. See the [English guide](viteDocs/docs/en/example.md).


示例同时展示应用自定义异步 Session 工厂使默认自动配置退让，以及原生 FastAPI middleware／lifespan 组合。
授权验证时，启动后运行 `uv run --package pythonboot-starter-example python example/http_smoke.py`。


## ORM 分页 / ORM pagination

`pythonboot_sqlalchemy` 和 `pythonboot_starter_sqlalchemy` 导出 `PageQuery`、`Page[T]`、
`paginate`（同步）与 `apaginate`（异步）。`PageQuery` 默认 `page=1`、`pageSize=10`，
`Page` 额外包含 `total` 与 `rows`。分页封装接收原生 Session 与单实体／单列 Select，
计算筛选总数并应用 OFFSET／LIMIT，支持 DTO mapper，Session 与事务仍由调用方管理。
完整示例增加 `/users/page` 和 `/sync/users/page`，原有列表接口保留。
详见 [中文分页文档](viteDocs/docs/zh/sqlalchemy.md#分页查询)。

The ORM packages export `PageQuery`, `Page[T]`, sync `paginate`, and async `apaginate`.
Pagination defaults to page 1 and size 10; results also contain total and rows.
Native Session ownership and transaction boundaries remain with callers.
See [English pagination documentation](viteDocs/docs/en/sqlalchemy.md#pagination).
