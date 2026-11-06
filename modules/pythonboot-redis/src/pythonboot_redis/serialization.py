"""Application-scoped serializers for Redis utility set/get operations."""

from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from pythonboot_redis.client import RedisResult, RedisValue


class RedisSerializer(ABC):
    """Synchronous codec shared by synchronous and asynchronous utility methods."""

    @abstractmethod
    def dumps(self, value: Any) -> RedisValue:
        """Encode a value into a native redis-py input."""

    @abstractmethod
    def loads(self, value: RedisResult) -> Any:
        """Decode a stored value; decoding failures must propagate."""


class JsonRedisSerializer(RedisSerializer):
    """Encode models, dataclasses, and ordinary object attributes as JSON."""

    def dumps(self, value: Any) -> str:
        return json.dumps(value, default=self._default, ensure_ascii=True, allow_nan=False, separators=(",", ":"))

    @staticmethod
    def _default(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if is_dataclass(value) and not isinstance(value, type):
            return asdict(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, (set, frozenset)):
            return list(value)
        if not isinstance(value, type) and hasattr(value, "__dict__"):
            return vars(value)
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    def loads(self, value: RedisResult) -> Any:
        return json.loads(value)


class RawRedisSerializer(RedisSerializer):
    """Preserve native redis-py value encoding and response decoding."""

    def dumps(self, value: Any) -> RedisValue:
        if isinstance(value, bool) or not isinstance(value, (str, bytes, int, float)):
            raise TypeError("Raw Redis serialization requires str, bytes, int, or float")
        return value

    def loads(self, value: RedisResult) -> RedisResult:
        return value


def restore_value[T](value: Any, target_type: type[T] | None) -> T | Any:
    """Reconstruct an explicitly requested type without stored type metadata."""
    if target_type is None or value is None:
        return value
    if isinstance(value, target_type):
        return value
    if issubclass(target_type, BaseModel) or is_dataclass(target_type):
        return TypeAdapter(target_type).validate_python(value)
    if isinstance(value, dict) and target_type not in (dict, list, tuple, set, str, bytes, int, float, bool):
        return target_type(**value)
    return TypeAdapter(target_type).validate_python(value)
