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
