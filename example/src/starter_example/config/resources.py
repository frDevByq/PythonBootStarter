"""Add synchronous named resources alongside asynchronous auto-configuration."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis import ConnectionPool
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine

from pythonboot import bean, configuration, configuration_properties
from pythonboot_starter_redis import RedisClient, RedisProperties
from pythonboot_starter_sqlalchemy import AsyncSessionFactory, SessionFactory, SqlAlchemyProperties
from pythonboot_starter_sqlalchemy import AsyncSoftDeleteSession, SoftDeleteSession


@configuration_properties("example")
class ExampleProperties(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXAMPLE_", extra="forbid")

    name: str = "PythonBoot Starter Example"
    sync_database_url: SecretStr


@configuration
class ResourceConfiguration:
    """Custom providers explicitly own synchronous resource cleanup."""

    @bean(name="sqlAlchemyAsyncSessionFactory")
    def async_session_factory(self, engine: AsyncEngine, settings: SqlAlchemyProperties) -> AsyncSessionFactory:
        """An application factory makes the matching default auto-configuration back off."""
        options = settings.session.model_dump()
        if settings.soft_delete.enabled:
            options.update(class_=AsyncSoftDeleteSession, soft_delete=settings.soft_delete)
        return AsyncSessionFactory(bind=engine, **options)

    @bean(name="exampleSyncEngine", qualifiers=("sync",), destroy_method="dispose")
    def sync_engine(self, settings: ExampleProperties) -> Engine:
        return create_engine(settings.sync_database_url.get_secret_value(), pool_pre_ping=True)

    @bean(name="exampleSyncSessionFactory", qualifiers=("sync",))
    def sync_session_factory(self, engine: Engine, settings: SqlAlchemyProperties) -> SessionFactory:
        options = settings.session.model_dump()
        if settings.soft_delete.enabled:
            options.update(class_=SoftDeleteSession, soft_delete=settings.soft_delete)
        return SessionFactory(bind=engine, **options)

    @bean(name="exampleSyncRedisPool", destroy_method="disconnect")
    def sync_redis_pool(self, settings: RedisProperties) -> ConnectionPool:
        return ConnectionPool.from_url(settings.url.get_secret_value(), **settings.connection_options())

    @bean(name="exampleSyncRedisClient", qualifiers=("sync",), destroy_method="close")
    def sync_redis_client(self, pool: ConnectionPool) -> RedisClient:
        return RedisClient(connection_pool=pool)
