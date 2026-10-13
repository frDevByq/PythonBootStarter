"""FastAPI routing, dependency injection, and exception handling integration."""

from pythonboot_web.integration import inject, register_exception_handlers, register_routers
from pythonboot_web.docs import register_api_docs, resolve_docs_options
from pythonboot_web.datetime import DateTimeFormatMiddleware, date_time, resolve_datetime_format
from pythonboot_web.context_middleware import ApplicationContextMiddleware
from pythonboot_web.request_context import RequestContextHolder
from pythonboot_web.decorators import (
    controller, controller_advise, delete, exception_handler, get, patch, post, put, route,
)

__all__ = [
    "controller", "controller_advise", "exception_handler", "route", "get", "post", "put", "patch", "delete",
    "inject", "register_routers", "register_exception_handlers", "resolve_datetime_format",
    "DateTimeFormatMiddleware", "date_time",
    "resolve_docs_options", "register_api_docs",
    "ApplicationContextMiddleware",
    "RequestContextHolder",
]

from pythonboot_web.application import PythonBootApplication, create_app
from pythonboot_web.bootstrap import pythonboot_application

__all__ += ["PythonBootApplication", "create_app", "pythonboot_application"]
