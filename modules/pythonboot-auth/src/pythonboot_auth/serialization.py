"""Replaceable session codecs and explicit, application-selected type restoration."""

from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, TypeAdapter
from pythonboot_auth.exceptions import SessionSerializationError


class SessionSerializer(ABC):
    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        raise NotImplementedError


class JsonSessionSerializer(SessionSerializer):
    def serialize(self, value: Any) -> bytes:
        try:
            return json.dumps(
                value, default=self._default, ensure_ascii=False, allow_nan=False, separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as error:
            raise SessionSerializationError("Session value is not JSON serializable") from error

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
        if isinstance(value, (set, frozenset)):
            return list(value)
        if not isinstance(value, type) and hasattr(value, "__dict__"):
            return vars(value)
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    def deserialize(self, data: bytes) -> Any:
        try:
            return json.loads(data.decode("utf-8"), parse_constant=self._invalid_constant)
        except (TypeError, ValueError, UnicodeError, RecursionError) as error:
            raise SessionSerializationError("Stored session value is not valid JSON") from error

    @staticmethod
    def _invalid_constant(value: str) -> Any:
        raise ValueError("Non-finite JSON numbers are not supported")


def restore_session_value(value: Any, target_type: Any = None) -> Any:
    """Restore caller-supplied types without importing classes named by stored data."""
    if target_type is None or value is None:
        return value
    try:
        if isinstance(target_type, type) and target_type.__module__ != "builtins":
            if isinstance(value, target_type):
                return value
            if not issubclass(target_type, BaseModel) and not is_dataclass(target_type) and isinstance(value, dict):
                return target_type(**value)
        return TypeAdapter(target_type).validate_python(value)
    except Exception as error:
        raise SessionSerializationError("Session value cannot be restored to the requested target type") from error
