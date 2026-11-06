"""Lazy optional backend imports and application-first authentication beans."""

import logging
from typing import Any
from pythonboot import (
    ContextUtil, auto_configuration, bean, conditional_on_missing_bean, conditional_on_property,
)
from pythonboot_auth.async_service import AsyncAuthService
from pythonboot_auth.exceptions import AuthConfigurationError
from pythonboot_auth.properties import AuthProperties
from pythonboot_auth.provider import AsyncStpInterface, StpInterface
from pythonboot_auth.serialization import JsonSessionSerializer, SessionSerializer
from pythonboot_auth.service import AuthService
from pythonboot_auth.storage import AsyncMemorySessionStore, AsyncSessionStore, MemorySessionStore, SessionStore

logger = logging.getLogger(__name__)


@auto_configuration(order=3900, imports=(AuthProperties,))
@conditional_on_property("pythonboot.auth.enabled", having_value=True, match_if_missing=True)
class AuthBaseAutoConfiguration:
    @bean(name="authSessionSerializer")
    @conditional_on_missing_bean(SessionSerializer, "authSessionSerializer")
    def serializer(self) -> SessionSerializer:
        logger.info("Configuring JSON authentication session serialization.")
        return JsonSessionSerializer()


def _redis_client(properties: AuthProperties, *, asynchronous: bool) -> Any:
    try:
        from pythonboot_redis import AsyncRedisClient, RedisClient
    except ImportError as error:
        raise AuthConfigurationError("Redis authentication storage requires pythonboot-starter-auth[redis]") from error
    client_type = AsyncRedisClient if asynchronous else RedisClient
    return ContextUtil.get_bean(client_type, name=properties.redis.client_name)


@auto_configuration(order=4000)
@conditional_on_property("pythonboot.auth.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.auth.mode", having_value="sync", match_if_missing=True)
class AuthSyncStorageAutoConfiguration:
    @bean(name="authSessionStore", destroy_method="close")
    @conditional_on_missing_bean(SessionStore, "authSessionStore")
    @conditional_on_property("pythonboot.auth.storage", having_value="memory", match_if_missing=True)
    def memory_store(self, properties: AuthProperties) -> SessionStore:
        if properties.storage != "memory":
            raise AuthConfigurationError("Auth storage must be selected in application YAML")
        logger.info("Creating process-local authentication memory store.")
        return MemorySessionStore()

    @bean(name="authSessionStore")
    @conditional_on_missing_bean(SessionStore, "authSessionStore")
    @conditional_on_property("pythonboot.auth.storage", having_value="redis")
    def redis_store(self, properties: AuthProperties) -> SessionStore:
        if properties.storage != "redis":
            raise AuthConfigurationError("Auth storage must be selected in application YAML")
        client = _redis_client(properties, asynchronous=False)
        from pythonboot_auth.redis_store import RedisSessionStore
        logger.info("Creating Redis authentication store using an application-managed client.")
        return RedisSessionStore(client, key_prefix=properties.redis.key_prefix)


@auto_configuration(order=4000)
@conditional_on_property("pythonboot.auth.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.auth.mode", having_value="async")
class AuthAsyncStorageAutoConfiguration:
    @bean(name="authAsyncSessionStore", destroy_method="close")
    @conditional_on_missing_bean(AsyncSessionStore, "authAsyncSessionStore")
    @conditional_on_property("pythonboot.auth.storage", having_value="memory", match_if_missing=True)
    def memory_store(self, properties: AuthProperties) -> AsyncSessionStore:
        if properties.storage != "memory":
            raise AuthConfigurationError("Auth storage must be selected in application YAML")
        logger.info("Creating process-local asynchronous authentication memory store.")
        return AsyncMemorySessionStore()

    @bean(name="authAsyncSessionStore")
    @conditional_on_missing_bean(AsyncSessionStore, "authAsyncSessionStore")
    @conditional_on_property("pythonboot.auth.storage", having_value="redis")
    def redis_store(self, properties: AuthProperties) -> AsyncSessionStore:
        if properties.storage != "redis":
            raise AuthConfigurationError("Auth storage must be selected in application YAML")
        client = _redis_client(properties, asynchronous=True)
        from pythonboot_auth.redis_store import AsyncRedisSessionStore
        logger.info("Creating asynchronous Redis authentication store using an application-managed client.")
        return AsyncRedisSessionStore(client, key_prefix=properties.redis.key_prefix)


@auto_configuration(order=4100)
@conditional_on_property("pythonboot.auth.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.auth.mode", having_value="sync", match_if_missing=True)
class AuthSyncAutoConfiguration:
    @bean(name="authService")
    @conditional_on_missing_bean(AuthService, "authService")
    def service(
        self, store: SessionStore, serializer: SessionSerializer, properties: AuthProperties,
        provider: StpInterface | None = None,
    ) -> AuthService:
        if not properties.enabled or properties.mode != "sync":
            raise AuthConfigurationError("Auth enabled and mode must be selected in application YAML")
        logger.info("Configuring synchronous authentication service with storage=%s.", properties.storage)
        return AuthService(store, serializer, properties, provider)


@auto_configuration(order=4100)
@conditional_on_property("pythonboot.auth.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.auth.mode", having_value="async")
class AuthAsyncAutoConfiguration:
    @bean(name="authAsyncService")
    @conditional_on_missing_bean(AsyncAuthService, "authAsyncService")
    def service(
        self, store: AsyncSessionStore, serializer: SessionSerializer, properties: AuthProperties,
        provider: AsyncStpInterface | None = None,
    ) -> AsyncAuthService:
        if not properties.enabled or properties.mode != "async":
            raise AuthConfigurationError("Auth enabled and mode must be selected in application YAML")
        logger.info("Configuring asynchronous authentication service with storage=%s.", properties.storage)
        return AsyncAuthService(store, serializer, properties, provider)
