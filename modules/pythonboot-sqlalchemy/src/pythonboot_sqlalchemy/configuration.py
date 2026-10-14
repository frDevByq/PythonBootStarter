"""Register native engines and session factories without implicit commits."""

import logging

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pythonboot import (
    auto_configuration, bean, conditional_on_missing_bean, conditional_on_property,
)
from pythonboot_sqlalchemy.engine import database_url, engine_options
from pythonboot_sqlalchemy.factories import AsyncSessionFactory, SessionFactory
from pythonboot_sqlalchemy.properties import DataSourceProperties, SqlAlchemyProperties

logger = logging.getLogger(__name__)


@auto_configuration(order=1900, imports=(DataSourceProperties, SqlAlchemyProperties))
@conditional_on_property("pythonboot.sqlalchemy.enabled", having_value=True, match_if_missing=True)
class SqlAlchemyPropertiesAutoConfiguration:
    """Bind connection and ORM properties before resource auto-configuration."""


@auto_configuration(order=2000)
@conditional_on_property("pythonboot.sqlalchemy.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.sqlalchemy.mode", having_value="sync")
class SqlAlchemySyncEngineAutoConfiguration:
    """Provide an application-owned synchronous engine unless one already exists."""

    @bean(name="sqlAlchemyEngine", destroy_method="dispose")
    @conditional_on_missing_bean(Engine, "sqlAlchemyEngine")
    def engine(self, properties: DataSourceProperties, orm: SqlAlchemyProperties) -> Engine:
        if not orm.enabled or orm.mode != "sync":
            raise ValueError("SQLAlchemy enabled and mode must be selected in application YAML")
        logger.info("Creating synchronous SQLAlchemy engine with pool_kind=%s.", properties.pool.kind)
        return create_engine(database_url(properties), **engine_options(properties, asynchronous=False))


@auto_configuration(order=2000)
@conditional_on_property("pythonboot.sqlalchemy.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.sqlalchemy.mode", having_value="async", match_if_missing=True)
class SqlAlchemyAsyncEngineAutoConfiguration:
    """Provide an application-owned async engine with awaited disposal on shutdown."""

    @bean(name="sqlAlchemyAsyncEngine", destroy_method="dispose")
    @conditional_on_missing_bean(AsyncEngine, "sqlAlchemyAsyncEngine")
    def engine(self, properties: DataSourceProperties, orm: SqlAlchemyProperties) -> AsyncEngine:
        if not orm.enabled or orm.mode != "async":
            raise ValueError("SQLAlchemy enabled and mode must be selected in application YAML")
        logger.info("Creating asynchronous SQLAlchemy engine with pool_kind=%s.", properties.pool.kind)
        return create_async_engine(database_url(properties), **engine_options(properties, asynchronous=True))


@auto_configuration(order=2100)
@conditional_on_property("pythonboot.sqlalchemy.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.sqlalchemy.mode", having_value="sync")
class SqlAlchemySyncSessionAutoConfiguration:
    """Create a native singleton factory; sessions remain explicitly scoped by callers."""

    @bean(name="sqlAlchemySessionFactory")
    @conditional_on_missing_bean(SessionFactory, "sqlAlchemySessionFactory")
    def session_factory(self, engine: Engine, properties: SqlAlchemyProperties) -> SessionFactory:
        logger.info("Creating synchronous SQLAlchemy session factory.")
        return SessionFactory(bind=engine, **properties.session.model_dump())


@auto_configuration(order=2100)
@conditional_on_property("pythonboot.sqlalchemy.enabled", having_value=True, match_if_missing=True)
@conditional_on_property("pythonboot.sqlalchemy.mode", having_value="async", match_if_missing=True)
class SqlAlchemyAsyncSessionAutoConfiguration:
    """Create a native async factory without sharing sessions across tasks."""

    @bean(name="sqlAlchemyAsyncSessionFactory")
    @conditional_on_missing_bean(AsyncSessionFactory, "sqlAlchemyAsyncSessionFactory")
    def session_factory(self, engine: AsyncEngine, properties: SqlAlchemyProperties) -> AsyncSessionFactory:
        logger.info("Creating asynchronous SQLAlchemy session factory.")
        return AsyncSessionFactory(bind=engine, **properties.session.model_dump())
