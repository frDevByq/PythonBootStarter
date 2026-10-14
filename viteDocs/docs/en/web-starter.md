# Web Starter and implementation package

`pythonboot` provides IoC, Beans, AOP, configuration, transaction abstractions, and task execution
without FastAPI or Uvicorn. `pythonboot-web` in `modules/pythonboot-web` implements Web features;
`pythonboot-starter-web` in `starters/pythonboot-starter-web` aggregates the implementation and its dependencies.
Each package is published independently to PyPI.

```bash
uv add pythonboot-starter-web
```

Import core APIs from `pythonboot`. Import the application class, bootstrap decorator, `create_app`, controllers,
route decorators, `inject`, `date_time`, and `RequestContextHolder` from `pythonboot_web`.
The former core top-level Web exports, `pythonboot.web`, and `pythonboot.boot.application` were removed.
YAML keys under `pythonboot.web` and `pythonboot.docs` remain unchanged.

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

app = Application().app
```

For local development, keep the core and Starter repositories as sibling directories. The core repository's
`uv sync` installs the local Starter and Web implementation through its development group; use
`uv sync --no-dev` for core-only dependencies. Use `uv sync --all-packages` in the Starter workspace.
Local UV source paths do not enter published dependencies.


