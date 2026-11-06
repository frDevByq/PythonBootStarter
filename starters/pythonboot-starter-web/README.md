# pythonboot-starter-web

聚合 `pythonboot-web` 及其核心、FastAPI 和 Uvicorn 依赖。
使用 `uv add pythonboot-starter-web` 安装；Web 接口从 `pythonboot_web` 导入。
本包同时导出 `PythonBootApplication`、`create_app` 和 `pythonboot_application`。


完整分层应用见 [全量 Starter 示例](../../example/README.md)，包含全部 Starter、PostgreSQL／Redis 和同步／异步 HTTP 用法。
See the [complete Starter application](../../example/README.md) for all Starters and sync/async HTTP examples.


当前 FastAPI 应用自动注册为名为 `fastapiApp` 的单例 Bean，可通过 `app: FastAPI = autowired()` 注入，
或在容器启动后通过 `ContextUtil.get_bean(FastAPI)` 获取。每个应用使用独立实例；
`configure()` 执行时容器尚未启动，请直接使用传入的 `app`。禁用自动配置时此 Bean 仍会注册。


The current FastAPI application is registered as the singleton Bean `fastapiApp`.
Inject it with `app: FastAPI = autowired()` or obtain it with `ContextUtil.get_bean(FastAPI)` after container startup.
Each application has its own instance. The container has not started during `configure()`; use its `app` argument there.
The Bean is also registered when `auto_configure=False`.
