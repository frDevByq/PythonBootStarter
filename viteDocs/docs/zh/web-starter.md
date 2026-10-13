# Web Starter 与独立实现包

`pythonboot` 提供 IoC、Bean、AOP、配置、事务抽象和任务执行，不依赖 FastAPI 或 Uvicorn。
`pythonboot-web` 位于 `modules/pythonboot-web`，实现 Web 功能；
`pythonboot-starter-web` 位于 `starters/pythonboot-starter-web`，聚合实现包及其依赖。
各包分别发布到 PyPI。

```bash
uv add pythonboot-starter-web
```

核心接口从 `pythonboot` 导入；启动类、启动装饰器、`create_app`、Controller、
路由装饰器、`inject`、`date_time` 和 `RequestContextHolder` 从 `pythonboot_web` 导入。
旧的核心包顶层 Web 导出、`pythonboot.web` 及 `pythonboot.boot.application` 已移除。
YAML 配置键 `pythonboot.web` 和 `pythonboot.docs` 保持不变。

```python
from pythonboot import autowired, service
from pythonboot_web import PythonBootApplication, controller, get, pythonboot_application

@service
class GreetingService:
    def greeting(self) -> str:
        return "Hello"

@controller(prefix="/greeting", tags=["问候"])
class GreetingController:
    service: GreetingService = autowired()

    @get("", summary="获取问候")
    def greeting(self) -> str:
        return self.service.greeting()

@pythonboot_application(scan_packages=("myapp",))
class Application(PythonBootApplication):
    pass

app = Application().app
```

本地开发时，将核心仓库与 Starter 仓库放在同级目录。核心仓库使用 `uv sync`
安装开发组中的本地 Starter 与 Web 实现；仅需核心能力时使用 `uv sync --no-dev`。
Starter 工作区使用 `uv sync --all-packages`。UV sources 的本地路径不进入发布依赖。
