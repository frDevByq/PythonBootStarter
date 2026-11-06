"""Executable authorization decorators preserve endpoint signatures and metadata."""

from collections.abc import Callable
from functools import wraps
import inspect
from typing import Any, TypeVar, get_type_hints

from pythonboot_auth.policy import CheckMode
from pythonboot_auth.util import AsyncAuthUtil, AuthUtil

T = TypeVar("T")


def _decorate(target: T, kind: str, codes: tuple[str, ...], mode: CheckMode) -> T:
    if inspect.isclass(target):
        methods = tuple(
            (name, method) for name, method in inspect.getmembers(target, inspect.isfunction)
            if getattr(method, "__pythonboot_routes__", ())
        )
        if not methods:
            raise TypeError("Class authentication decorators require PythonBoot route methods")
        for name, method in methods:
            setattr(target, name, _decorate(method, kind, codes, mode))
        return target
    if not inspect.isfunction(target):
        raise TypeError("Authentication decorators require a function or controller class")
    if inspect.iscoroutinefunction(target):
        @wraps(target)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            if kind == "login":
                await AsyncAuthUtil.check_login()
            elif kind == "permission":
                await AsyncAuthUtil.check_permission(*codes, mode=mode)
            else:
                await AsyncAuthUtil.check_role(*codes, mode=mode)
            return await target(*args, **kwargs)
    else:
        @wraps(target)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if kind == "login":
                AuthUtil.check_login()
            elif kind == "permission":
                AuthUtil.check_permission(*codes, mode=mode)
            else:
                AuthUtil.check_role(*codes, mode=mode)
            return target(*args, **kwargs)
    # Resolve annotations in their original module, including postponed annotations.
    try:
        wrapped.__annotations__ = get_type_hints(target, include_extras=True)
    except (NameError, TypeError) as error:
        raise TypeError("Cannot resolve decorated function annotations") from error
    signature = inspect.signature(target)
    wrapped.__signature__ = signature.replace(
        parameters=[parameter.replace(annotation=wrapped.__annotations__.get(name, parameter.annotation))
                    for name, parameter in signature.parameters.items()],
        return_annotation=wrapped.__annotations__.get("return", signature.return_annotation),
    )
    wrapped.__pythonboot_auth_required__ = True
    return wrapped


def require_login(target: T) -> T:
    return _decorate(target, "login", (), "and")


def _require(kind: str, codes: tuple[str, ...], mode: CheckMode) -> Callable[[T], T]:
    if mode not in ("and", "or") or not codes or any(not isinstance(code, str) or not code for code in codes):
        raise ValueError("Authentication decorators require non-empty codes and mode 'and' or 'or'")
    if kind == "permission" and any("*" in code for code in codes):
        raise ValueError("Required permissions must be concrete; wildcard grants come from StpInterface")
    return lambda target: _decorate(target, kind, codes, mode)


def require_permission(*permissions: str, mode: CheckMode = "and") -> Callable[[T], T]:
    return _require("permission", permissions, mode)


def require_role(*roles: str, mode: CheckMode = "and") -> Callable[[T], T]:
    return _require("role", roles, mode)
