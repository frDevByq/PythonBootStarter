# 全量 Starter 示例工程

仓库的 `example/` 是标准 `src` 布局 PythonBoot 应用，包含全部 Starter、PostgreSQL、Redis
以及同步／异步 HTTP 接口。入口为 `src/starter_example/application.py`，启动类继承
`PythonBootApplication`，配置、Controller、Service、domain 分层管理。

## 安装与启动

在仓库根目录执行：

```bash
docker compose -f example/compose.yml up -d
uv sync --all-packages
uv run --package pythonboot-starter-example python -m starter_example.application
```

接口地址 `http://127.0.0.1:18000`，文档 `/docs`，规范 `/openapi.json`。
数据库端口 15432，数据库 `pythonboot_example`，用户名／密码 `pythonboot`；Redis 端口 16379。
以上账号仅用于本地示例。已有容器用 `docker start`，用完只执行
`docker stop pythonboot-starter-example-postgres pythonboot-starter-example-redis`，保留容器与数据。

依赖三个分发包 `pythonboot-starter-web`、`pythonboot-starter-sqlalchemy`、`pythonboot-starter-redis`，
分别聚合实现模块 `pythonboot-web`、`pythonboot-sqlalchemy`、`pythonboot-redis` 和核心 `pythonboot`。
启动入口导入 `pythonboot_starter_web`，路由与上下文导入 `pythonboot_web`，
ORM／Redis 导入对应 `pythonboot_starter_*` 的公开导出，核心接口导入 `pythonboot`。
应用自行声明 PostgreSQL 驱动 `asyncpg`、`psycopg[binary]`。

## 功能清单

| 示例 | 接口 |
| --- | --- |
| 生命周期与 Starter 状态 | `GET /web/health` |
| 异步 ORM CRUD／筛选 | `/users`、`/users/{id}` |
| 同步 ORM CRUD／筛选 | `/sync/users`、`/sync/users/{id}` |
| 显式回滚 | `POST /users/rollback`、`POST /sync/users/rollback` |
| Redis 同步／异步全部工具、锁归属、续期与释放 | `POST /redis/demo`、`POST /redis/sync/demo` |
| 请求头／查询／路径／请求体／请求数据、响应状态／头／Cookie | `POST /web/echo/{id}` |
| 参数与字段日期格式 | `GET /web/datetime`、`POST /web/schedule` |
| 重定向／自定义方法 | `GET /web/redirect`、`OPTIONS /web/methods` |
| 独立任务显式绑定容器 | `GET /web/task` |
| 原生 APIRouter／依赖桥接 | `GET /native/info` |
| 异常与校验 | 不存在的用户或路径、非法请求（404／422） |
| AOP／属性注入／配置属性／profile | CRUD 和 Redis Service、config 目录 |

ORM 提供 GET／POST／PUT／PATCH／DELETE；所有业务接口声明 `BaseResult[T]`。
Redis 覆盖所有公开工具方法：get_client、字符串、TTL、计数器、Hash、List、Set、有序集合及原生锁。
每次使用独立 UUID 键空间，结束清理自己的键。

默认异步资源通过 entry point 自动配置，同步资源由应用 Bean 声明关闭责任，
展示名称与限定符注入。业务推荐 `autowired()` 属性注入；每次操作创建独立 Session，
显式 commit／rollback，同步路由在线程池执行，异步路由使用异步驱动。
演示表由应用生命周期回调显式创建，Starter 不自动建表；生产应用应使用迁移。
默认 Engine、Redis 客户端和连接池由容器关闭，异步清理由框架 await。
锁租期 30 秒、等待 5 秒，成功后在 finally 中释放，显式续期，没有自动续期。

配置文件为 `application.yml` 与 `application-local.yml`；连接地址可分别通过
`PYTHONBOOT_DATASOURCE_URL`、`EXAMPLE_SYNC_DATABASE_URL`、`PYTHONBOOT_REDIS_URL` 覆盖。
默认异步资源的 enabled／mode 在 YAML 中选择，切换时同步调整依赖它们的示例服务，不静默降级。


示例同时展示应用自定义异步 Session 工厂使默认自动配置退让，以及原生 FastAPI middleware／lifespan 组合。
授权验证时，启动后运行 `uv run --package pythonboot-starter-example python example/http_smoke.py`。


同步与异步分页：`GET /sync/users/page?page=1&pageSize=10`、`GET /users/page?page=1&pageSize=10`，
可附加 `name` 筛选，返回 `BaseResult[Page[UserView]]`，内含 total、page、pageSize、rows。
