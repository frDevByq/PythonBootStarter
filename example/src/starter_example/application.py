"""Run the complete application with python -m starter_example.application."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response

from pythonboot_starter_web import PythonBootApplication, pythonboot_application


@asynccontextmanager
async def native_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Compose an application-owned lifespan with managed Bean startup and shutdown."""
    app.state.native_ready = True
    try:
        yield
    finally:
        app.state.native_ready = False


@pythonboot_application
class Application(PythonBootApplication):
    """Scan the application package and discover installed Starter entry points."""

    def configure(self, app: FastAPI) -> None:
        @app.middleware("http")
        async def application_header(
            request: Request, call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            response = await call_next(request)
            response.headers["X-Application"] = "pythonboot-starter-example"
            return response


application = Application(
    title="PythonBoot Starter Example",
    config_dir=Path(__file__).parent / "config",
    lifespan=native_lifespan,
)
app = application.app


if __name__ == "__main__":
    application.run(port=18000)
