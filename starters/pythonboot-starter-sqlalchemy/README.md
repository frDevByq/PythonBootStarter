# pythonboot-starter-sqlalchemy

SQLAlchemy ORM 的启动依赖聚合包，依赖 `pythonboot-sqlalchemy`，传递引入核心
`pythonboot` 和 `sqlalchemy[asyncio]`。实际 ORM 集成和自动配置由实现包承担。

```bash
uv add pythonboot-starter-sqlalchemy asyncpg
```

驱动由应用选择，也可使用 `asyncmy`、`aiosqlite` 或兼容的同步驱动。
配置 URL 后，SQLAlchemy 原生解析数据库和驱动。
默认异步模式；同步模式在 YAML 中设置 `pythonboot.sqlalchemy.mode: sync`。
未设置 URL 且未提供自定义 Engine 时，启动明确报错。

业务从 `pythonboot_sqlalchemy` 导入 `AsyncSessionFactory` / `SessionFactory`，
通过 `autowired()` 注入；本包也显式重导出工厂和配置类型。
Session 在业务方法中创建，显式提交，无自动事务边界。

不使用 `@transactional` 隐式管理 Session：显式 `commit()` 让提交位置和事务边界更容易
被看见、审阅和管理。AI 辅助编写代码时，可明确要求生成提交逻辑以降低遗漏概率。

完整配置与用法：[中文文档](../../viteDocs/docs/zh/sqlalchemy.md)、
[English documentation](../../viteDocs/docs/en/sqlalchemy.md)、
[示例 / Example](../../examples/sqlalchemy/README.md)。

## English

Install distribution `pythonboot-starter-sqlalchemy` and a compatible driver.
The Starter aggregates `pythonboot-sqlalchemy`; its import package is `pythonboot_starter_sqlalchemy`.
Prefer importing ORM integration types from `pythonboot_sqlalchemy` and core decorators
from `pythonboot`. Async mode is the default; choose sync mode through application YAML.
Inject a native Session factory, scope Sessions explicitly, and call `commit()` yourself.
Explicit commits make transaction boundaries visible and easier to manage, without `@transactional`.
Requiring commit logic in AI-assisted code generation reduces the chance of omission.


完整分层应用见 [全量 Starter 示例](../../example/README.md)，包含全部 Starter、PostgreSQL／Redis 和同步／异步 HTTP 用法。
See the [complete Starter application](../../example/README.md) for all Starters and sync/async HTTP examples.


## 分页查询

`PageQuery` 包含 `page`（默认 1）和 `pageSize`（默认 10），二者必须大于等于 1。
`Page[T]` 包含相同分页参数，以及 `total`（默认 0）和 `rows: list[T]`（默认空列表）。
Python 属性与 JSON 字段均使用 `pageSize`，不需要别名转换。

从 `pythonboot_sqlalchemy` 或 `pythonboot_starter_sqlalchemy` 导入这两个模型，以及
同步 `paginate`、异步 `apaginate`。实现位于实现模块，Starter 只导出公共入口，无新增依赖。

```python
from sqlalchemy import select
from pythonboot_starter_sqlalchemy import Page, PageQuery, paginate, apaginate

query = PageQuery(page=1, pageSize=10)
statement = select(User).where(User.name == "Alice").order_by(User.id)

with session_factory() as session:
    page = paginate(session, statement, query, mapper=UserView.model_validate)

async with async_session_factory() as session:
    page = await apaginate(session, statement, query, mapper=UserView.model_validate)
```

省略 `query` 时使用默认分页；`mapper` 可选，用于在 Session 内将实体转换成 DTO。
省略 `mapper` 则 `rows` 保留原生实体或标量；调用方应在关闭 Session 前加载所需属性。

封装对传入 Select 生成 COUNT 子查询和 OFFSET／LIMIT 查询，保留过滤、JOIN、DISTINCT、
GROUP BY 与 HAVING；总数查询移除排序，数据查询保留原排序。原有 LIMIT／OFFSET／FETCH
由分页参数替换，原 Select 不被修改。无匹配结果或页码超出范围时返回空 `rows`，
`total` 始终表示完整筛选结果总数，不自动调整页码。请使用包含唯一字段的排序保证分页稳定。

支持只选择一个 ORM 实体或一个标量列的 Select；多列／多实体查询明确报错。
总数按 SQL 查询结果行统计，JOIN 重复行不自动去重；需要去重时显式使用 DISTINCT。
需要 `.unique()` 的集合 joined eager loading 不在此封装范围内，可使用 `selectinload`。
COUNT 与数据查询是两次顺序执行的 SQL，在并发写入时一致性取决于调用方事务隔离级别。
封装不创建、关闭、提交或回滚 Session，不修改事务边界，异步操作不得并发共享同一 Session。

全量示例提供 `GET /users/page` 和 `GET /sync/users/page`，支持 `page`、`pageSize`、`name` 参数，
返回 `BaseResult[Page[UserView]]`；原有列表接口保持不变。


## Pagination

`PageQuery` has `page` (default 1) and `pageSize` (default 10), both at least 1.
`Page[T]` adds `total` (default 0) and `rows: list[T]` (an independent empty list by default).
Python attributes and JSON use the exact field name `pageSize`.

Import both models and the sync `paginate` / async `apaginate` helpers from
`pythonboot_sqlalchemy` or `pythonboot_starter_sqlalchemy`. Implementation belongs to the module;
the Starter only re-exports public interfaces. No dependency is added.

```python
from sqlalchemy import select
from pythonboot_starter_sqlalchemy import Page, PageQuery, paginate, apaginate

query = PageQuery(page=1, pageSize=10)
statement = select(User).where(User.name == "Alice").order_by(User.id)

with session_factory() as session:
    page = paginate(session, statement, query, mapper=UserView.model_validate)

async with async_session_factory() as session:
    page = await apaginate(session, statement, query, mapper=UserView.model_validate)
```

Omit `query` to use defaults. The optional `mapper` materializes DTOs within the Session;
otherwise rows retain native entities or scalar values. Load required attributes before closing.

A COUNT subquery measures the full selection, and an OFFSET/LIMIT query loads the page.
Filters, joins, DISTINCT, GROUP BY, and HAVING are preserved. Count removes ordering; rows retain it.
Existing LIMIT/OFFSET/FETCH clauses are replaced by pagination. The original Select is not mutated.
Empty and out-of-range pages keep the full matching `total`, return empty `rows`, and retain the
requested page number. Order by a unique key for stable paging.

Select exactly one ORM entity or scalar column; multi-column/entity statements raise an error.
Totals count SQL result rows, including duplicate join rows; use explicit DISTINCT when needed.
Collection joined eager loading requiring `.unique()` is outside this helper's scope; use `selectinload`.
Count and rows execute sequentially as two queries; concurrent-write consistency depends on the
caller's transaction isolation. Helpers do not create, close, commit, or roll back Sessions.
Never share an AsyncSession between concurrent tasks.

The complete application exposes `GET /users/page` and `GET /sync/users/page`, accepting
`page`, `pageSize`, and optional `name`, and returning `BaseResult[Page[UserView]]`.
Existing list endpoints remain available.
