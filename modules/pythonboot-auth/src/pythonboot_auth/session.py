"""Session handles revalidate ownership and persist every mutation immediately."""

from typing import TYPE_CHECKING, Any, TypeVar, overload

if TYPE_CHECKING:
    from pythonboot_auth.service import AuthService
    from pythonboot_auth.async_service import AsyncAuthService

T = TypeVar("T")


class Session:
    def __init__(self, service: "AuthService", account_id: str, digest: str, *, token_session: bool) -> None:
        self._service = service
        self.account_id = account_id
        self._digest = digest
        self._token_session = token_session

    @overload
    def get(self, key: str, default: None = None, *, target_type: type[T]) -> T | None: ...

    @overload
    def get(self, key: str, default: T, *, target_type: type[T]) -> T: ...

    @overload
    def get(self, key: str, default: Any = None, *, target_type: Any = None) -> Any: ...

    def get(self, key: str, default: Any = None, *, target_type: Any = None) -> Any:
        return self._service._data(
            self.account_id, self._digest, self._token_session, "get", key,
            default=default, target_type=target_type,
        )

    def set(self, key: str, value: Any) -> None:
        self._service._data(self.account_id, self._digest, self._token_session, "set", key, value)

    def delete(self, key: str) -> bool:
        return self._service._data(self.account_id, self._digest, self._token_session, "delete", key)

    def keys(self) -> tuple[str, ...]:
        return self._service._data(self.account_id, self._digest, self._token_session, "keys")


class AsyncSession:
    def __init__(self, service: "AsyncAuthService", account_id: str, digest: str, *, token_session: bool) -> None:
        self._service = service
        self.account_id = account_id
        self._digest = digest
        self._token_session = token_session

    @overload
    async def get(self, key: str, default: None = None, *, target_type: type[T]) -> T | None: ...

    @overload
    async def get(self, key: str, default: T, *, target_type: type[T]) -> T: ...

    @overload
    async def get(self, key: str, default: Any = None, *, target_type: Any = None) -> Any: ...

    async def get(self, key: str, default: Any = None, *, target_type: Any = None) -> Any:
        return await self._service._data(
            self.account_id, self._digest, self._token_session, "get", key,
            default=default, target_type=target_type,
        )

    async def set(self, key: str, value: Any) -> None:
        await self._service._data(self.account_id, self._digest, self._token_session, "set", key, value)

    async def delete(self, key: str) -> bool:
        return await self._service._data(self.account_id, self._digest, self._token_session, "delete", key)

    async def keys(self) -> tuple[str, ...]:
        return await self._service._data(self.account_id, self._digest, self._token_session, "keys")
