"""Connection settings bound through PythonBoot Configuration Properties."""

from typing import Any, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from pythonboot import configuration_properties


@configuration_properties("pythonboot.redis")
class RedisProperties(BaseSettings):
    """Native standalone Redis connection options; connections open on first command."""

    model_config = SettingsConfigDict(env_prefix="PYTHONBOOT_REDIS_", extra="forbid")

    enabled: bool = True
    mode: Literal["sync", "async"] = "sync"
    url: SecretStr = SecretStr("redis://localhost:6379/0")
    username: str | None = None
    password: SecretStr | None = None
    decode_responses: bool = True
    encoding: str = Field(default="utf-8", min_length=1)
    max_connections: int = Field(default=50, ge=1)
    socket_timeout: float = Field(default=5, gt=0, allow_inf_nan=False)
    socket_connect_timeout: float = Field(default=5, gt=0, allow_inf_nan=False)
    health_check_interval: int = Field(default=30, ge=0)

    def connection_options(self) -> dict[str, Any]:
        """Return keyword options without exposing secret representations."""
        options: dict[str, Any] = {
            "decode_responses": self.decode_responses,
            "encoding": self.encoding,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "health_check_interval": self.health_check_interval,
        }
        if self.username is not None:
            options["username"] = self.username
        if self.password is not None:
            options["password"] = self.password.get_secret_value()
        return options

    def connection_url(self, mode: Literal["sync", "async"]) -> str:
        """Validate selection before constructing a default connection pool."""
        if not self.enabled or self.mode != mode:
            raise ValueError("Redis enabled and mode must be selected in application YAML")
        url = self.url.get_secret_value()
        if not url.strip():
            raise ValueError("pythonboot.redis.url must not be empty")
        return url
