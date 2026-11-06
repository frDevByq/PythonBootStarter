"""Public authentication interfaces; optional Web and Redis modules stay unloaded."""

from pythonboot_auth.async_service import AsyncAuthService
from pythonboot_auth.context import AuthContext, AuthContextHolder
from pythonboot_auth.decorators import require_login, require_permission, require_role
from pythonboot_auth.exceptions import (
    AuthConfigurationError, AuthContextError, AuthError, AuthStorageError, CsrfError,
    NotLoginError, NotPermissionError, NotRoleError, SessionSerializationError,
)
from pythonboot_auth.models import LoginResult, SessionInfo
from pythonboot_auth.policy import CheckMode, permission_matches
from pythonboot_auth.properties import AuthProperties, RedisAuthProperties, SessionProperties, TokenProperties
from pythonboot_auth.provider import AsyncStpInterface, StpInterface
from pythonboot_auth.serialization import JsonSessionSerializer, SessionSerializer
from pythonboot_auth.service import AuthService
from pythonboot_auth.session import AsyncSession, Session
from pythonboot_auth.storage import AsyncMemorySessionStore, AsyncSessionStore, MemorySessionStore, SessionStore
from pythonboot_auth.util import AsyncAuthUtil, AuthUtil

__all__ = [
    "AuthService", "AsyncAuthService", "AuthUtil", "AsyncAuthUtil", "StpInterface", "AsyncStpInterface",
    "SessionStore", "AsyncSessionStore", "MemorySessionStore", "AsyncMemorySessionStore",
    "SessionSerializer", "JsonSessionSerializer", "Session", "AsyncSession", "SessionInfo", "LoginResult",
    "AuthProperties", "SessionProperties", "TokenProperties", "RedisAuthProperties",
    "AuthContext", "AuthContextHolder", "CheckMode", "permission_matches",
    "require_login", "require_permission", "require_role", "AuthError", "NotLoginError",
    "NotPermissionError", "NotRoleError", "AuthStorageError", "SessionSerializationError",
    "AuthConfigurationError", "AuthContextError", "CsrfError",
]
