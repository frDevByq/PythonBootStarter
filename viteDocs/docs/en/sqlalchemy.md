# SQLAlchemy Starter

## Installation and responsibilities

```bash
uv add pythonboot-starter-sqlalchemy asyncpg
```

The dependency chain is `pythonboot-starter-sqlalchemy` → `pythonboot-sqlalchemy` →
`pythonboot` and `sqlalchemy[asyncio]`. The Starter aggregates dependencies and exports;
the implementation owns configuration, auto-configuration, and default Engine lifecycle.
Import `pythonboot_sqlalchemy` in application code.

Use native SQLAlchemy 2.x ORM directly. There is no Mapper, Session proxy, implicit transaction
interceptor, schema creation, or migration. Applications install their own database drivers.

| Database | Async driver | URL prefix |
| --- | --- | --- |
| PostgreSQL | asyncpg | `postgresql+asyncpg://` |
| MySQL / MariaDB | asyncmy | `mysql+asyncmy://` |
| SQLite | aiosqlite | `sqlite+aiosqlite:///` |

Other databases and synchronous drivers use supported SQLAlchemy dialect URLs.
Drivers must match the configured engine mode. Missing drivers, unknown dialects, and unsupported
options fail explicitly instead of selecting a different driver.

## Configuration Properties

```yaml
pythonboot:
  datasource:
    url: postgresql+asyncpg://user:password@localhost:5432/app
    echo: false
    hide_parameters: true
    connect_args: {}
    pool:
      kind: default
      size: 10
      max_overflow: 20
      timeout: 30
      recycle: 1800
      pre_ping: true
  sqlalchemy:
    enabled: true
    mode: async
    session:
      expire_on_commit: false
      autoflush: true
```

`DataSourceProperties` binds `pythonboot.datasource`; `SqlAlchemyProperties` binds
`pythonboot.sqlalchemy`. Both are injectable Configuration Properties Beans.

| Property under `pythonboot` | Default | Behavior |
| --- | --- | --- |
| `datasource.url` | Empty | Required for default engines; represented as `SecretStr` |
| `datasource.echo` | `false` | Native SQL logging |
| `datasource.hide_parameters` | `true` | Hide parameters in SQL logs and statement errors, not literal SQL text |
| `datasource.isolation_level` | Unset | Native engine isolation level; unsupported values fail |
| `datasource.connect_args` | `{}` | Driver connection arguments, including SSL, charset, and connect timeout |
| `datasource.pool.kind` | `default` | `default`, `queue`, `null`, or `static` |
| `datasource.pool.size` | Unset | Explicit `pool_size`, minimum 1 |
| `datasource.pool.max_overflow` | Unset | Minimum -1; -1 means unlimited overflow |
| `datasource.pool.timeout` | Unset | Pool acquisition timeout in seconds, minimum 0 |
| `datasource.pool.recycle` | Unset | Recycling seconds, minimum -1; -1 disables age recycling |
| `datasource.pool.pre_ping` | `true` | Test connections when checked out |
| `sqlalchemy.enabled` | `true` | Enable auto-configuration through YAML |
| `sqlalchemy.mode` | `async` | Choose `async` or `sync` through YAML |
| `sqlalchemy.session.expire_on_commit` | `false` | Keep loaded attributes after commit |
| `sqlalchemy.session.autoflush` | `true` | Allow native flush before queries and other ORM operations |

Auto-configuration conditions read YAML, so select `enabled` and `mode` in YAML rather than
environment variables. Other settings support environment overrides such as
`PYTHONBOOT_DATASOURCE_URL`, `PYTHONBOOT_DATASOURCE_POOL__SIZE`, and
`PYTHONBOOT_SQLALCHEMY_SESSION__AUTOFLUSH`.

Unset capacity settings preserve dialect-specific defaults. `queue` selects `QueuePool` for sync
engines or `AsyncAdaptedQueuePool` for async engines. `null` selects `NullPool`; `static` selects
`StaticPool`. Null and static pools reject size, max_overflow, and timeout options.
With `default`, explicitly supplied capacity settings must be supported by the dialect-selected
pool or SQLAlchemy raises an error. Usually omit capacity settings for SQLite, especially in-memory databases.

## Why this Starter does not use `@transactional`

Business code explicitly calls `commit()` and, when an explicit rollback is needed, `rollback()`.
The commit point is visible in the execution flow, making it easier to see which operations share
a transaction, when changes become durable, and how failures are handled. This makes transaction
control easier to review and manage. Business code defines the boundary instead of committing
automatically when an annotated method returns.

This choice also reflects widespread AI-assisted development. Explicit generation requirements
for Session scope and commit points let AI produce the commit logic alongside business operations,
reducing the chance of omission. Visible calls also let developers and AI reviewers directly assess
whether the transaction flow is complete. The Starter therefore favors visible, directly controlled
transaction boundaries.

The core framework still provides `@transactional`, but this Starter does not register a corresponding
transaction manager or use that annotation to manage native Sessions.

## Injection and explicit commits

`AsyncSessionFactory` is a direct class alias for `async_sessionmaker`; `SessionFactory` is an
alias for `sessionmaker`. Neither wraps the native factory nor uses a parameterized generic or
Python 3.12 `type` alias, allowing the core container to resolve concrete-class injection.

```python
from pythonboot import autowired, service
from pythonboot_sqlalchemy import AsyncSessionFactory
from sqlalchemy import select

@service
class UserService:
    session_factory: AsyncSessionFactory = autowired()

    async def list_users(self) -> list[User]:
        async with self.session_factory() as session:
            return list((await session.scalars(select(User))).all())

    async def rename(self, user_id: int, name: str) -> None:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")
            user.name = name
            await session.commit()
```

`User` is an application-defined ORM model. Returned entities detach when the Session closes.
Unloaded or expired attributes and lazy relationships cannot load outside that scope.
Eager-load required relationships and materialize API DTOs before closing the Session.

Native ORM identity mapping and dirty tracking remain active. Changes may autoflush before
another query, but flushing is not committing. Closing rolls back outstanding transactions and
returns connections to the pool. Previously successful commits are not undone by later failures.

After catching a flush or commit failure, explicitly roll back before reusing the same Session:

```python
from sqlalchemy.exc import IntegrityError

async with self.session_factory() as session:
    try:
        session.add(user)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        # The Session can now be used again.
```

If the exception leaves the scope, Session closure cleans up uncommitted work.
Factory `.begin()` scopes commit automatically on successful exit and are not used by these examples.
This module registers no core transaction manager; `@transactional` does not take ownership of these Sessions.
Pass a Session explicitly between Services when sharing a transaction; the caller owns commit and closure.
Sessions are not singleton Beans. Each concurrent task creates its own Session; never execute concurrently
through one AsyncSession.

## Synchronous mode

```yaml
pythonboot:
  datasource:
    url: sqlite:///./app.db
  sqlalchemy:
    mode: sync
```

SQLite's synchronous driver is included in Python. Install compatible drivers for other databases.

```python
from pythonboot import autowired, service
from pythonboot_sqlalchemy import SessionFactory

@service
class UserService:
    session_factory: SessionFactory = autowired()

    def rename(self, user_id: int, name: str) -> None:
        with self.session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User not found")
            user.name = name
            session.commit()
```

Do not directly run blocking synchronous database operations in asynchronous business methods.

## Beans, lifecycle, and pool integration

| Bean name | Type | Condition |
| --- | --- | --- |
| `dataSourceProperties` | `DataSourceProperties` | Module enabled |
| `sqlAlchemyProperties` | `SqlAlchemyProperties` | Module enabled |
| `sqlAlchemyEngine` | `sqlalchemy.Engine` | Sync mode; no matching type or name |
| `sqlAlchemySessionFactory` | `SessionFactory` | Sync mode; no matching type or name |
| `sqlAlchemyAsyncEngine` | `sqlalchemy.ext.asyncio.AsyncEngine` | Async mode; no matching type or name |
| `sqlAlchemyAsyncSessionFactory` | `AsyncSessionFactory` | Async mode; no matching type or name |

Entry-point name: `sqlalchemy`. Properties assemble at order 1900, engines at 2000, and factories
at 2100. Conditions inspect Bean definitions without instantiating resources. Default engine creation
does not connect; first use opens a connection. Application shutdown disposes owned default engines,
awaiting async disposal. Web applications use the existing ASGI lifespan to start and close the container.
The container does not track individual Sessions; callers must close them.

Application Engine Beans suppress default engines, and default factories use the supplied engines.
The URL may be omitted in that case. A custom factory suppresses the default factory, but engine
configuration remains independent. Exclude the corresponding engine auto-configuration or disable
this module if no default engine is wanted. Declare custom resource cleanup with Bean lifecycle metadata.

A future pool Starter can supply native Engine Beans through an earlier auto-configuration.
External pools must adapt to the dialect's driver protocol, typically using `NullPool` and a
connection-return adapter to avoid double pooling. Async dialects need async-compatible adapters,
not a synchronous creator. The provider owns external pool shutdown.

## Multiple data sources

The built-in properties describe one default source. Register application Configuration Properties
and named Engine/factory Beans for additional sources. There is no automatic routing or cross-database
atomic transaction. Use Bean names, qualifiers, or primary to resolve multiple candidates; ambiguity fails.

```python
from typing import Annotated
from pythonboot import autowired, bean, configuration
from pythonboot_sqlalchemy import AsyncSessionFactory
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

@configuration
class OrderDatabaseConfiguration:
    @bean(name="orderEngine", destroy_method="dispose")
    def order_engine(self, properties: OrderDatabaseProperties) -> AsyncEngine:
        return create_async_engine(properties.url.get_secret_value())

    @bean(name="orderSessionFactory")
    def order_sessions(
        self, engine: Annotated[AsyncEngine, autowired(name="orderEngine")],
    ) -> AsyncSessionFactory:
        return AsyncSessionFactory(engine, expire_on_commit=False)
```

`OrderDatabaseProperties` is an application-defined Configuration Properties class.
Inject with `session_factory: AsyncSessionFactory = autowired(name="orderSessionFactory")`.
Parameter names alone do not qualify dependencies. Usually disable default auto-configuration
and explicitly register each Engine/factory pair when using multiple sources.

## Public API and example

`pythonboot_sqlalchemy` and `pythonboot_starter_sqlalchemy` explicitly export `SessionFactory`,
`AsyncSessionFactory`, `DataSourceProperties`, `SqlAlchemyProperties`, `PoolProperties`, and
`SessionProperties`. Import Engine, Session, models, and expressions from SQLAlchemy itself.
Repository `examples/sqlalchemy/` includes async SQLite configuration, ORM models, Service attribute
injection, materialized query DTOs, and explicit commits. Applications prepare the schema themselves.
