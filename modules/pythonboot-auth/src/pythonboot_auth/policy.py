"""Pure session state transitions shared by synchronous and asynchronous services."""

import base64
from collections.abc import Sequence
import hashlib
import hmac
import logging
import math
import re
import secrets
import time
from typing import Any, Literal
from uuid import uuid4

from pythonboot_auth.context import AuthContextHolder
from pythonboot_auth.exceptions import (
    AuthStorageError, CsrfError, NotLoginError, NotPermissionError, NotRoleError,
    SessionSerializationError,
)
from pythonboot_auth.models import LoginResult, SessionInfo
from pythonboot_auth.properties import AuthProperties
from pythonboot_auth.serialization import SessionSerializer, restore_session_value
from pythonboot_auth.storage import State

logger = logging.getLogger(__name__)
_UNSET = object()
CheckMode = Literal["and", "or"]


def permission_matches(granted: str, required: str) -> bool:
    """Only '*' is special; matching is case-sensitive and covers the whole code."""
    return re.fullmatch(".*".join(re.escape(part) for part in granted.split("*")), required) is not None


def check_grants(required: tuple[str, ...], granted: Sequence[str], mode: CheckMode, *, roles: bool) -> None:
    if mode not in ("and", "or") or not required or any(not isinstance(code, str) or not code for code in required):
        raise ValueError("Checks require non-empty codes and mode 'and' or 'or'")
    if not isinstance(granted, Sequence) or isinstance(granted, (str, bytes)) or any(not isinstance(code, str) or not code for code in granted):
        raise TypeError("StpInterface must return a sequence of non-empty strings")
    if not roles and any("*" in code for code in required):
        raise ValueError("Required permission codes must be concrete; wildcards belong to granted permissions")
    flags = [
        code in granted if roles else any(permission_matches(value, code) for value in granted)
        for code in required
    ]
    if not (all(flags) if mode == "and" else any(flags)):
        raise NotRoleError(required, mode) if roles else NotPermissionError(required, mode)


class _Policy:
    def __init__(self, serializer: SessionSerializer, properties: AuthProperties | None) -> None:
        self.serializer = serializer
        self.properties = properties if properties is not None else AuthProperties()
        if not self.properties.check_enabled:
            logger.error(
                "!!! SECURITY WARNING: pythonboot.auth.check_enabled=false !!! "
                "LOGIN, PERMISSION AND ROLE CHECKS ARE BYPASSED. "
                "Protected endpoints allow unauthenticated access. "
                "Set pythonboot.auth.check_enabled=true to restore authentication checks."
            )

    @staticmethod
    def identity(login_id: str | int, login_type: str) -> tuple[str, str]:
        if isinstance(login_id, bool) or not isinstance(login_id, (str, int)) or not str(login_id):
            raise ValueError("login_id must be a non-empty string or integer")
        if not isinstance(login_type, str) or not login_type:
            raise ValueError("login_type must be a non-empty string")
        normalized = str(login_id)
        account_id = hashlib.sha256(f"{len(login_type)}:{login_type}:{normalized}".encode()).hexdigest()
        return normalized, account_id

    @staticmethod
    def digest(token: Any = _UNSET) -> str:
        value = AuthContextHolder.token() if token is _UNSET else token
        if value is None or value == "":
            raise NotLoginError("missing_token")
        if not isinstance(value, str) or len(value) > 1024 or not value.strip():
            raise NotLoginError("malformed_token")
        return hashlib.sha256(value.encode()).hexdigest()

    def new_login(
        self, login_id: str | int, login_type: str | None, device: str,
    ) -> tuple[str, str, dict[str, Any], LoginResult]:
        if not isinstance(device, str) or not device:
            raise ValueError("device must be a non-empty string")
        kind = self.properties.login_type if login_type is None else login_type
        normalized, account_id = self.identity(login_id, kind)
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        digest = self.digest(token)
        now = time.time()
        record = {
            "session_id": uuid4().hex, "login_id": normalized, "login_type": kind,
            "device": device, "created_at": now, "last_activity": now,
            "expires_at": now + self.properties.session.timeout,
            "idle_timeout": self.properties.session.idle_timeout,
            "status": "active", "csrf_digest": hashlib.sha256(csrf.encode()).hexdigest(), "data": {},
        }
        return account_id, digest, record, LoginResult(token, csrf, self.info(record))

    @staticmethod
    def info(record: dict[str, Any]) -> SessionInfo:
        return SessionInfo(**{key: record[key] for key in SessionInfo.__dataclass_fields__})

    @staticmethod
    def active(record: dict[str, Any], now: float) -> bool:
        return record["status"] == "active" and record["expires_at"] > now and (
            record["last_activity"] + record["idle_timeout"] > now
        )

    @staticmethod
    def prepare(state: State | None) -> State:
        if state is None:
            return {"revision": "", "data": {}, "tokens": {}}
        now = time.time()
        for digest, record in tuple(state["tokens"].items()):
            if record["expires_at"] <= now:
                del state["tokens"][digest]
            elif record["status"] == "active" and record["last_activity"] + record["idle_timeout"] <= now:
                record["status"] = "expired"
                record["data"] = {}
        if not any(record["status"] == "active" for record in state["tokens"].values()):
            state["data"] = {}
        return state

    def add_login(self, state: State, digest: str, record: dict[str, Any]) -> None:
        for value in state["tokens"].values():
            if value["status"] == "active" and (
                not self.properties.session.concurrent or (
                    self.properties.session.same_device_exclusive and value["device"] == record["device"]
                )
            ):
                value["status"] = "replaced"
                value["data"] = {}
        active = sorted(
            (value for value in state["tokens"].values() if value["status"] == "active"),
            key=lambda value: (value["created_at"], value["session_id"]),
        )
        while len(active) >= self.properties.session.max_sessions:
            value = active.pop(0)
            value["status"] = "kicked_out"
            value["data"] = {}
        state["tokens"][digest] = record.copy()

    def require(self, state: State, digest: str, *, touch: bool = True) -> dict[str, Any]:
        record = state["tokens"].get(digest)
        if record is None:
            raise NotLoginError("invalid_or_expired")
        if not self.active(record, time.time()):
            reason = record["status"] if record["status"] != "active" else "expired"
            raise NotLoginError(reason)
        if touch:
            record["last_activity"] = time.time()
        return record

    @staticmethod
    def finalize(state: State) -> int:
        state["revision"] = uuid4().hex
        deadline = max((value["expires_at"] for value in state["tokens"].values()), default=time.time() + 1)
        return max(1, math.ceil(deadline - time.time()))

    def encode(self, value: Any) -> str:
        try:
            encoded = self.serializer.serialize(value)
            if not isinstance(encoded, bytes):
                raise TypeError("SessionSerializer.serialize must return bytes")
            return base64.b64encode(encoded).decode("ascii")
        except SessionSerializationError:
            raise
        except Exception as error:
            raise SessionSerializationError("Session serialization failed") from error

    def decode(self, value: str, *, target_type: Any = None) -> Any:
        try:
            decoded = self.serializer.deserialize(base64.b64decode(value, validate=True))
            return restore_session_value(decoded, target_type)
        except SessionSerializationError:
            raise
        except Exception as error:
            raise SessionSerializationError("Session deserialization failed") from error

    def session_data(
        self, state: State, digest: str, token_session: bool, operation: str,
        key: str | None = None, value: Any = None,
    ) -> Any:
        record = self.require(state, digest)
        data = record["data"] if token_session else state["data"]
        if operation == "keys":
            return tuple(data)
        if not isinstance(key, str) or not key:
            raise ValueError("Session keys must be non-empty strings")
        if operation == "set":
            data[key] = value
            return None
        if operation == "delete":
            return data.pop(key, _UNSET) is not _UNSET
        return data.get(key, _UNSET)

    def csrf(self, record: dict[str, Any], csrf_token: str | None) -> None:
        if not isinstance(csrf_token, str) or not hmac.compare_digest(
            record["csrf_digest"], hashlib.sha256(csrf_token.encode()).hexdigest(),
        ):
            raise CsrfError("A valid CSRF token is required for cookie authentication")

    @staticmethod
    def contention() -> AuthStorageError:
        logger.error("Authentication state update exceeded the configured retry limit.")
        return AuthStorageError("Concurrent authentication update retry limit exceeded")
