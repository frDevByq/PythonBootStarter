# pythonboot-web

PythonBoot 的独立 Web 实现包，包含 Controller、路由、异常处理、请求与响应上下文、
日期格式化、API 文档、ASGI 生命周期和 Web 启动类。

依赖 `pythonboot`、FastAPI 和 Uvicorn，用户推荐安装 `pythonboot-starter-web`。
核心接口从 `pythonboot` 导入，Web 接口从 `pythonboot_web` 导入。
原来的 `pythonboot.web` 和核心包顶层 Web 导出已移除。
YAML 的 `pythonboot.web` 配置键保持不变。

```python
from pythonboot import autowired, service
from pythonboot_web import PythonBootApplication, controller, get, pythonboot_application

@service
class GreetingService:
    def greeting(self) -> str:
        return "Hello"

@controller(prefix="/greeting")
class GreetingController:
    service: GreetingService = autowired()

    @get("")
    def greeting(self) -> str:
        return self.service.greeting()

@pythonboot_application(scan_packages=("myapp",))
class Application(PythonBootApplication):
    pass
```


完整分层应用见 [全量 Starter 示例](../../example/README.md)，包含全部 Starter、PostgreSQL／Redis 和同步／异步 HTTP 用法。
See the [complete Starter application](../../example/README.md) for all Starters and sync/async HTTP examples.
