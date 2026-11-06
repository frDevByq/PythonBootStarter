"""Application-owned credentials and role lookup for local demonstration only."""

from collections.abc import Sequence

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pythonboot import bean, component, configuration, configuration_properties
from pythonboot_starter_auth import (
    AsyncStpInterface, AuthProperties, AuthService, MemorySessionStore,
    SessionSerializer, SessionStore, StpInterface,
)


@configuration_properties("example_auth")
class ExampleAuthProperties(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXAMPLE_AUTH_", env_nested_delimiter="__", extra="forbid")
    accounts: dict[str, SecretStr]


def permissions(login_id: str, login_type: str) -> Sequence[str]:
    if login_type != "user":
        return ()
    return ("example:*", "admin:session:*") if login_id == "admin" else ("example:read",) if login_id == "reader" else ()


def roles(login_id: str, login_type: str) -> Sequence[str]:
    if login_type != "user":
        return ()
    return ("admin",) if login_id == "admin" else ("reader",) if login_id == "reader" else ()


@component
class ExampleStpInterface(StpInterface):
    def get_permission_list(self, login_id: str, login_type: str) -> Sequence[str]:
        return permissions(login_id, login_type)

    def get_role_list(self, login_id: str, login_type: str) -> Sequence[str]:
        return roles(login_id, login_type)


@component
class ExampleAsyncStpInterface(AsyncStpInterface):
    async def get_permission_list(self, login_id: str, login_type: str) -> Sequence[str]:
        return permissions(login_id, login_type)

    async def get_role_list(self, login_id: str, login_type: str) -> Sequence[str]:
        return roles(login_id, login_type)


@configuration
class ExampleAuthConfiguration:
    @bean(name="exampleSyncAuthStore", destroy_method="close")
    def sync_store(self) -> SessionStore:
        return MemorySessionStore()

    @bean(name="exampleSyncAuthService", qualifiers=("sync",))
    def sync_service(
        self, store: SessionStore, serializer: SessionSerializer,
        properties: AuthProperties, provider: StpInterface,
    ) -> AuthService:
        return AuthService(store, serializer, properties.model_copy(update={"mode": "sync", "storage": "memory"}), provider)
