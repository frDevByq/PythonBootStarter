# 全量 Starter 示例

自定义同步／异步 Session 工厂已接入 `soft_delete` 配置，默认关闭。启用时，参与模型须继承
`SoftDeleteMixin` 并通过应用迁移添加配置字段；独立示例见 `../examples/sqlalchemy/soft_delete_example.py`。
Custom sync/async factories honor the opt-in soft-delete configuration, disabled by default.
Participating models declare the marker mixin and configured column through application migrations.

标准 `src` 布局的 PythonBoot 应用，安装所有 Starter：
`pythonboot-starter-web`、`pythonboot-starter-sqlalchemy`、`pythonboot-starter-redis`、
`pythonboot-starter-auth[web,redis]`。
启动接口从 `pythonboot_starter_web` 导入，路由等 Web API 从 `pythonboot_web` 导入；
ORM、Redis 公共接口从对应 Starter 导入，核心容器接口从 `pythonboot` 导入。

## 启动

在仓库根目录执行：

```bash
docker compose -f example/compose.yml up -d
uv sync --all-packages
uv run --package pythonboot-starter-example python -m starter_example.application
```

应用地址 `http://127.0.0.1:18000`，API 文档使用 Scalar（`/docs`），OpenAPI `/openapi.json`。
PostgreSQL 使用端口 `15432`、数据库 `pythonboot_example`、用户名／密码 `pythonboot`；
Redis 使用端口 `16379`。这些凭据仅用于本地演示。

已有同名容器时使用 `docker start pythonboot-starter-example-postgres pythonboot-starter-example-redis`，
不要重复执行创建命令。用完执行：

```bash
docker stop pythonboot-starter-example-postgres pythonboot-starter-example-redis
```

保留容器与数据，不使用 `--rm`、`docker rm` 或 `docker compose down`。

## 结构

- `src/starter_example/application.py`：继承 `PythonBootApplication` 的启动类，默认递归扫描本包。
- `config/`：YAML 与 local profile、配置属性、自定义资源、生命周期、AOP 和全局异常处理。
- `controller/`：类控制器、原生 FastAPI 路由、请求校验与统一响应。
- `service/`：`autowired()` 属性注入、原生 ORM 与 Redis 业务演示。
- `domain/`：ORM 模型、请求／响应 DTO、`BaseResult[T]`。

## 功能与接口

| 功能 | HTTP 接口 |
| --- | --- |
| 异步 Redis 登录、账号/Token Session、权限与角色 | `POST /auth/login`、`GET/PUT /auth/me`、`GET /auth/device`、`GET /auth/either` |
| 多端会话、注销与管理员踢人 | `GET /auth/sessions`、`POST /auth/logout`、`POST /auth/kickout/{login_id}` |
| 同步内存登录与鉴权 | `POST /sync/auth/login`、`GET /sync/auth/me`、`POST /sync/auth/logout` |
| 全部 Starter 与生命周期状态 | `GET /web/health` |
| 异步 ORM 增删改查、筛选 | `GET/POST /users`、`GET/PUT/PATCH/DELETE /users/{id}` |
| 同步 ORM 增删改查、筛选 | `GET/POST /sync/users`、`GET/PUT/PATCH/DELETE /sync/users/{id}` |
| 显式 rollback | `POST /users/rollback`、`POST /sync/users/rollback` |
| 异步 Redis 全部工具与原生锁 | `POST /redis/demo` |
| 同步 Redis 全部工具与原生锁 | `POST /redis/sync/demo` |
| 请求头、查询、路径、缓存请求体、请求数据、响应状态／头／Cookie | `POST /web/echo/{id}?source=http` |
| 日期查询格式与请求体字段格式 | `GET /web/datetime?at=2026/10/14`、`POST /web/schedule` |
| 重定向、自定义 HTTP 方法 | `GET /web/redirect`、`OPTIONS /web/methods` |
| 独立任务显式绑定当前容器 | `GET /web/task` |
| 原生 APIRouter 和 `Depends(inject(...))` | `GET /native/info` |
| 业务异常、404、422 统一响应 | 不存在的用户／路径、非法请求参数 |
| 同步／异步业务切面 | CRUD 和 Redis Service 的 `@logged` |
| API 文档与日期响应格式 | `/docs`、`/openapi.json` |

Redis 两个演示接口执行 `get_client`、get/set、delete/exists/expire/ttl、incr/decr、
Hash、List、Set、有序集合的所有工具方法，以及锁获取、归属判断、显式续期和释放。
每次使用独立 UUID 键空间，演示后清理自己的数据，不修改其他业务键。

默认异步 Engine、Redis 池和客户端通过已安装的 entry point 自动配置；
应用自定义异步 Session 工厂使对应默认自动配置退让。原生 FastAPI middleware 和 lifespan 与框架能力组合，
`/web/health` 返回 lifespan 状态，响应头 `X-Application` 演示应用 middleware。
应用额外声明同步 Engine、Session 工厂、Redis 池和客户端，演示命名／限定符注入与
自定义资源的关闭责任。同步接口由 FastAPI 在线程池中执行，异步接口使用异步驱动。
业务为每次操作创建 Session，显式 commit／rollback；不会共享 Session 或自动绑定事务。
两个 ORM 路径使用同一张 PostgreSQL 表，便于观察提交结果。

`DemoSchema` 在 `@postconstruct` 中显式建演示表，不在导入时连接数据库；
这是应用自己的初始化逻辑，Starter 不自动建表，生产应用应使用迁移。
容器退出时关闭客户端与连接池并 dispose Engine；异步清理由框架 await。
锁每次创建独立对象，租期 30 秒、等待 5 秒，在 finally 中释放，无自动续期。

YAML 配置见 `src/starter_example/config/application.yml`，`application-local.yml` 演示 profile 覆盖。
连接属性可用 `PYTHONBOOT_DATASOURCE_URL`、`EXAMPLE_SYNC_DATABASE_URL`、`PYTHONBOOT_REDIS_URL` 覆盖。
`enabled` 和 `mode` 在 YAML 中选择；本应用同时演示默认异步资源和自定义同步资源，
关闭或切换默认资源时需对应调整注入和控制器，不提供缺失依赖的静默降级。

## HTTP 示例

```bash
curl -X POST http://127.0.0.1:18000/users -H 'Content-Type: application/json' -d '{"name":"Alice"}'
curl http://127.0.0.1:18000/sync/users
curl -X POST http://127.0.0.1:18000/redis/demo
curl -X POST http://127.0.0.1:18000/redis/sync/demo
curl -i -X POST 'http://127.0.0.1:18000/web/echo/1?source=http' -H 'Content-Type: application/json' -H 'X-Trace-Id: demo' -d '{"message":"hello"}'
curl -X POST http://127.0.0.1:18000/web/schedule -H 'Content-Type: application/json' -d '{"at":"2026/10/14 09:30"}'
```

成功业务响应为 `{"code":200,"message":"操作成功","result":...}`；失败业务码为 500，
HTTP 状态仍保留 404／422／409 等语义，创建用户 HTTP 状态为 201，上下文回显为 202。

## English

This standard src-layout application includes every Starter and demonstrates both sync and async
PostgreSQL ORM CRUD with explicit commits and rollbacks, all Redis utility methods and native locks,
Web routes, validation, exception advice, request/response context, date formatting, OpenAPI,
configuration profiles, dependency bridging, lifecycle hooks, and sync/async AOP.
Run the three commands above from the workspace root. Use the local example credentials only for
local development. Restart existing containers with `docker start`; stop them after use and retain
them and their data. The application explicitly creates its demo schema at lifecycle startup;
production applications should manage schema migrations. Default async engines and Redis resources are auto-configured; an application-defined async Session factory
overrides its matching default, and custom sync providers declare their cleanup ownership. Each operation owns its Session, each Redis
demo owns a UUID key namespace, and each lock has a bounded lease and is released in finally.
See the [English example guide](../viteDocs/docs/en/example.md).


已授权验证时，启动应用后执行 `uv run --package pythonboot-starter-example python example/http_smoke.py`，
覆盖全部 26 个业务 HTTP 操作以及并发 ORM、Redis、请求上下文隔离。


本次启动与 HTTP 测试结果见 [验证记录](HTTP_TEST_RESULTS.md)。
See the [HTTP verification record](HTTP_TEST_RESULTS.md).


## ORM 分页

`GET /users/page`、`GET /sync/users/page` 使用 `PageQuery` 与 `apaginate`／`paginate`，
默认 `page=1`、`pageSize=10`，支持 name 筛选，返回 `BaseResult[Page[UserView]]`。
Page 包含 total、page、pageSize、rows；原有非分页列表接口保留。

Sync and async pagination endpoints return total, page, pageSize, and rows; defaults are page 1
and size 10. Optional name filtering is applied before counting and paging.

`RedisUtil` / `AsyncRedisUtil` 的 set/get 默认 JSON 序列化对象（Pydantic、dataclass、普通对象），
读取可用 `get(key, target_type=User)` 还原类型。`pythonboot.redis.serializer` 可配置 `json`、
`raw` 或继承 `RedisSerializer` 的自定义类完整路径；应用序列化器 Bean 优先。
仅工具 set/get 使用此配置，原生客户端和其他命令保持原生行为；切换格式需迁移旧值或使用新键。

Utility set/get serialize objects as JSON by default, including Pydantic models, dataclasses, and ordinary objects.
Use `get(key, target_type=User)` to reconstruct a type. Configure `pythonboot.redis.serializer` as
`json`, `raw`, or a fully qualified `RedisSerializer` subclass; application serializer Beans override defaults.
Native clients and other commands retain native behavior. Migrate existing values or use new keys when switching formats.

## 鉴权 / Authentication

未登录访问需要权限或角色的接口时抛出 NotLoginError，消息仅为“Not logged in”，由应用异常处理映射为 401。
Permission and role checks reject unauthenticated callers with NotLoginError (`Not logged in`), mapped to HTTP 401 by application advice.

应用 configure 显式安装 AuthInterceptor，保护 `/auth/*` 与 `/sync/auth/*`，
放行 `/auth/login` 与 `/sync/auth/login`；其他原有接口保持原有访问行为。
默认异步 AuthService 使用 Redis，命名同步 Bean 使用进程内存，两个后端的 Token 不能互用。
应用按请求路径选择拦截器服务，同步和异步装饰器分别使用匹配的容器 Bean。

仅本地演示账号为 `admin / admin-demo`、`reader / reader-demo`。应用验证密码后才调用 login，
账号 Session 直接保存不含密码的 SessionUser 对象，通过 `get("user", target_type=SessionUser)`
自动还原，修改昵称后重新 set；Token Session 保存 device。admin 有 `example:*`、
`admin:session:*` 与 admin 角色，reader 只有 `example:read`；修改昵称和踢人需要相应权限。
权限每次通过应用 StpInterface 动态获取；默认 JSON 序列化可通过自定义 Bean 替换。

```bash
curl -X POST http://127.0.0.1:18000/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin-demo","device":"browser"}'
curl http://127.0.0.1:18000/auth/me -H 'Authorization: Bearer <token>'
curl http://127.0.0.1:18000/auth/sessions -H 'Authorization: Bearer <token>'
```

使用另一个 device 登录演示共享账号数据和独立 Token 数据；重复同设备登录替换旧会话，
超过 5 个活跃登录踢掉最早登录。登录响应的 csrf_token 用于可选 Cookie 写操作，当前示例默认使用 Header。
ErrorAdvice 是应用自己的异常处理，将未登录映射为 401、角色/权限/CSRF 失败映射为 403、
存储故障映射为 503，业务失败码仍为 500；Starter 本身仅抛异常。

The application explicitly registers its interceptor and excludes both login endpoints. Async routes use
Redis; sync routes use a named memory service, with separate tokens. Local demonstration accounts are
admin/admin-demo and reader/reader-demo. Credential verification and dynamic roles/permissions belong to
the application. Account sessions store SessionUser models directly and restore them with target_type=SessionUser;
token sessions hold device data. Wildcard grants, OR checks,
role checks, concurrent-device sessions, replacement, logout and kickout are demonstrated. Exception advice
is application-owned; the framework only raises typed errors. See [the Auth guide](../viteDocs/docs/en/auth.md).


当前 FastAPI 应用自动注册为名为 `fastapiApp` 的单例 Bean，可通过 `app: FastAPI = autowired()` 注入，
或在容器启动后通过 `ContextUtil.get_bean(FastAPI)` 获取。每个应用使用独立实例；
`configure()` 执行时容器尚未启动，请直接使用传入的 `app`。禁用自动配置时此 Bean 仍会注册。


The current FastAPI application is registered as the singleton Bean `fastapiApp`.
Inject it with `app: FastAPI = autowired()` or obtain it with `ContextUtil.get_bean(FastAPI)` after container startup.
Each application has its own instance. The container has not started during `configure()`; use its `app` argument there.
The Bean is also registered when `auto_configure=False`.

## 跳过鉴权校验 / Bypass authentication checks

application.yml 默认设置 `pythonboot.auth.check_enabled: true`。
改为 `false` 或设置 `PYTHONBOOT_AUTH_CHECK_ENABLED=false`，同步内存与异步 Redis 服务的
登录／权限／角色校验及装饰器、Web 拦截器直接放行，无需 Token 或权限提供者。
`check_login()` 此时返回 None；获取当前用户、Session 或注销仍要求真实 Token。
拦截器自动 Cookie CSRF 校验也会跳过，显式 CSRF 校验保持原行为。
应用凭据验证仍保留，`enabled` 仍控制模块装配。

Set `pythonboot.auth.check_enabled: false` in application.yml, or use
`PYTHONBOOT_AUTH_CHECK_ENABLED=false`, to bypass login, permission and role checks for both services,
including decorators and the Web interceptor. check_login returns None; identity/session access and logout
still require valid tokens. Automatic interceptor CSRF checks are skipped; explicit CSRF checks and
application credential verification remain active. Keep enabled true to retain service auto-configuration.

关闭鉴权校验时，服务创建会以 ERROR 级别输出醒目的安全警告及恢复配置提示。
Disabling authentication checks emits a prominent ERROR-level security warning when the service is created, including instructions to restore checks.
