# pythonboot-sqlalchemy

PythonBoot 的 SQLAlchemy 原生 ORM 实现包。分发名为 `pythonboot-sqlalchemy`，
导入名为 `pythonboot_sqlalchemy`；应用推荐安装聚合包 `pythonboot-starter-sqlalchemy`。

- 通过 Configuration Properties 绑定 `pythonboot.datasource` 和 `pythonboot.sqlalchemy`。
- 自动注册同步或异步 Engine 和原生 Session 工厂，应用 Bean 优先。
- `SessionFactory` 是 `sessionmaker` 的类别名，`AsyncSessionFactory` 是 `async_sessionmaker`
  的类别名，可直接作为 `autowired()` 注入类型，不增加代理或包装层。
- Session 由业务创建并关闭；业务显式 `commit()`，需要继续复用失败 Session 时显式 `rollback()`。
- 不提供 Mapper、自动提交、事务拦截器、自动建表或数据库迁移。
- 默认 Engine 关闭时调用 `dispose()`；异步关闭由容器等待。
- 数据库驱动由应用安装，URL 交由 SQLAlchemy 原生解析；未默认安装任何驱动。

不使用 `@transactional` 管理 Session，是为了让 `commit()` 的位置直接出现在业务流程中，
便于看清和管理事务边界、提交时机及异常处理。在 AI 辅助编写代码的工作流中，
明确要求生成 Session 作用域和提交逻辑可以降低遗漏提交的概率，显式调用也便于审阅。

```yaml
pythonboot:
  datasource:
    url: postgresql+asyncpg://user:password@localhost:5432/app
  sqlalchemy:
    mode: async
    session:
      expire_on_commit: false
      autoflush: true
```

```python
from pythonboot import autowired, service
from pythonboot_sqlalchemy import AsyncSessionFactory

@service
class UserService:
    session_factory: AsyncSessionFactory = autowired()

    async def rename(self, user_id: int, name: str) -> None:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")
            user.name = name
            await session.commit()
```

`User` 为应用自定义 SQLAlchemy ORM 模型。多 Service 共享事务时显式传递 Session。
连接池 Starter 可以提供自己的 Engine Bean（外部连接池适配通常配合 `NullPool`），
或注册更早装配的自动配置；本模块退让并继续使用原生 Session 工厂。
用户 Engine 的关闭责任由其 Bean 生命周期声明，外部池由创建方关闭。

完整配置、公共 API、同步用法和多数据源说明见
[`viteDocs/docs/zh/sqlalchemy.md`](../../viteDocs/docs/zh/sqlalchemy.md)，
可运行用法示例见 [`examples/sqlalchemy`](../../examples/sqlalchemy/README.md)。

## English

`pythonboot-sqlalchemy` is the implementation distribution; import `pythonboot_sqlalchemy`.
Install `pythonboot-starter-sqlalchemy` plus your chosen database driver in applications.
Configuration Properties bind connection and ORM settings. Native Engine and Session factory
Beans back off to application Beans. Callers explicitly create Sessions and commit changes;
Session context exit closes resources and rolls back uncommitted transactions.
There is no Mapper, implicit commit, transaction interceptor, schema creation, or migration.
Explicit commit points make transaction boundaries and failure handling visible and easier to manage.
In AI-assisted development, requiring Session scopes and commit logic reduces omissions and makes
the resulting transaction flow easier to review. This Starter does not use `@transactional` to manage Sessions.
Short factory names are aliases of native classes, compatible with concrete-class Bean injection.
The container disposes default engines, awaiting asynchronous disposal. Custom Engine and
external pool ownership must be declared by their providers.
See [English documentation](../../viteDocs/docs/en/sqlalchemy.md) and the
[example](../../examples/sqlalchemy/README.md).


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
