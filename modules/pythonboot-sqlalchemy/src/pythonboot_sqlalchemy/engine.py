"""Build native engine options while preserving dialect and driver selection."""

from typing import Any

from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, QueuePool, StaticPool

from pythonboot_sqlalchemy.properties import DataSourceProperties


def engine_options(properties: DataSourceProperties, *, asynchronous: bool) -> dict[str, Any]:
    """Translate declared pool settings without guessing the database driver."""
    options: dict[str, Any] = {
        "echo": properties.echo,
        "hide_parameters": properties.hide_parameters,
        "connect_args": dict(properties.connect_args),
        "pool_pre_ping": properties.pool.pre_ping,
    }
    if properties.isolation_level is not None:
        options["isolation_level"] = properties.isolation_level
    pool = properties.pool
    if pool.kind == "queue":
        options["poolclass"] = AsyncAdaptedQueuePool if asynchronous else QueuePool
    elif pool.kind == "null":
        options["poolclass"] = NullPool
    elif pool.kind == "static":
        options["poolclass"] = StaticPool
    for name, value in (
        ("pool_size", pool.size),
        ("max_overflow", pool.max_overflow),
        ("pool_timeout", pool.timeout),
        ("pool_recycle", pool.recycle),
    ):
        if value is not None:
            options[name] = value
    return options


def database_url(properties: DataSourceProperties) -> str:
    """Require a URL only when the default engine is actually created."""
    url = properties.url.get_secret_value()
    if not url.strip():
        raise ValueError("pythonboot.datasource.url is required for the default SQLAlchemy engine")
    return url
