# PythonBoot Starter

PythonBoot Starter 仓库集中维护可独立发布的功能实现包和启动依赖包。
每个 Starter 的安装、配置、公开 API 和示例都在本站维护。

当前提供 `pythonboot-starter-web`，它聚合 `pythonboot-web`、`pythonboot`、FastAPI 和 Uvicorn。

```bash
uv add pythonboot-starter-web
```

核心容器、Bean、AOP、配置、事务抽象和任务执行由 `pythonboot` 提供；
Web 启动、Controller、路由、请求上下文和 FastAPI 集成由 `pythonboot_web` 提供。

从 [安装与模块拆分](/zh/web-starter.html) 开始。
