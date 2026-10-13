# SQLAlchemy Starter

## 安装与职责

```bash
uv add pythonboot-starter-sqlalchemy asyncpg
```

依赖链为 `pythonboot-starter-sqlalchemy` → `pythonboot-sqlalchemy` → `pythonboot`、
`sqlalchemy[asyncio]`。Starter 只聚合依赖和导出入口；实现包提供配置、自动装配与
Engine 生命周期。安装分发包使用连字符，业务导入 `pythonboot_sqlalchemy`。

本模块直接使用 SQLAlchemy 2.x ORM，没有 Mapper、Session 代理或隐式事务装饰器。
数据库驱动由应用另行安装，不默认安装驱动、不自动建表、不执行迁移。

| 数据库 | 异步驱动 | URL 前缀 |
| --- | --- | --- |
| PostgreSQL | asyncpg | `postgresql+asyncpg://` |
| MySQL / MariaDB | asyncmy | `mysql+asyncmy://` |
| SQLite | aiosqlite | `sqlite+aiosqlite:///` |

其他数据库和同步驱动使用 SQLAlchemy 支持的方言 URL。驱动必须与同步／异步模式匹配，
缺少驱动、未知方言或不支持的配置直接报错，不回退到其他驱动。

## 配置属性

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

`DataSourceProperties` 使用 `@configuration_properties("pythonboot.datasource")`；
`SqlAlchemyProperties` 使用 `@configuration_properties("pythonboot.sqlalchemy")`，
二者都注册为可注入的配置 Bean。

| 配置 | 默认值 | 行为 |
| --- | --- | --- |
| `datasource.url` | 空 | 默认 Engine 必填；配置 Bean 使用 `SecretStr` 隐藏展示 |
| `datasource.echo` | `false` | SQLAlchemy SQL 日志开关 |
| `datasource.hide_parameters` | `true` | 隐藏 SQL 日志和语句异常中的参数；不隐藏原始 SQL 文本中的字面值 |
| `datasource.isolation_level` | 未设置 | 原生 Engine 隔离级别，数据库不支持时报错 |
| `datasource.connect_args` | `{}` | 传递给驱动的连接参数，如 SSL、字符集和连接超时 |
| `datasource.pool.kind` | `default` | `default`、`queue`、`null`、`static` |
| `datasource.pool.size` | 未设置 | 显式传递 `pool_size`，至少 1 |
| `datasource.pool.max_overflow` | 未设置 | 至少 -1，-1 表示无限溢出连接 |
| `datasource.pool.timeout` | 未设置 | 获取池连接等待秒数，至少 0 |
| `datasource.pool.recycle` | 未设置 | 连接回收秒数，至少 -1，-1 表示不按时间回收 |
| `datasource.pool.pre_ping` | `true` | 借出连接时探活 |
| `sqlalchemy.enabled` | `true` | 是否装配本模块，在 YAML 中选择 |
| `sqlalchemy.mode` | `async` | `async` 或 `sync`，在 YAML 中选择 |
| `sqlalchemy.session.expire_on_commit` | `false` | 提交后不自动过期已加载属性 |
| `sqlalchemy.session.autoflush` | `true` | 查询等操作前允许 SQLAlchemy 自动 flush |

上表中的键均位于 `pythonboot` 下。自动配置条件读取 YAML；`enabled` 和 `mode`
必须在 YAML 中选择，不能用环境变量切换自动配置模式。
其他属性支持环境变量覆盖，如 `PYTHONBOOT_DATASOURCE_URL`、
`PYTHONBOOT_DATASOURCE_POOL__SIZE` 和 `PYTHONBOOT_SQLALCHEMY_SESSION__AUTOFLUSH`。

未设置池容量参数时保留方言默认值，不向所有数据库强行套用同一套配置。
`queue` 在异步模式使用 `AsyncAdaptedQueuePool`，同步模式使用 `QueuePool`；
`null` 为 `NullPool`，`static` 为 `StaticPool`。后两者不接受 size、max_overflow、timeout。
`default` 的容量参数也必须适用于方言选择的池，否则由 SQLAlchemy 明确报错。
SQLite 通常省略容量配置，内存数据库按其方言默认池处理。

## 为什么不使用 `@transactional`

本 Starter 选择在业务代码中显式调用 `commit()`，需要主动回滚时调用 `rollback()`。
提交位置直接出现在执行流程里，阅读代码就能看到哪些操作属于同一个事务、
何时持久化，以及异常后如何处理，更容易审阅和管理事务。
事务边界由业务明确决定，不跟随被注解方法的返回自动提交。

这一选择也考虑了当前广泛使用 AI 辅助编写代码的工作方式：在生成要求中明确
Session 作用域和提交位置，AI 可以一并生成提交逻辑，降低遗漏提交的概率；
显式的调用也便于开发者和 AI 在审阅时直接确认事务是否完整。
因此，本 Starter 优先采用可见、可直接控制的事务流程。

核心框架仍提供 `@transactional`，但本 Starter 不注册对应事务管理器，
不通过该注解管理原生 Session。

## 注入与显式提交

`AsyncSessionFactory` 直接指向原生 `async_sessionmaker` 类，`SessionFactory` 直接指向
`sessionmaker` 类。它们没有包装层，也不是参数化泛型或 Python 3.12 `type` 别名，
因此兼容核心要求具体类的 Bean 类型解析。

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

`User` 是应用自己的 ORM 模型。查询返回的实体在 Session 关闭后脱离管理；
未加载或过期的属性、延迟加载关系不能在作用域外继续加载。
需要的关系在作用域内显式预加载，Web 返回值建议在关闭前转成 DTO。

原生 ORM 使用身份映射和脏检查；受管理对象属性修改可能在下一次查询前自动 flush，
但 flush 不等于 commit。Session 关闭时回滚尚未提交的事务并归还连接，
已经成功 commit 的修改不会因后续异常撤销。

如果捕获 flush／commit 异常后还要继续使用同一 Session，先显式 `rollback()`：

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

如果异常直接离开作用域，可让关闭过程清理未提交事务。不要使用工厂的 `.begin()`
来实现本项目示例的事务边界，因为它会在成功退出时自动提交。
本模块不注册核心事务管理器，`@transactional` 不会自动接管这里创建的 Session。

多个 Service 共用事务时显式传入同一 Session，由调用方提交和关闭。
Session 不是单例 Bean；并发任务各自创建 Session，禁止共享一个 AsyncSession 并发执行。

## 同步模式

```yaml
pythonboot:
  datasource:
    url: sqlite:///./app.db
  sqlalchemy:
    mode: sync
```

SQLite 同步驱动来自 Python 标准库；其他数据库需安装兼容同步驱动。

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

异步业务中不要直接执行阻塞的同步数据库操作。

## Bean 与扩展点

| Bean 名称 | 类型 | 装配条件 |
| --- | --- | --- |
| `dataSourceProperties` | `DataSourceProperties` | 模块启用 |
| `sqlAlchemyProperties` | `SqlAlchemyProperties` | 模块启用 |
| `sqlAlchemyEngine` | `sqlalchemy.Engine` | 同步模式且没有相同类型或名称的 Bean |
| `sqlAlchemySessionFactory` | `SessionFactory` | 同步模式且没有相同类型或名称的 Bean |
| `sqlAlchemyAsyncEngine` | `sqlalchemy.ext.asyncio.AsyncEngine` | 异步模式且没有相同类型或名称的 Bean |
| `sqlAlchemyAsyncSessionFactory` | `AsyncSessionFactory` | 异步模式且没有相同类型或名称的 Bean |

自动配置入口名称为 `sqlalchemy`，配置 Bean 在 order 1900、Engine 在 2000、工厂在 2100
装配。条件只依据 Bean 定义评估，不提前实例化资源。默认 Engine 创建不连接数据库；
第一次使用时连接。关闭应用时调用 `dispose()`，异步 Engine 的关闭由容器 await；
Web 应用通过已有 ASGI lifespan 启停容器。Session 不由容器追踪，调用方必须关闭。

用户提供 Engine Bean 时，默认 Engine 退让，默认工厂使用用户 Engine；配置 URL 可以省略。
用户提供工厂时，默认工厂退让；默认 Engine 是独立自动配置，仍会装配，若不需要它，
应排除对应 Engine 自动配置或关闭整个模块并自行提供资源。
用户提供资源时，关闭责任通过自己的 `destroy_method` 或生命周期回调声明。

后续连接池 Starter 可通过更早装配的自动配置提供原生 Engine。
外部连接池需要适配 SQLAlchemy 方言所要求的驱动协议，通常使用 `NullPool`
配合连接归还适配，避免两层池叠加；异步适配必须兼容异步方言，不能直接套同步 creator。
外部池由创建方关闭，不自动取得用户资源所有权。

## 多数据源

当前属性提供一个默认数据源；多个数据源通过应用自己的 Configuration Properties 和
命名 Engine／工厂 Bean 显式注册，不自动切换连接，也不提供跨库原子事务。
多候选时使用名称、限定符或 primary；不明确选择会由核心容器报错。

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

`OrderDatabaseProperties` 是应用自己的配置属性类；工厂参数使用名称限定对应 Engine。
参数名称本身不作为依赖限定符。
业务通过 `session_factory: AsyncSessionFactory = autowired(name="orderSessionFactory")` 注入。
多数据源时通常关闭默认装配并显式声明每组 Engine 和工厂。

## 公共 API 与示例

`pythonboot_sqlalchemy` 和 `pythonboot_starter_sqlalchemy` 显式导出
`SessionFactory`、`AsyncSessionFactory`、`DataSourceProperties`、`SqlAlchemyProperties`、
`PoolProperties` 和 `SessionProperties`。Engine、Session、模型和查询表达式从 SQLAlchemy 导入。
完整示例位于仓库 `examples/sqlalchemy/`，包含 SQLite 异步配置、ORM 模型、
Service 属性注入、查询 DTO 和显式提交；数据库结构需应用自己准备。
