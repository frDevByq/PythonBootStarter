"""Explicit FastAPI registration; dependencies raise errors inside exception handling."""

from collections.abc import Callable
import logging

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Receive, Scope, Send

from pythonboot import ContextUtil
from pythonboot_auth.async_service import AsyncAuthService
from pythonboot_auth.context import AuthContext, AuthContextHolder
from pythonboot_auth.exceptions import AuthConfigurationError
from pythonboot_auth.policy import permission_matches
from pythonboot_auth.properties import AuthProperties
from pythonboot_auth.service import AuthService

logger = logging.getLogger(__name__)


class _AuthContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        container = request.app.state.context
        with ContextUtil.use(container):
            properties = container.get_bean(AuthProperties)
            values = request.headers.getlist(properties.token.header)
            token: str | None = None
            malformed = len(values) > 1
            from_cookie = False
            if values:
                parts = values[0].split()
                if len(parts) == 2 and parts[0].lower() == "bearer" and len(parts[1]) <= 1024:
                    token = parts[1]
                else:
                    malformed = True
            elif properties.token.cookie is not None:
                token = request.cookies.get(properties.token.cookie)
                from_cookie = token is not None
            context = AuthContext(
                token=token, malformed=malformed, from_cookie=from_cookie,
                csrf_token=request.headers.get(properties.token.csrf_header),
                unsafe_request=request.method not in ("GET", "HEAD", "OPTIONS"),
            )
            with AuthContextHolder.use(context=context):
                await self.app(scope, receive, send)


class AuthInterceptor:
    """Include rules require login; exclusions bypass rules but never explicit decorators."""

    def __init__(
        self, *, include: tuple[str, ...] = (), exclude: tuple[str, ...] = (),
        service_resolver: Callable[[Request], AuthService | AsyncAuthService] | None = None,
    ) -> None:
        for patterns in (include, exclude):
            if isinstance(patterns, str) or any(not isinstance(pattern, str) or not pattern for pattern in patterns):
                raise ValueError("Interceptor paths must be sequences of non-empty strings")
        self.include = tuple(include)
        self.exclude = tuple(exclude)
        self.service_resolver = service_resolver

    async def check(self, request: Request) -> None:
        container = request.app.state.context
        properties = container.get_bean(AuthProperties)
        if not properties.enabled:
            raise AuthConfigurationError("An installed AuthInterceptor requires pythonboot.auth.enabled=true")
        if not properties.check_enabled:
            return
        endpoint = request.scope.get("endpoint")
        declared = bool(getattr(endpoint, "__pythonboot_auth_required__", False))
        path = request.scope.get("path", request.url.path)
        protected = any(permission_matches(pattern, path) for pattern in self.include) and not any(
            permission_matches(pattern, path) for pattern in self.exclude
        )
        if not protected and not declared:
            return
        auth_context = AuthContextHolder.current()
        service = (
            self.service_resolver(request) if self.service_resolver is not None
            else container.get_bean(AsyncAuthService if properties.mode == "async" else AuthService)
        )
        if isinstance(service, AsyncAuthService):
            await service.check_login()
            if auth_context.from_cookie and auth_context.unsafe_request:
                await service.check_csrf(auth_context.csrf_token)
        elif isinstance(service, AuthService):
            def check() -> None:
                service.check_login()
                if auth_context.from_cookie and auth_context.unsafe_request:
                    service.check_csrf(auth_context.csrf_token)
            await run_in_threadpool(check)
        else:
            raise AuthConfigurationError("AuthInterceptor resolver must return AuthService or AsyncAuthService")

    def install(self, app: FastAPI) -> None:
        install_auth_interceptor(app, interceptor=self)


def install_auth_interceptor(
    app: FastAPI, *, interceptor: AuthInterceptor | None = None,
    include: tuple[str, ...] = (), exclude: tuple[str, ...] = (),
) -> None:
    """Install once during application configuration, after existing routes are declared."""
    if getattr(app.state, "pythonboot_auth_installed", False):
        raise AuthConfigurationError("AuthInterceptor is already installed on this application")
    if interceptor is not None and (include or exclude):
        raise ValueError("Pass an interceptor or path rules, not both")
    selected = interceptor if interceptor is not None else AuthInterceptor(include=include, exclude=exclude)
    dependency = Depends(selected.check)
    original_routes = tuple(app.router.routes)
    app.router.routes.clear()
    # Rebuild API routes through public APIs while retaining the original route order.
    for route in original_routes:
        if isinstance(route, APIRoute):
            existing = APIRouter()
            existing.routes.append(route)
            app.include_router(existing, dependencies=[dependency])
        else:
            app.router.routes.append(route)
    app.router.dependencies.append(dependency)
    app.add_middleware(_AuthContextMiddleware)
    app.state.pythonboot_auth_installed = True
    app.openapi_schema = None
    logger.info("Registered authentication interceptor with %d include and %d exclude rules.", len(selected.include), len(selected.exclude))
