"""Explicit authentication context binding with guaranteed restoration."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from pythonboot_auth.exceptions import AuthContextError, NotLoginError


@dataclass(frozen=True)
class AuthContext:
    token: str | None = field(default=None, repr=False)
    malformed: bool = False
    from_cookie: bool = False
    csrf_token: str | None = field(default=None, repr=False)
    unsafe_request: bool = False


_current: ContextVar[AuthContext | None] = ContextVar("pythonboot_auth_context", default=None)


class AuthContextHolder:
    @staticmethod
    def current() -> AuthContext:
        context = _current.get()
        if context is None:
            raise AuthContextError("No authentication context is bound; pass a token or use AuthContextHolder.use")
        return context

    @staticmethod
    def token() -> str | None:
        context = _current.get()
        if context is None:
            raise NotLoginError("missing_token")
        if context.malformed:
            raise NotLoginError("malformed_token")
        return context.token

    @staticmethod
    @contextmanager
    def use(token: str | None = None, *, context: AuthContext | None = None) -> Iterator[AuthContext]:
        value = context if context is not None else AuthContext(token=token)
        binding = _current.set(value)
        try:
            yield value
        finally:
            _current.reset(binding)
