# 全量 Starter 示例

标准 `src` 布局的 PythonBoot 应用，安装所有 Starter：
`pythonboot-starter-web`、`pythonboot-starter-sqlalchemy`、`pythonboot-starter-redis`。
启动接口从 `pythonboot_starter_web` 导入，路由等 Web API 从 `pythonboot_web` 导入；
ORM、Redis 公共接口从对应 Starter 导入，核心容器接口从 `pythonboot` 导入。

## 启动

在仓库根目录执行：

```bash
docker compose -f example/compose.yml up -d
uv sync --all-packages
uv run --package pythonboot-starter-example python -m starter_example.application
```

应用地址 `http://127.0.0.1:18000`，API 文档 `/docs`，OpenAPI `/openapi.json`。
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
