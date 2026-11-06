"""Static convenience entry points resolve services from the current container."""

from typing import Any
from pythonboot import ContextUtil
from pythonboot_auth.async_service import AsyncAuthService
from pythonboot_auth.models import LoginResult, SessionInfo
from pythonboot_auth.policy import CheckMode, _UNSET
from pythonboot_auth.service import AuthService
from pythonboot_auth.session import AsyncSession, Session


class AuthUtil:
    @staticmethod
    def get_service(*, name: str | None = None, qualifier: str | None = None) -> AuthService:
        return ContextUtil.get_bean(AuthService, name=name, qualifier=qualifier)

    @staticmethod
    def login(login_id: str | int, *, login_type: str | None = None, device: str = "default") -> LoginResult:
        return AuthUtil.get_service().login(login_id, login_type=login_type, device=device)

    @staticmethod
    def check_login(token: Any = _UNSET) -> SessionInfo | None:
        return AuthUtil.get_service().check_login(token)

    @staticmethod
    def is_login(token: Any = _UNSET) -> bool:
        return AuthUtil.get_service().is_login(token)

    @staticmethod
    def current_subject(token: Any = _UNSET) -> str:
        return AuthUtil.get_service().current_subject(token)

    @staticmethod
    def logout(token: Any = _UNSET) -> None:
        AuthUtil.get_service().logout(token)

    @staticmethod
    def kickout(login_id: str | int, **options: Any) -> int:
        return AuthUtil.get_service().kickout(login_id, **options)

    @staticmethod
    def list_sessions(login_id: str | int, **options: Any) -> list[SessionInfo]:
        return AuthUtil.get_service().list_sessions(login_id, **options)

    @staticmethod
    def check_permission(*permissions: str, token: Any = _UNSET, mode: CheckMode = "and") -> None:
        AuthUtil.get_service().check_permission(*permissions, token=token, mode=mode)

    @staticmethod
    def check_role(*roles: str, token: Any = _UNSET, mode: CheckMode = "and") -> None:
        AuthUtil.get_service().check_role(*roles, token=token, mode=mode)

    @staticmethod
    def check_csrf(csrf_token: str | None, *, token: Any = _UNSET) -> None:
        AuthUtil.get_service().check_csrf(csrf_token, token=token)

    @staticmethod
    def get_session(token: Any = _UNSET) -> Session:
        return AuthUtil.get_service().get_session(token)

    @staticmethod
    def get_token_session(token: Any = _UNSET) -> Session:
        return AuthUtil.get_service().get_token_session(token)


class AsyncAuthUtil:
    @staticmethod
    def get_service(*, name: str | None = None, qualifier: str | None = None) -> AsyncAuthService:
        return ContextUtil.get_bean(AsyncAuthService, name=name, qualifier=qualifier)

    @staticmethod
    async def login(login_id: str | int, *, login_type: str | None = None, device: str = "default") -> LoginResult:
        return await AsyncAuthUtil.get_service().login(login_id, login_type=login_type, device=device)

    @staticmethod
    async def check_login(token: Any = _UNSET) -> SessionInfo | None:
        return await AsyncAuthUtil.get_service().check_login(token)

    @staticmethod
    async def is_login(token: Any = _UNSET) -> bool:
        return await AsyncAuthUtil.get_service().is_login(token)

    @staticmethod
    async def current_subject(token: Any = _UNSET) -> str:
        return await AsyncAuthUtil.get_service().current_subject(token)

    @staticmethod
    async def logout(token: Any = _UNSET) -> None:
        await AsyncAuthUtil.get_service().logout(token)

    @staticmethod
    async def kickout(login_id: str | int, **options: Any) -> int:
        return await AsyncAuthUtil.get_service().kickout(login_id, **options)

    @staticmethod
    async def list_sessions(login_id: str | int, **options: Any) -> list[SessionInfo]:
        return await AsyncAuthUtil.get_service().list_sessions(login_id, **options)

    @staticmethod
    async def check_permission(*permissions: str, token: Any = _UNSET, mode: CheckMode = "and") -> None:
        await AsyncAuthUtil.get_service().check_permission(*permissions, token=token, mode=mode)

    @staticmethod
    async def check_role(*roles: str, token: Any = _UNSET, mode: CheckMode = "and") -> None:
        await AsyncAuthUtil.get_service().check_role(*roles, token=token, mode=mode)

    @staticmethod
    async def check_csrf(csrf_token: str | None, *, token: Any = _UNSET) -> None:
        await AsyncAuthUtil.get_service().check_csrf(csrf_token, token=token)

    @staticmethod
    async def get_session(token: Any = _UNSET) -> AsyncSession:
        return await AsyncAuthUtil.get_service().get_session(token)

    @staticmethod
    async def get_token_session(token: Any = _UNSET) -> AsyncSession:
        return await AsyncAuthUtil.get_service().get_token_session(token)
