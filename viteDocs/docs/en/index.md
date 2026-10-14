# PythonBoot Starter

The PythonBoot Starter repository maintains independently published implementation modules and Starter packages.
This site contains installation, configuration, public API, and examples for every Starter.

[Redis Starter](/en/redis.html) integrates redis-py with native client injection, Configuration Properties,
sync/async static utilities, and distributed locks. Install `pythonboot-starter-redis` to use it.

`pythonboot-starter-web` currently aggregates `pythonboot-web`, `pythonboot`, FastAPI, and Uvicorn.

[SQLAlchemy Starter](/en/sqlalchemy.html) provides native Engine and Session factory Beans through
Configuration Properties. Install `pythonboot-starter-sqlalchemy` and your driver, create Sessions
explicitly, and commit in business code. Scope exit closes resources without automatic commits or schema creation.

```bash
uv add pythonboot-starter-web
```

`pythonboot` provides the core container, Beans, AOP, configuration, transaction abstractions, and task execution.
`pythonboot_web` provides Web bootstrap, controllers, routes, request context, and FastAPI integration.

Start with [Installation and modules](/en/web-starter.html).


[Complete Starter application](./example.md): all Starters, PostgreSQL/Redis, layered application structure, and sync/async HTTP examples.
