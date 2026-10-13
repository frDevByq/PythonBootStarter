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
