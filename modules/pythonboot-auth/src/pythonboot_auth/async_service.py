"""Asynchronous authentication with atomic session transitions and dynamic grants."""

from collections.abc import Callable
import logging
from typing import Any, TypeVar

from pythonboot_auth.exceptions import AuthConfigurationError, NotLoginError
from pythonboot_auth.models import LoginResult, SessionInfo
from pythonboot_auth.policy import CheckMode, _Policy, _UNSET, check_grants
from pythonboot_auth.properties import AuthProperties
from pythonboot_auth.provider import AsyncStpInterface
from pythonboot_auth.serialization import JsonSessionSerializer, SessionSerializer
from pythonboot_auth.session import AsyncSession
from pythonboot_auth.storage import AsyncSessionStore, State

logger = logging.getLogger(__name__)
T = TypeVar("T")


class AsyncAuthService(_Policy):
    def __init__(
        self, store: AsyncSessionStore, serializer: SessionSerializer | None = None,
        properties: AuthProperties | None = None, provider: AsyncStpInterface | None = None,
    ) -> None:
        super().__init__(serializer if serializer is not None else JsonSessionSerializer(), properties)
        self.store = store
        self.provider = provider

    async def _update(self, account_id: str, operation: Callable[[State], T]) -> T:
        for _ in range(self.properties.update_retries):
            previous = await self.store.get(account_id)
            revision = previous["revision"] if previous else None
            state = self.prepare(previous)
            result = operation(state)
            if await self.store.compare_and_set(account_id, revision, state, self.finalize(state)):
                return result
        raise self.contention()

    async def _with_token(self, token: Any, operation: Callable[[State, str], T]) -> T:
        digest = self.digest(token)
        account_id = await self.store.lookup(digest)
        if account_id is None:
            raise NotLoginError("invalid_or_expired")
        return await self._update(account_id, lambda state: operation(state, digest))

    async def login(
        self, login_id: str | int, *, login_type: str | None = None, device: str = "default",
    ) -> LoginResult:
        account_id, digest, record, result = self.new_login(login_id, login_type, device)
        await self._update(account_id, lambda state: self.add_login(state, digest, record))
        logger.info("Created authentication session for login_type=%s.", record["login_type"])
        return result

    async def _require_login(self, token: Any = _UNSET) -> SessionInfo:
        return await self._with_token(token, lambda state, digest: self.info(self.require(state, digest)))

    async def check_login(self, token: Any = _UNSET) -> SessionInfo | None:
        if not self.properties.check_enabled:
            return None
        return await self._require_login(token)

    async def is_login(self, token: Any = _UNSET) -> bool:
        try:
            return await self.check_login(token) is not None
        except NotLoginError:
            return False

    async def current_subject(self, token: Any = _UNSET) -> str:
        return (await self._require_login(token)).login_id

    async def logout(self, token: Any = _UNSET) -> None:
        def revoke(state: State, digest: str) -> None:
            record = self.require(state, digest, touch=False)
            record["status"] = "logged_out"
            record["data"] = {}
            if not any(value["status"] == "active" for value in state["tokens"].values()):
                state["data"] = {}
        await self._with_token(token, revoke)
        logger.info("Logged out authentication session.")

    async def kickout(
        self, login_id: str | int, *, login_type: str | None = None,
        device: str | None = None, session_id: str | None = None,
    ) -> int:
        kind = self.properties.login_type if login_type is None else login_type
        _, account_id = self.identity(login_id, kind)
        def revoke(state: State) -> int:
            count = 0
            for record in state["tokens"].values():
                if record["status"] == "active" and (device is None or record["device"] == device) and (
                    session_id is None or record["session_id"] == session_id
                ):
                    record["status"] = "kicked_out"
                    record["data"] = {}
                    count += 1
            if not any(record["status"] == "active" for record in state["tokens"].values()):
                state["data"] = {}
            return count
        count = await self._update(account_id, revoke)
        logger.info("Revoked %d authentication sessions for login_type=%s.", count, kind)
        return count

    async def list_sessions(
        self, login_id: str | int, *, login_type: str | None = None, include_inactive: bool = False,
    ) -> list[SessionInfo]:
        kind = self.properties.login_type if login_type is None else login_type
        _, account_id = self.identity(login_id, kind)
        return await self._update(account_id, lambda state: sorted(
            (self.info(record) for record in state["tokens"].values()
             if include_inactive or record["status"] == "active"),
            key=lambda info: (info.created_at, info.session_id),
        ))

    async def check_permission(self, *permissions: str, token: Any = _UNSET, mode: CheckMode = "and") -> None:
        if not self.properties.check_enabled:
            return
        subject = await self._require_login(token)
        if self.provider is None:
            raise AuthConfigurationError("Register an AsyncStpInterface Bean before checking permissions")
        check_grants(permissions, await self.provider.get_permission_list(subject.login_id, subject.login_type), mode, roles=False)

    async def check_role(self, *roles: str, token: Any = _UNSET, mode: CheckMode = "and") -> None:
        if not self.properties.check_enabled:
            return
        subject = await self._require_login(token)
        if self.provider is None:
            raise AuthConfigurationError("Register an AsyncStpInterface Bean before checking roles")
        check_grants(roles, await self.provider.get_role_list(subject.login_id, subject.login_type), mode, roles=True)

    async def check_csrf(self, csrf_token: str | None, *, token: Any = _UNSET) -> None:
        await self._with_token(token, lambda state, digest: self.csrf(self.require(state, digest), csrf_token))

    async def get_session(self, token: Any = _UNSET) -> AsyncSession:
        digest = self.digest(token)
        account_id = await self.store.lookup(digest)
        if account_id is None:
            raise NotLoginError("invalid_or_expired")
        await self._update(account_id, lambda state: self.require(state, digest))
        return AsyncSession(self, account_id, digest, token_session=False)

    async def get_token_session(self, token: Any = _UNSET) -> AsyncSession:
        session = await self.get_session(token)
        return AsyncSession(self, session.account_id, session._digest, token_session=True)

    async def _data(
        self, account_id: str, digest: str, token_session: bool,
        operation: str, key: str | None = None, value: Any = None, default: Any = None,
        target_type: Any = None,
    ) -> Any:
        encoded = self.encode(value) if operation == "set" else None
        result = await self._update(account_id, lambda state: self.session_data(
            state, digest, token_session, operation, key, encoded,
        ))
        if operation == "get":
            return default if result is _UNSET else self.decode(result, target_type=target_type)
        return result
