"""Authentication failures never manufacture an HTTP response."""


class AuthError(Exception):
    """Base authentication and authorization error."""


class NotLoginError(AuthError):
    def __init__(self, reason: str = "missing_token") -> None:
        self.reason = reason
        super().__init__("Not logged in")


class NotPermissionError(AuthError):
    def __init__(self, permissions: tuple[str, ...], mode: str) -> None:
        self.permissions = permissions
        self.mode = mode
        super().__init__(f"Required permissions are not granted ({mode}): {', '.join(permissions)}")


class NotRoleError(AuthError):
    def __init__(self, roles: tuple[str, ...], mode: str) -> None:
        self.roles = roles
        self.mode = mode
        super().__init__(f"Required roles are not granted ({mode}): {', '.join(roles)}")


class AuthStorageError(AuthError):
    """Storage unavailable, invalid stored data, or concurrent update exhausted."""


class SessionSerializationError(AuthError):
    """A session value cannot be encoded or decoded by the selected serializer."""


class AuthContextError(AuthError):
    """No authentication context is bound to this execution scope."""


class CsrfError(AuthError):
    """Cookie authentication requires a valid CSRF token for unsafe requests."""


class AuthConfigurationError(AuthError):
    """An explicitly requested authentication capability is not configured."""
