"""Typed database and ORM settings bound through PythonBoot configuration properties."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pythonboot import configuration_properties


class PoolProperties(BaseModel):
    """Pool options; omitted sizing values retain dialect-specific defaults."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["default", "queue", "null", "static"] = "default"
    size: int | None = Field(default=None, ge=1)
    max_overflow: int | None = Field(default=None, ge=-1)
    timeout: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    recycle: int | None = Field(default=None, ge=-1)
    pre_ping: bool = True

    @model_validator(mode="after")
    def validate_sizing(self) -> "PoolProperties":
        if self.kind in ("null", "static") and any(
            value is not None for value in (self.size, self.max_overflow, self.timeout)
        ):
            raise ValueError("Pool sizing options require a queue-compatible pool")
        return self


@configuration_properties("pythonboot.datasource")
class DataSourceProperties(BaseSettings):
    """Connection settings shared by default synchronous and asynchronous engines."""

    model_config = SettingsConfigDict(
        env_prefix="PYTHONBOOT_DATASOURCE_", env_nested_delimiter="__", extra="forbid",
    )

    url: SecretStr = SecretStr("")
    echo: bool = False
    hide_parameters: bool = True
    isolation_level: str | None = None
    connect_args: dict[str, Any] = Field(default_factory=dict)
    pool: PoolProperties = Field(default_factory=PoolProperties)


class SessionProperties(BaseModel):
    """Native sessionmaker options without automatic transaction boundaries."""

    model_config = ConfigDict(extra="forbid")

    expire_on_commit: bool = False
    autoflush: bool = True


class SoftDeleteProperties(BaseModel):
    """Opt-in logical deletion with application-defined marker values."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = False
    field: str = Field(default="is_delete", pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    active_value: bool | int | str = False
    deleted_value: bool | int | str = True

    @model_validator(mode="after")
    def validate_values(self) -> "SoftDeleteProperties":
        if self.active_value == self.deleted_value:
            raise ValueError("Soft-delete active and deleted values must differ")
        return self


@configuration_properties("pythonboot.sqlalchemy")
class SqlAlchemyProperties(BaseSettings):
    """ORM settings; mode and enabled select auto-configurations through YAML."""

    model_config = SettingsConfigDict(
        env_prefix="PYTHONBOOT_SQLALCHEMY_", env_nested_delimiter="__", extra="forbid",
    )

    enabled: bool = True
    mode: Literal["sync", "async"] = "async"
    session: SessionProperties = Field(default_factory=SessionProperties)
    soft_delete: SoftDeleteProperties = Field(default_factory=SoftDeleteProperties)
