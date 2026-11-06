"""Authentication properties; backend selection is explicit in application YAML."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pythonboot import configuration_properties


class SessionProperties(BaseModel):
    model_config = {"extra": "forbid"}
    timeout: int = Field(default=86400, ge=1)
    idle_timeout: int = Field(default=1800, ge=1)
    concurrent: bool = True
    same_device_exclusive: bool = True
    max_sessions: int = Field(default=5, ge=1)


class TokenProperties(BaseModel):
    model_config = {"extra": "forbid"}
    header: str = Field(default="Authorization", min_length=1)
    cookie: str | None = None
    csrf_header: str = Field(default="X-CSRF-Token", min_length=1)


class RedisAuthProperties(BaseModel):
    model_config = {"extra": "forbid"}
    key_prefix: str = Field(default="pythonboot:auth:", min_length=1)
    client_name: str | None = None

    @model_validator(mode="after")
    def validate_prefix(self) -> "RedisAuthProperties":
        if "{" in self.key_prefix or "}" in self.key_prefix:
            raise ValueError("Auth Redis key_prefix must not contain hash-tag braces")
        return self


@configuration_properties("pythonboot.auth")
class AuthProperties(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PYTHONBOOT_AUTH_", env_nested_delimiter="__", extra="forbid",
    )
    enabled: bool = True
    check_enabled: bool = True
    mode: Literal["sync", "async"] = "sync"
    storage: Literal["memory", "redis"] = "memory"
    login_type: str = Field(default="user", min_length=1)
    session: SessionProperties = Field(default_factory=SessionProperties)
    token: TokenProperties = Field(default_factory=TokenProperties)
    redis: RedisAuthProperties = Field(default_factory=RedisAuthProperties)
    update_retries: int = Field(default=16, ge=1, le=100)
